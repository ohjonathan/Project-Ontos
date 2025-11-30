# Contributing to Project Ontos

Thank you for your interest in contributing to Project Ontos! This document provides guidelines for contributing.

## Ways to Contribute

- **Report bugs** - Open an issue describing the problem
- **Suggest features** - Open an issue with your idea
- **Submit fixes** - Fork, fix, and submit a pull request
- **Improve documentation** - Help make the docs clearer
- **Share feedback** - Tell us how you're using Ontos

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ohjona/Project-Ontos.git
   cd Project-Ontos
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov  # For running tests
   ```

3. **Install pre-commit hooks** (optional but recommended)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Making Changes

### Before You Start

1. Check existing [issues](https://github.com/ohjona/Project-Ontos/issues) to avoid duplicate work
2. For large changes, open an issue first to discuss the approach

### Code Guidelines

- **Python style**: Follow PEP 8, use 4-space indentation
- **Type hints**: Add type hints to new functions
- **Docstrings**: Document public functions with docstrings
- **Tests**: Add tests for new functionality

### Commit Messages

Write clear, concise commit messages:

```
Add --json output flag to generate_context_map.py

- Adds JSON output option for CI/CD integration
- Includes schema documentation in README
```

### Pull Request Process

1. **Fork** the repository
2. **Create a branch** for your feature: `git checkout -b feature/my-feature`
3. **Make your changes** and commit them
4. **Run tests**: `pytest tests/ -v`
5. **Run validation**: `python3 scripts/generate_context_map.py --strict`
6. **Push** to your fork and open a PR

### PR Checklist

- [ ] Tests pass locally
- [ ] Code follows project style
- [ ] Documentation updated (if applicable)
- [ ] POCHANGELOG.md updated under `[Unreleased]`

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=scripts

# Run specific test file
pytest tests/test_yaml_edge_cases.py -v
```

## Questions?

- Open an issue for questions
- Check existing documentation in `docs/`

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
