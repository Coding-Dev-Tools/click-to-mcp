"""Auto-discover installed Click/typer CLIs via Python entry points.

Scans the installed packages for console_scripts entry points that
point to Click or typer CLI objects, and provides a way to serve
them as MCP servers.
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from importlib.metadata import distribution, entry_points
from typing import Any

logger = logging.getLogger(__name__)


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
        logger.debug("Failed to get metadata for %s", pkg_name)
        return ""


def scan_entry_points() -> list[DiscoveredCLI]:
    """Scan all installed console_scripts entry points for Click/typer CLIs.

    Returns:
        List of discovered CLIs that appear to use Click or typer.
    """
    discovered: list[DiscoveredCLI] = []

    try:
        eps = entry_points(group="console_scripts")
    except TypeError:
        # Older Python: entry_points() returns dict
        eps = entry_points().get("console_scripts", [])

    for entry_point in eps:
        try:
            obj = entry_point.load()
            cli_type = _probe_cli_type(obj)

            if cli_type == "unknown":
                continue

            pkg_name = entry_point.dist.name if entry_point.dist else "unknown"
            pkg_version = entry_point.dist.version if entry_point.dist else "?"
            summary = _get_package_metadata(pkg_name)

            discovered.append(DiscoveredCLI(
                name=entry_point.name,
                module_path=entry_point.module,
                attr_name=entry_point.attr if entry_point.attr else "",
                package_name=pkg_name,
                package_version=pkg_version,
                summary=summary,
                is_typer=(cli_type == "typer"),
            ))
        except Exception:
            logger.debug("Failed to load entry point %s", entry_point.name)
            continue

    return discovered


def load_cli(cli_name: str) -> Any | None:
    """Load a CLI object by its console_scripts entry point name.

    Args:
        cli_name: The name of the CLI (e.g. 'api-contract-guardian').

    Returns:
        The loaded Click Group/Command/Typer app, or None if not found.
    """
    try:
        eps = entry_points(group="console_scripts")
    except TypeError:
        eps = entry_points().get("console_scripts", [])

    for entry_point in eps:
        if entry_point.name == cli_name:
            try:
                return entry_point.load()
            except Exception:
                logger.debug("Failed to load CLI %s", cli_name)
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
        logger.debug("Failed to import %s.%s", module_path, attr_name)
        return None


def find_our_clis() -> dict[str, Any]:
    """Specifically find Revenue Holdings CLI tools.

    Returns:
        Dict of {cli_name: click_or_typer_app} for our projects.
    """
    result: dict[str, Any] = {}
    try:
        eps = entry_points(group="console_scripts")
    except TypeError:
        eps = entry_points().get("console_scripts", [])

    our_modules = [
        "api_contract_guardian", "json2sql", "deploydiff", "configdrift",
    ]

    for ep in eps:
        if any(mod in (ep.module or "") for mod in our_modules):
            try:
                obj = ep.load()
                if _probe_cli_type(obj) != "unknown":
                    result[ep.name] = obj
            except Exception:
                logger.debug("Failed to load entry point %s for our CLIs", ep.name)
                continue

    return result
