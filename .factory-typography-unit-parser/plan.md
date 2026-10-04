# Typography unit parser repair

Requirement: deterministic critique must parse the complete `line-height` CSS value so numeric backtracking cannot reinterpret dimensional values such as `18px` or `13px` as unitless `1`. Preserve the existing unitless threshold: `1.2` is reported; `1.5` and `1.6` are accepted. Pixel, em, rem and percentage values are outside the unitless test.

Scope: `prestige_design/critique.py` and `tests/test_critique.py`. No findings schema, security handling, small-text rule, dependency, network, provider, deployment or publication changes.

Validation: run `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -p pytest_asyncio.plugin -q tests/test_critique.py` under Python 3.11.9 on Windows. Initial unfiltered pytest could not load the unrelated global AnchorPy/construct plugin (`ImportError: cannot import name Int8ul`); the bounded plugin-disabled run passed.
