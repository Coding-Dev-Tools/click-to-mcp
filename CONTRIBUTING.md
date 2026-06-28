# Contributing

Thanks for your interest in contributing!

## Development Setup

1. Fork and clone the repo
2. Create a virtual environment: python -m venv .venv && source .venv/bin/activate
3. Install dev dependencies: pip install -e ".[dev]"
4. Run tests: pytest tests/ -v
5. Lint: 
ruff check src/

## Pull Requests

- Fork the repo and create a feature branch
- Add tests for any new functionality
- Ensure all existing tests pass
- Run 
ruff check src/ --fix before committing
- Keep PRs focused on a single change

## Reporting Issues

- Use GitHub Issues
- Include Python version, OS, and steps to reproduce
- Include relevant error output

## Code Style

- Python 3.10+
- Type hints where practical
- Follow ruff defaults (Black-compatible formatting)

## License

By contributing, you agree your work will be licensed under the same license as this project.