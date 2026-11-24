"""Validate paired checkpoints produced by an app's own browser tests."""

from __future__ import annotations

import json
import re
import zlib

from .habit import (
    _booleans,
    _dict,
    _items,
    _text,
    _unique_pairs,
    bounded,
    digest,
    local_path,
)

STATES = {
    "loading": "Show progress and keep the user's work available.",
    "empty": "Explain the empty state and offer the first useful action.",
    "error": "Explain the failure, preserve input, and offer a recovery action.",
    "retry": "Keep retry reachable and verify it completes the original task once.",
    "expired": "Explain the expired session, reauthenticate, and restore safe progress.",
    "success": "Confirm what was saved and offer a clear next step or exit.",
}
_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
_PNG = b"\x89PNG\r\n\x1a\n"
_IMAGE_BUDGET = 16 * 1024 * 1024
_PIXEL_BUDGET = 128 * 1024 * 1024


def _key(value):
    if not isinstance(value, str) or not _KEY.fullmatch(value):
        raise ValueError("Use a stable checkpoint, profile, or check ID")
    return value


def _capture(root, path, stage_image):
    source = local_path(root, path)
    if not source.is_file():
        raise ValueError("Journey capture must be a regular file")
    raw = bounded(source)
    data = _dict(
        json.loads(raw, object_pairs_hook=_unique_pairs),
        ("schema", "app_name", "profile", "metrics", "controls", "checkpoints"),
        "journey capture",
    )
    if data["schema"] != "prestige.journey-capture.v1":
        raise ValueError("Unsupported journey capture")
    _text(data["app_name"], "app name")
    _key(data["profile"])
    steps = []
    ids = set()
    for step in _items(data["checkpoints"], "journey checkpoints"):
        step = _dict(step, ("id", "state", "checks", "screenshot"), "checkpoint")
        key = _key(step["id"])
        if (
            key in ids
            or not isinstance(step["state"], str)
            or step["state"] not in STATES
        ):
            raise ValueError("Use unique checkpoint IDs and known journey states")
        ids.add(key)
        checks = step["checks"]
        if not isinstance(checks, dict) or not 1 <= len(checks) <= 20:
            raise ValueError("Each checkpoint requires 1 to 20 named test assertions")
        _booleans(checks, [_key(name) for name in checks], "checkpoint checks")
        image = None
        if step["screenshot"] is not None:
            image = stage_image(step["screenshot"])
        steps.append({**step, "screenshot": image})
    if not any(step["state"] == "success" for step in steps):
        raise ValueError("Each journey requires a success checkpoint")
    return (
        data,
        steps,
        {"path": source.relative_to(root).as_posix(), "sha256": digest(raw)},
    )


def _png_size(raw, budget):
    def invalid():
        return ValueError("Checkpoint PNG is invalid or has changed")

    if not raw.startswith(_PNG + b"\x00\x00\x00\x0dIHDR"):
        raise invalid()
    width, height = (
        int.from_bytes(raw[start : start + 4], "big") for start in (16, 20)
    )
    if not (
        1 <= width <= 8192 and 1 <= height <= 8192 and width * height <= 16_000_000
    ):
        raise invalid()
    if raw[24:29] not in (b"\x08\x02\x00\x00\x00", b"\x08\x06\x00\x00\x00"):
        raise invalid()
    stride = width * (3 if raw[25] == 2 else 4) + 1
    size = stride * height
    if size > budget:
        raise ValueError("Journey screenshot decoded byte budget exceeded")
    offset, compressed = 8, []
    while offset + 12 <= len(raw):
        length = int.from_bytes(raw[offset : offset + 4], "big")
        start, end = offset + 8, offset + 8 + length
        if end + 4 > len(raw) or zlib.crc32(raw[offset + 4 : end]) != int.from_bytes(
            raw[end : end + 4], "big"
        ):
            raise invalid()
        kind = raw[offset + 4 : start]
        offset = end + 4
        if kind == b"IDAT":
            compressed.append(raw[start:end])
        if kind == b"IEND" and not length and offset == len(raw):
            try:
                decoder = zlib.decompressobj()
                pixels = decoder.decompress(b"".join(compressed), size + 1)
            except zlib.error as error:
                raise invalid() from error
            if (
                len(pixels) == size
                and decoder.eof
                and not decoder.unused_data
                and all(mode <= 4 for mode in pixels[::stride])
            ):
                return size
            break
    raise invalid()


def load_pair(root, baseline, candidate, assets=None):
    baseline_path, candidate_path = (
        local_path(root, name) for name in (baseline, candidate)
    )
    if baseline_path == candidate_path or (
        baseline_path.is_file()
        and candidate_path.is_file()
        and baseline_path.samefile(candidate_path)
    ):
        raise ValueError("Select distinct baseline and candidate captures")
    total = 0
    decoded = 0

    def stage_image(item):
        nonlocal total, decoded
        row = _dict(item, ("path", "sha256"), "checkpoint screenshot")
        path = local_path(root, _text(row["path"], "screenshot path"))
        if not path.is_file() or path.suffix.lower() != ".png":
            raise ValueError("Checkpoint screenshot must be a regular PNG file")
        raw = bounded(path, min(2 * 1024 * 1024, _IMAGE_BUDGET - total))
        sha = digest(raw)
        if sha != row["sha256"]:
            raise ValueError("Checkpoint PNG is invalid or has changed")
        decoded += _png_size(raw, _PIXEL_BUDGET - decoded)
        total += len(raw)
        if assets is not None:
            assets[sha] = raw
        return {"sha256": sha}

    before, first, base_hash = _capture(root, baseline, stage_image)
    after, second, candidate_hash = _capture(root, candidate, stage_image)
    if any(before[key] != after[key] for key in ("app_name", "profile")):
        raise ValueError("Journey captures require the same app and execution profile")

    def shape(steps):
        return [
            (step["id"], step["state"], frozenset(step["checks"])) for step in steps
        ]

    if shape(first) != shape(second):
        raise ValueError(
            "Journey captures require matching checkpoints and checks in order"
        )
    return (
        before,
        after,
        {
            "profile": after["profile"],
            "captures": {"baseline": base_hash, "candidate": candidate_hash},
            "checkpoints": [
                {
                    "id": left["id"],
                    "state": left["state"],
                    "baseline": {
                        "checks": left["checks"],
                        "screenshot": left["screenshot"],
                    },
                    "candidate": {
                        "checks": right["checks"],
                        "screenshot": right["screenshot"],
                    },
                    "failed": sorted(
                        key for key, passed in right["checks"].items() if not passed
                    ),
                }
                for left, right in zip(first, second, strict=True)
            ],
            "scope": "Counts, landing, completion and user controls are supplied by the test. DOM observations and named assertions cover the submitted checkpoints.",
        },
    )
