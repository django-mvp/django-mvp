# Research: Brand Logo & Icon Templatetags

**Phase**: 0 — Pre-design research
**Branch**: `019-brand-logo-templatetags`
**Date**: 2026-05-28

---

## 1. Existing Implementation Audit

**Finding**: The feature is partially implemented in the current codebase.

| Component | File | Status |
|-----------|------|--------|
| Settings constants | `mvp/config.py` | Exists — naming differs from spec |
| Default resolver functions | `mvp/utils.py` | Exists — incomplete (logo has no dark variant) |
| `logo_url` templatetag | `mvp/templatetags/mvp.py` | Exists — signature differs from spec |
| `icon_url` templatetag | `mvp/templatetags/mvp.py` | Exists — signature differs from spec |
| Bundled static assets | `mvp/static/brand/` | Exists — `logo.svg`, `icon_light.svg`, `icon_dark.svg` |
| Tests | `tests/` | Missing — no test file for these templatetags |
| Documentation | `skills/django-mvp/SKILL.md` | Stale — settings and tag signatures undocumented |

### Existing vs Spec Gaps

| Gap | Existing Behaviour | Spec Requirement |
|-----|--------------------|-----------------|
| Settings names | `MVP_LOGO_URL_FUNC`, `MVP_ICON_URL_FUNC` | `MVP_LOGO_RESOLVER`, `MVP_ICON_RESOLVER` |
| Tag signature | `takes_context=True`; request extracted from context internally | Explicit `request` as first positional argument |
| Logo dark fallback | `logo_url` returns `brand/logo.svg` always (no dark variant) | Falls back to light logo for any unrecognised/absent dark asset |
| Error handling | None — `import_string` raises `ImportError` raw; resolver exceptions propagate | `ImproperlyConfigured` on bad import path; empty string on resolver exception |
| Audience labels | Not applicable (spec gap) | Spec XI violation — no labeled end-user story |

---

## 2. Decision: Settings Key Names

**Decision**: Rename `MVP_LOGO_URL_FUNC` → `MVP_LOGO_RESOLVER` and `MVP_ICON_URL_FUNC` → `MVP_ICON_RESOLVER`.

**Rationale**: The spec defines these names as the canonical API. The project is currently in alpha (v0.6.1); renaming now before stabilisation is lower cost than maintaining a compatibility shim long-term. The suffix `_RESOLVER` is more descriptive (it points to a callable that resolves a URL, not just any function).

**Alternatives Considered**:
- Keep `_FUNC` suffix: Rejected — inconsistent with the spec and less descriptive.
- Deprecation shim (support both names): Rejected for this iteration — adds complexity for a pre-1.0 alpha library with no known downstream consumers outside the demo app.

**Migration Impact**: Demo app and any test settings referencing `MVP_LOGO_URL_FUNC` / `MVP_ICON_URL_FUNC` must be updated. Scope is small (only `mvp/config.py` and anywhere they are explicitly set in settings files).

---

## 3. Decision: Templatetag Signature

**Decision**: Keep `takes_context=True`; the tag extracts `request` from the template context automatically. Template authors do not pass `request` explicitly.

**Rationale**: The `request` object is always required by the resolver contract, so there is no benefit to making it an explicit template argument — it would add boilerplate to every tag call (`{% logo_url request %}`, `{% logo_url request theme="dark" %}`) without adding clarity. Django's `RequestContext` (the standard template context for views) always provides `request`; developers are already assumed to be using it (Assumptions). Extracting it automatically is therefore the ergonomic choice.

**New Python signature**:
```python
@register.simple_tag(takes_context=True)
def logo_url(context, height, theme="light"):
    request = context.get("request")
    ...

@register.simple_tag(takes_context=True)
def icon_url(context, height, theme="light"):
    request = context.get("request")
    ...
```

**New template usage**:
```html
{% load mvp %}
<img src="{% logo_url height=40 %}">
<img src="{% logo_url height=40 theme="dark" %}"><!-- height is required -->
```

**Alternatives Considered**:
- Explicit `request` as first positional template argument (`{% logo_url request %}`): Rejected by user — request is always required, so declaring it every time is needless boilerplate.
- Hybrid (optional explicit override): Rejected — YAGNI; adds complexity for a rare edge case.

