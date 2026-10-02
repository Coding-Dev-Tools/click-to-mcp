# CLI Discovery Guide

## How `click-to-mcp discover` Works

The `discover` command scans your Python environment for installed packages that expose Click or typer CLI entry points.

### Scan Process

1. **Entry point scan**: Iterates over `importlib.metadata.entry_points()` looking for `console_scripts` and `cli` group entries
2. **Module import**: For each entry point, attempts to import the target object
3. **Type check**: Verifies the imported object is a `click.Group` or `click.Command` instance
4. **Metadata extraction**: Reads package name, version, and module path

### Output Format

```
Found N Click/typer CLI(s):

 1. [Click] my-cli
    Package: my-package 1.2.3
    Module: my_package.cli:main

 2. [Typer] another-app
    Package: another-package 0.5.0
    Module: another_app:app.cli
```

### Usage with serve

Copy the module path from discover output directly into the serve command:

```bash
click-to-mcp serve my_package.cli:main
```

### Programmatic Discovery

You can also use the Python API:

```python
from click_to_mcp.discovery import discover_clis

for cli_info in discover_clis():
    print(f"{cli_info.name}: {cli_info.module_path}")
```
