"""Source-bound JSX and TSX habit repairs using Tree-sitter byte ranges."""

from __future__ import annotations

from difflib import unified_diff
from html import escape, unescape
import os
from pathlib import Path
import re
import tempfile

from .habit import bounded, digest, local_path, seal

_MAX_SOURCE = 512 * 1024
_MAX_NODES = 50_000
_JSX = {"jsx_element", "jsx_self_closing_element"}
_FUNCTION = {"function_declaration", "function_expression", "arrow_function"}
_SCOPES = {
    "statement_block",
    "switch_body",
    "with_statement",
    "for_statement",
    "for_in_statement",
}
_MARKERS = ("primary", "action-dock", "completion", "done", "next")


def _parser(suffix):
    try:
        from tree_sitter import Language, Parser

        if suffix == ".tsx":
            from tree_sitter_typescript import language_tsx as grammar
        else:
            from tree_sitter_javascript import language as grammar
    except ImportError as exc:
        raise ValueError(
            "Install the Prestige habit extra to enable JSX and TSX repair"
        ) from exc
    return Parser(Language(grammar()))


def _walk(root):
    todo = [root]
    visited = 0
    while todo:
        node = todo.pop()
        visited += 1
        if visited > _MAX_NODES:
            raise ValueError("JSX AST exceeds the node budget")
        yield node
        todo.extend(reversed(node.named_children))


def _value(node):
    return node.text.decode("utf-8")


def _opening(node):
    return node.child_by_field_name("open_tag") if node.type == "jsx_element" else node


def _tag(node):
    if node is None or node.type not in _JSX:
        return ""
    name = _opening(node).child_by_field_name("name")
    return _value(name) if name is not None else ""


def _attrs(node):
    found = {}
    for child in _opening(node).named_children:
        if child.type == "jsx_expression":
            raise ValueError("An editable tag has dynamic spread attributes")
        if child.type != "jsx_attribute":
            continue
        name, *parts = child.named_children
        key = _value(name)
        if key in found:
            raise ValueError("An editable tag has duplicate attributes")
        val = parts[0] if parts else None
        found[key] = (
            True
            if val is None
            else unescape(_value(val)[1:-1])
            if val.type == "string"
            else None
        )
    return found


def _markers(tree):
    groups = {}
    names = {"data-prestige-" + name: name for name in _MARKERS}
    for attr in (n for n in _walk(tree.root_node) if n.type == "jsx_attribute"):
        key = names.get(_value(attr.named_children[0]))
        if key is None:
            continue
        owner = attr.parent
        node = owner.parent if owner.type == "jsx_opening_element" else owner
        value = _attrs(node)["data-prestige-" + key]
        if value not in (True, "true"):
            raise ValueError("Prestige markers must be static true attributes")
        component = next(
            (item for item in _ancestors(node) if item.type in _FUNCTION), None
        )
        if component is None:
            raise ValueError("Prestige markers must be inside a component function")
        found = groups.setdefault(component.start_byte, {})
        if key in found:
            raise ValueError(f"Ambiguous duplicate {key} marker")
        found[key] = node
    return list(groups.values())


def _ancestors(node):
    while node is not None:
        yield node
        node = node.parent


def _direct_inside(node, container):
    return node.parent == container and container.type == "jsx_element"


def _live_container(node):
    unsafe = {"hidden", "inert", "aria-hidden", "aria-disabled"}
    return all(
        not unsafe.intersection(_attrs(parent))
        for parent in _ancestors(node)
        if parent.type in _JSX
    )


def _click_expression(node):
    callable_nodes = {
        "identifier",
        "arrow_function",
        "function_expression",
        "member_expression",
    }
    for attr in _opening(node).named_children:
        if attr.type != "jsx_attribute" or _value(attr.named_children[0]) != "onClick":
            continue
        parts = attr.named_children[1:]
        if parts and parts[0].type == "jsx_expression":
            return any(
                child.type in callable_nodes for child in parts[0].named_children
            )
    return False