---

## 4. Decision: Default Logo Resolver — Dark Theme Handling

**Decision**: The default `logo_url` resolver falls back to `brand/logo.svg` for all themes (including dark). No `logo_dark.svg` will be added to the bundled assets.

**Rationale**: The bundled `logo.svg` is the django-mvp package logo, not a consumer's brand logo. Providing a separate dark variant of a placeholder logo adds asset maintenance burden with no user value. The spec's fallback rule (FR-009: fall back to light when only one asset is available) is satisfied — `logo.svg` is treated as the light variant, and all other themes fall back to it.

The `icon_url` resolver already has proper light/dark handling via `icon_light.svg` and `icon_dark.svg`. No change needed for icons.

**Alternatives Considered**:
- Add `logo_dark.svg` to bundled assets: Rejected — unnecessary for a placeholder/demo logo; real consumers will supply their own resolver or assets.
- Make the default resolver accept settings for asset paths: Rejected — spec explicitly removed light/dark path settings; resolver replacement is the extension point.

---

## 5. Decision: Error Handling

**Decision**: Two-tier error handling:
1. **Bad import path** (setting present but module/function not importable): Raise `django.core.exceptions.ImproperlyConfigured` with a clear message identifying the setting name and the bad path. This check happens on first tag call (lazy), not at Django startup.
2. **Resolver raises at runtime**: Catch all exceptions, return `""` (empty string). No logging.

**Rationale**: FR-013 requires `ImproperlyConfigured` for bad paths. FR-012 requires silent empty-string return for runtime resolver failures. FR (logging) was explicitly removed during clarification — the default resolver never fails; custom resolvers own their observability.

**Implementation Pattern**:
```python
try:
    func = import_string(resolver_path)
except ImportError as e:
    raise ImproperlyConfigured(
        f"MVP_LOGO_RESOLVER '{resolver_path}' could not be imported: {e}"
    ) from e
try:
    return func(request, height, theme) or ""
except Exception:
    return ""
```

**Alternatives Considered**:
- Validate at app startup (`AppConfig.ready()`): Rejected — import_string call at startup would couple app loading to the presence of the resolver module; lazy resolution is simpler and sufficient.
- Log on resolver exception: Rejected during spec clarification.

---

## 6. Decision: Caching of Imported Resolver

**Decision**: Do not cache the imported resolver function at the tag level. Call `import_string()` on every tag invocation.

**Rationale**: The spec says "no implicit caching at the tag level." Python's import system already caches module objects, so `import_string` is cheap. Caching the resolved callable at module level would break test isolation (tests swap resolver settings). Caching at tag level would prevent dynamic resolver changes (rare but valid in testing scenarios).

**Alternatives Considered**:
- Cache using `functools.lru_cache` on a helper: Rejected — complicates test isolation.
- Module-level lazy cache (`_logo_resolver = None`): Rejected — same issue; tests cannot swap resolvers cleanly.

---

## 7. Decision: Spec Amendment — Constitution XI Violation

**Decision**: Amend spec.md to add audience labels and one explicit end-user story before proceeding to implementation.

**Rationale**: Constitution Principle XI requires at least one labeled developer story AND one labeled end-user story. All 4 current stories are developer-facing and unlabeled. Story 3 (per-tenant logo) has an implicit end-user dimension but is not labeled as such.

**Proposed amendment**:
- Add `**Audience**: Developer` label to all 4 existing stories.
- Promote the implicit end-user concern in Story 3 to an explicit end-user scenario, or add a new Story 5 labeled `**Audience**: End User`.

This amendment does not change the implementation scope.

---

## Summary of Decisions

| # | Decision | Chosen |
|---|----------|--------|
| 1 | Settings naming | Rename to `MVP_LOGO_RESOLVER` / `MVP_ICON_RESOLVER` |
| 2 | Tag signature | Explicit `request` positional argument; no `takes_context` |
| 3 | Logo dark fallback | Single `logo.svg` for all themes; no new bundled dark asset |
| 4 | Error handling | `ImproperlyConfigured` for bad path; `""` on runtime exception |
| 5 | Caching | No caching; rely on Python import cache |
| 6 | Spec amendment | Add audience labels + one end-user story before implementation |
