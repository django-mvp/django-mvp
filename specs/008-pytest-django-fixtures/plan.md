# Phase 2: Standardize Test Suite to pytest-django Fixtures

## Problem Statement

The remaining ~365 tests use an inconsistent mix of testing strategies:
- Some create `Client()` instances inline instead of using the `client` fixture
- Some define stub view classes via `type()` inline instead of conftest helpers
- Shared model fixtures (`category`, `product`, `article`) are duplicated across test files
- No consistent use of `@pytest.mark.django_db` on DB-dependent tests

## Solution

1. **Expand `tests/conftest.py`** with shared model fixtures and view factory helpers
2. **Replace inline `Client()` creation** with the `client` fixture in `test_error_views.py`
3. **Verify consistency** across all test files — no production code changes needed
4. **Run full suite** to verify zero regressions

## Scope

- Files modified: `tests/conftest.py`, `tests/test_views/test_error_views.py`, and any file with duplicated fixtures
- No production code changes
- All 365 tests must still pass
