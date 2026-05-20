"""Regression tests for pyproject.toml metadata integrity."""

import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def test_no_dead_license_extra():
    """The 'license' optional-dependency referenced a non-existent
    'revenueholdings-license' PyPI package.  It must stay removed."""
    with open(PYPROJECT, "rb") as f:
        data = tomllib.load(f)
    extras = data["project"]["optional-dependencies"]
    assert "license" not in extras, (
        f"license extra found with deps: {extras['license']} — "
        "revenueholdings-license does not exist on PyPI"
    )


def test_required_extras_present():
    """Ensure the real optional-dependency groups are still declared."""
    with open(PYPROJECT, "rb") as f:
        data = tomllib.load(f)
    extras = data["project"]["optional-dependencies"]
    assert "http" in extras, "http extra must be present"
    assert "dev" in extras, "dev extra must be present"