def _dock_edits(found):
    primary, dock = found.get("primary"), found.get("action-dock")
    if primary is None and dock is None:
        return []
    if primary is None or dock is None:
        raise ValueError("The primary action and its destination must both be marked")
    if _tag(primary) != "button" or _attrs(primary).get("type") != "button":
        raise ValueError("Only an explicitly typed non-submit button can move")
    if not _click_expression(primary):
        raise ValueError("The primary action needs its own callable click expression")
    if not _live_container(primary):
        raise ValueError("The primary action cannot be hidden or inert")
    if _tag(dock) not in {"div", "section"} or not _live_container(dock):
        raise ValueError("The action dock must be a visible native container")
    if _direct_inside(primary, dock):
        return []
    header = primary.parent
    if _tag(header) != "header" or not _direct_inside(header, dock.parent):
        raise ValueError("The dock and the primary action header must be siblings")
    if any(key.startswith("on") for parent in (header, dock) for key in _attrs(parent)):
        raise ValueError("Moving the CTA would change delegated events")
    if dock.start_byte <= header.end_byte or any(
        node.type == "jsx_element" and _tag(node) == "form"
        for node in _ancestors(primary)
    ):
        raise ValueError(
            "Moving this CTA would cross an unsafe layout or form boundary"
        )
    close = dock.child_by_field_name("close_tag")
    if (
        close is None
        or dock.text[
            _opening(dock).end_byte - dock.start_byte : close.start_byte
            - dock.start_byte
        ].strip()
    ):
        raise ValueError("The marked action dock must be empty")
    return [
        (primary.start_byte, primary.end_byte, b"", "FRICTION_BARRIER"),
        (close.start_byte, close.start_byte, primary.text, "FRICTION_BARRIER"),
    ]


def _parameter_names(owner):
    parameters = owner.child_by_field_name("parameters")
    if parameters is None:
        parameters = owner.child_by_field_name("parameter")
    if parameters is None:
        return set()
    args = (
        parameters.named_children
        if parameters.type == "formal_parameters"
        else [parameters]
    )
    names = set()
    for node in args:
        if node.type in {"required_parameter", "optional_parameter"}:
            node = node.child_by_field_name("pattern")
        if node is None:
            continue
        if node.type == "identifier":
            names.add(_value(node))
        if node.type == "object_pattern":
            names.update(_object_bindings(node))
    return names


def _object_bindings(node):
    for item in node.named_children:
        if item.type == "shorthand_property_identifier_pattern":
            yield _value(item)
        if item.type == "pair_pattern":
            target = item.child_by_field_name("value")
            if target is not None and target.type == "identifier":
                yield _value(target)


def _completion_edits(found):
    done, host = found.get("done"), found.get("completion")
    if done is None and host is None and "next" not in found:
        return []
    if done is None or host is None or not _direct_inside(done, host):
        raise ValueError(
            "The completion and its direct Done control must both be marked"
        )
    if _tag(host) not in {"section", "div", "dialog"} or _tag(done) != "button":
        raise ValueError("The completion needs native container and button elements")
    done_attrs = _attrs(done)
    if done_attrs.get("type") != "button" or not _click_expression(done):
        raise ValueError("The Done control needs an existing non-submit click handler")
    if "disabled" in done_attrs or not _live_container(done):
        raise ValueError(
            "The Done control and its completion must be visible and enabled"
        )
    existing = found.get("next")
    if existing is not None:
        if _tag(existing) != "button" or host not in _ancestors(existing.parent):
            raise ValueError("The existing next action is outside the completion")
        attributes = _attrs(existing)
        if attributes.get("type") != "button":
            raise ValueError("The existing next action must be a non-submit button")
        if (
            "disabled" in attributes
            or not _live_container(existing)
            or not _click_expression(existing)
        ):
            raise ValueError(
                "The existing next action needs a visible, enabled click control"
            )
        return []
    if any(
        {"onClick", "onClickCapture"}.intersection(_attrs(parent))
        for parent in _ancestors(host)
        if parent.type in _JSX
    ):
        raise ValueError(
            "Adding a next action would change delegated completion events"
        )
    return [_next_edit(host, done)]


