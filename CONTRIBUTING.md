# Contributing to Django MVP

Thank you for your interest in contributing to Django MVP! This guide will help you get started.

## Core Principles

This project follows the principles defined in [.specify/memory/constitution.md](.specify/memory/constitution.md). Please read it before contributing.

**Key requirements:**

- **Design-First**: Implementation and design verification MUST occur before writing tests
- **Documentation-First**: Public behavior changes MUST include documentation updates
- **Component Quality**: All components MUST be accessible and use semantic HTML

## Development Setup

1. Clone the repository
2. Install dependencies with Poetry:

   ```bash
   poetry install
   ```

3. Run tests to verify setup:

   ```bash
   poetry run pytest
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
poetry run pytest

# Run with coverage
poetry run pytest --cov=mvp

# Run specific test file
poetry run pytest tests/test_app_components.py

# Run with verbose output
poetry run pytest -xvs
```

## Code Quality

Before submitting a pull request:

1. **Run tests:**

   ```bash
   poetry run pytest
   ```

2. **Run linting:**

   ```bash
   poetry run ruff check .
   ```

3. **Format code:**

   ```bash
   poetry run ruff format .
   ```

4. **Format templates:**

   ```bash
   poetry run djlint mvp/templates --reformat
   ```

## Pull Request Process

1. Create a feature branch from `main`
2. Implement the feature/design
3. Verify the design meets expectations (use the playwright-cli skill in a real
   browser for UI changes)
4. Write comprehensive tests for the verified implementation
5. Update documentation
6. Run all quality checks
7. Submit PR with:
   - Clear description of changes
   - Link to any related issues
   - Confirmation that tests pass
   - Note any breaking changes

For UI-impacting changes, the PR MUST include behavior-level verification evidence
from playwright-cli skill steps aligned to acceptance criteria. Page-load-only checks
are insufficient. Screenshot-file analysis is fallback-only for multi-viewport
differences, configuration-driven visual diffs, subtle layout/CSS regressions, or
explicit reviewer request.

## Component Development

When creating or modifying Cotton components:

1. **Use snake_case/kebab-case for filenames:** `small-box.html`, `info_box.html`
2. **Document all c-vars** with comments in the component
3. **Provide default values** for optional c-vars
4. **Use semantic HTML** with appropriate ARIA attributes
5. **Test all component states:** default, with custom c-vars, with slots

## Questions?

- Check the [constitution](.specify/memory/constitution.md) for project rules
- Review existing components and tests for examples
- Open an issue for discussion

Thank you for contributing!
