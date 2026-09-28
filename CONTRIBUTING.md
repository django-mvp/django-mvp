# Contributing to Django MVP

Thank you for your interest in contributing to Django MVP! This guide will help you get started.

## Core Principles

This project follows the rules in [CONSTITUTION.md](CONSTITUTION.md). Please read it before contributing,
together with the two standards it makes binding:

- [Testing standards](docs/contributing/standards/testing.md): what gets a test and what does not,
  the test-first cycle, test structure and fixtures, and the coverage floors.
- [Code documentation standards](docs/contributing/standards/code-documentation.md): docstrings,
  component annotations and comments.

## Development Setup

1. Clone the repository
2. Install dependencies with [uv](https://docs.astral.sh/uv/):

   ```bash
   uv sync
   ```

3. Run tests to verify setup:

   ```bash
   uv run pytest
   ```

## Testing Requirements

### Cotton Component Testing

All Cotton components MUST be tested using the following pattern:

```python
import pytest
from django_cotton import cotton_render


@pytest.fixture
def mock_request(rf):
    """Use pytest-django's rf fixture for request factory."""
    return rf.get("/")


def test_my_component(mock_request):
    """Test component rendering."""
    # Use slash notation for component paths
    html = cotton_render(mock_request, "app/my-component", {
        "my_var": "value",
    })

    assert "expected-content" in html
```

**Important:**

- Use `django_cotton.cotton_render()` - NOT `Template()` or `render_to_string()`
- Use pytest-django's `rf` fixture - NOT `RequestFactory()` directly
- Use **slash notation** for component paths: `"app/wrapper"` not `"app.wrapper"`
- Test with c-vars, slots, and edge cases (missing optional vars, etc.)

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=mvp

# Run specific test file
uv run pytest tests/test_components/test_app_header.py

# Run with verbose output
uv run pytest -xvs
```

## Code Quality

Before submitting a pull request:

1. **Run tests:**

   ```bash
   uv run pytest
   ```

2. **Run linting:**

   ```bash
   uv run ruff check .
   ```

3. **Format code:**

   ```bash
   uv run ruff format .
   ```

4. **Format templates:**

   ```bash
   uv run djlint mvp/templates --reformat
   ```

## Pull Request Process

1. Create a feature branch from `main`
2. Write a failing test for the behaviour, then the code that makes it pass
3. Update documentation
4. Run all quality checks
5. Submit PR with:
   - Clear description of changes
   - Link to any related issues
   - Confirmation that tests pass
   - Note any breaking changes

## Component Development

Before building a new component, check that it belongs in this package at all. The test is
repeat use: would a second, unrelated project want this? Components that pass, and that the
maintainers agree on, live here. Specialized or advanced ones belong in a package of their
own — Cotton resolves components from any installed app, so a separate component pack needs no
registration and drops straight in alongside these.

When creating or modifying Cotton components:

1. **Use snake_case/kebab-case for filenames:** `small-box.html`, `info_box.html`
2. **Annotate the component** with its `@description`, `@prop` and `@slot` lines, as the
   code documentation standards describe
3. **Provide default values** for optional c-vars
4. **Use semantic HTML** with appropriate ARIA attributes
5. **Test the markup the component publishes:** its element, classes, attributes and slots

## Questions?

- Check the [constitution](CONSTITUTION.md) for project rules
- Read the *Scope & philosophy* section of the [README](README.md) for what belongs here
- See [GOALS.md](GOALS.md) for the directions the package is working toward
- Review existing components and tests for examples
- Open an issue for discussion

Thank you for contributing!