def _next_edit(host, done):
    config = _attrs(host)
    handler, label = (
        config.get("data-prestige-next-" + key) for key in ("handler", "label")
    )
    if not isinstance(handler, str) or not re.fullmatch(
        r"[$A-Za-z_][$\w]*", handler, re.ASCII
    ):
        raise ValueError("The completion requires a named next-action handler")
    if not isinstance(label, str) or not label.strip() or len(label) > 100:
        raise ValueError("The completion requires an explicit next-action label")
    owner = next((n for n in _ancestors(host) if n.type in _FUNCTION), None)
    if owner is None or handler not in _parameter_names(owner):
        raise ValueError(
            "The next-action handler must be an existing component parameter"
        )
    body = owner.child_by_field_name("body")
    if any(n.type in _SCOPES and n != body for n in _within(host, owner)):
        raise ValueError("A nested scope could shadow the next-action handler")
    text = (
        f'{{typeof {handler} === "function" && '
        f'<button type="button" data-prestige-next onClick={{() => {handler}()}}>'
        f"{escape(label)}</button>}}"
    ).encode("utf-8")
    return done.end_byte, done.end_byte, text, "DEAD_END_TERMINAL"


def _within(node, owner):
    for parent in _ancestors(node):
        if parent == owner:
            return
        yield parent


def _plan(parser, raw):
    tree = parser.parse(raw)
    if tree.root_node.has_error:
        raise ValueError("JSX or TSX has syntax errors")
    return [
        edit
        for found in _markers(tree)
        for edit in _dock_edits(found) + _completion_edits(found)
    ]


def _transform(raw, edits):
    cursor = 0
    chunks = []
    for start, end, replacement, _ in sorted(edits):
        if start < cursor:
            raise ValueError("Proposed JSX edits overlap")
        chunks.extend((raw[cursor:start], replacement))
        cursor = end
    return b"".join((*chunks, raw[cursor:]))


def _apply(path, original, modified):
    lock = path.with_name(f".{path.name}.prestige-lock")
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        with tempfile.TemporaryDirectory(dir=path.parent) as temporary:
            pending = Path(temporary) / path.name
            pending.write_bytes(modified)
            pending.chmod(path.stat().st_mode)
            if bounded(path, _MAX_SOURCE) != original:
                raise ValueError("Source changed since preview")
            os.replace(pending, path)
    finally:
        os.close(fd)
        lock.unlink(missing_ok=True)


def habit_remediate(root: Path, source: str, expect_sha256: str | None = None) -> dict:
    root = root.resolve()
    path = local_path(root, source)
    if path.suffix.lower() not in (".jsx", ".tsx"):
        raise ValueError("Expected a .jsx or .tsx component")
    raw = bounded(path, _MAX_SOURCE)
    before = raw.decode("utf-8")
    before_sha = digest(raw)
    if expect_sha256 is not None and expect_sha256 != before_sha:
        raise ValueError("Source SHA-256 differs from the reviewed preview")
    parser = _parser(path.suffix.lower())
    edits = _plan(parser, raw)
    modified = _transform(raw, edits)
    if edits and _plan(parser, modified):
        raise ValueError("The proposed repair does not reach a stable AST")
    name = path.relative_to(root).as_posix()
    patch = "".join(
        unified_diff(
            before.splitlines(keepends=True),
            modified.decode("utf-8").splitlines(keepends=True),
            f"a/{name}",
            f"b/{name}",
        )
    )
    if len(patch.encode("utf-8")) > 256 * 1024:
        raise ValueError("Repair preview exceeds the output budget")
    applied = bool(edits and expect_sha256 is not None)
    if applied:
        _apply(path, raw, modified)
    return seal(
        {
            "schema": "prestige.habit-remediation.v1",
            "path": name,
            "source_sha256": before_sha,
            "candidate_sha256": digest(modified),
            "applied": applied,
            "repairs": sorted({edit[3] for edit in edits}),
            "patch": patch,
            "verification": {
                "syntax": "PASS",
                "idempotent": True,
                "behavior": "NOT_RUN",
            },
        }
    )
