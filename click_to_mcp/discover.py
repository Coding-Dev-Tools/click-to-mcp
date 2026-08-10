"""Auto-discover installed Click/typer CLIs via Python entry points.

Scans the installed packages for console_scripts entry points that
point to Click or typer CLI objects, and provides a way to serve
them as MCP servers.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from importlib.metadata import distribution, entry_points
from typing import Any


@dataclass
class DiscoveredCLI:
    """Information about a discovered Click/typer CLI."""

    name: str
    module_path: str
    attr_name: str
    package_name: str
    package_version: str
    summary: str = ""
    is_typer: bool = False


def _probe_cli_type(obj: Any) -> str:
    """Determine if an object is Click CLI, Typer CLI, or other."""
    import click

    if isinstance(obj, click.Group):
        return "click"
    if isinstance(obj, click.Command):
        return "click"

    # Typer uses registered_commands / registered_groups
    if hasattr(obj, "registered_commands") or hasattr(obj, "registered_groups"):
        return "typer"

    return "unknown"


def _get_package_metadata(pkg_name: str) -> str:
    """Get a short summary for a package using importlib.metadata."""
    try:
        dist = distribution(pkg_name)
        return dist.metadata.get("Summary", "") or ""
    except Exception:
        return ""


def scan_entry_points() -> list[DiscoveredCLI]:
    """Scan all installed console_scripts entry points for Click/typer CLIs.

    Returns:
        List of discovered CLIs that appear to use Click or typer.
    """
    discovered: list[DiscoveredCLI] = []

    eps_all = entry_points()
    if hasattr(eps_all, "select"):
        eps = list(eps_all.select(group="console_scripts"))
    else:
        eps = eps_all.get("console_scripts", [])  # type: ignore[attr-defined]

    for entry_point in eps:
        try:
            obj = entry_point.load()
            cli_type = _probe_cli_type(obj)

            if cli_type == "unknown":
                continue

            pkg_name = entry_point.dist.name if entry_point.dist else "unknown"
            pkg_version = entry_point.dist.version if entry_point.dist else "?"
            summary = _get_package_metadata(pkg_name)

            discovered.append(
                DiscoveredCLI(
                    name=entry_point.name,
                    module_path=entry_point.module,
                    attr_name=entry_point.attr if entry_point.attr else "",
                    package_name=pkg_name,
                    package_version=pkg_version,
                    summary=summary,
                    is_typer=(cli_type == "typer"),
                )
            )
        except (Exception, SystemExit):
            continue

    return discovered


def load_cli(cli_name: str) -> Any | None:
    """Load a CLI object by its console_scripts entry point name.

    Args:
        cli_name: The name of the CLI (e.g. 'api-contract-guardian').

    Returns:
        The loaded Click Group/Command/Typer app, or None if not found.
    """
    eps_all = entry_points()
    if hasattr(eps_all, "select"):
        eps = list(eps_all.select(group="console_scripts"))
    else:
        eps = eps_all.get("console_scripts", [])  # type: ignore[attr-defined]

    for entry_point in eps:
        if entry_point.name == cli_name:
            try:
                return entry_point.load()
            except Exception:
                return None

    # Fallback: built-in demo CLI bundled with this package.
    # When running from a source checkout without `pip install -e .`,
    # the entry point may not be registered, but we can still import directly.
    if cli_name == "click-to-mcp-demo":
        try:
            from .demo import cli as demo_cli
            return demo_cli
        except Exception:
            return None

    return None


def import_cli(module_path: str, attr_name: str) -> Any | None:
    """Import a CLI object from a module path and attribute name.

    Args:
        module_path: Dotted module path (e.g. 'api_contract_guardian.cli').
        attr_name: Attribute name within the module (e.g. 'app').

    Returns:
        The imported object, or None if not found.
    """
    try:
        module = importlib.import_module(module_path)
        if attr_name:
            return getattr(module, attr_name, None)
        # No attr name — try common conventions
        for candidate in ("app", "cli", "main", "typer_app", "click_app"):
            obj = getattr(module, candidate, None)
            if obj is not None:
                return obj
        return module
    except Exception:
        return None


def find_our_clis() -> dict[str, Any]:
    """Specifically find Revenue Holdings CLI tools.

    Returns:
        Dict of {cli_name: click_or_typer_app} for our projects.
    """
    result: dict[str, Any] = {}
    eps_all = entry_points()
    if hasattr(eps_all, "select"):
        eps = list(eps_all.select(group="console_scripts"))
    else:
        eps = eps_all.get("console_scripts", [])  # type: ignore[attr-defined]

    our_modules = [
        "api_contract_guardian",
        "json2sql",
        "deploydiff",
        "configdrift",
    ]

    for ep in eps:
        if any(mod in (ep.module or "") for mod in our_modules):
            try:
                obj = ep.load()
                if _probe_cli_type(obj) != "unknown":
                    result[ep.name] = obj
            except Exception:
                continue

    return result
