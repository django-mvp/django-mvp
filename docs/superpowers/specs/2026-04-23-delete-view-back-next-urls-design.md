# Delete View: Separate Back and Next URLs

**Date:** 2026-04-23  
**Status:** Approved  
**Scope:** `MVPDeleteView`, `MVPUpdateView.get_delete_url()`, `delete_view.html`

---

## Problem

The delete page currently uses a single `?next=` query parameter for two distinct purposes:

1. The "Go Back" button — should navigate to *where the user came from* (e.g. the update page).
2. The post-delete redirect — should navigate to a *safe destination after the object is gone* (e.g. the list view).

These are different URLs in the most common case (entering from the update page), but the current code conflates them into one parameter. The result: clicking "Go Back" after opening from the update page takes the user to the list, not back to the form they came from.

---

## Design

### URL Contract

The delete link carries two explicit query parameters:

```
/products/1/delete/?back=/products/1/edit/&next=/products/
```

| Parameter | Read on | Used for | Fallback when absent |
|---|---|---|---|
| `back` | GET only | "Go Back" button `href` | list URL |
| `next` | POST only (hidden input) | post-delete redirect | list URL |

`back` is read from `request.GET` once, injected into context as `back_url`, and rendered directly into the Go Back button's `href`. It never touches the form POST.

`next` is carried through the form as a hidden `<input name="next">` (unchanged from current behaviour). `MVPDeleteView.get_success_url()` reads it from POST data via the existing `NextURLMixin`.

Both parameters are validated with `url_has_allowed_host_and_scheme` before use to prevent open-redirect attacks. Both fall back to the list URL when absent or invalid.

---

### Code Changes (5 touch-points)

#### 1. `MVPDeleteView.get_back_url()` — new method

```python
def get_back_url(self) -> str:
    """Return the URL for the Go Back button.

    Reads ``?back`` from the GET query string, validates it against the
    current host, and falls back to the list URL.
    """
    from django.utils.http import url_has_allowed_host_and_scheme
    candidate = self.request.GET.get("back")
    if candidate and url_has_allowed_host_and_scheme(
        url=candidate,
        allowed_hosts={self.request.get_host()},
        require_https=self.request.is_secure(),
    ):
        return candidate
    return self.get_list_url()
```

#### 2. `MVPDeleteView.get_context_data()` — add `back_url`

```python
context["back_url"] = self.get_back_url()
# existing: context["next_url"] = ... (from NextURLMixin via super())
```

`next_url` in context comes from `NextURLMixin.get_context_data()`, which reads `?next` from the GET query string. This is the value pre-populated into the hidden `<input name="next">` and remains unchanged.

#### 3. `delete_view.html` — Go Back button

Change:

```django
<c-button text="{% trans "Go back" %}"
          href="{{ next_url }}"
          ...
```

To:

```django
<c-button text="{% trans "Go back" %}"
          href="{{ back_url }}"
          ...
```

The hidden input `name="next"` and its value `{{ next_url }}` are unchanged.

#### 4. `MVPUpdateView.get_delete_url()` — append both params

Current behaviour appends `?next=<list_url>`. New behaviour:

```python
def get_delete_url(self):
    url = reverse(delete_view_name, kwargs=self.get_lookup_kwargs())
    back_url = reverse(self._get_view_name("update"), kwargs=self.get_lookup_kwargs())
    next_url = self.get_list_url()
    params = urlencode({"back": back_url, "next": next_url})
    return f"{url}?{params}"
```

- `back` = the update view URL (stable, computed via `reverse()`)
- `next` = the list URL (safe destination after deletion)

#### 5. `NextURLMixin.get_next_url()` — no change

Already reads `next` from GET (for context injection) and from POST (for redirect). Behaviour is correct as-is.

---

### Other Callers (tables, direct links)

Any delete link that omits `?back=` silently falls back to the list URL for "Go Back" — which is the correct behaviour when entering from a table or list page. Callers that want explicit control (e.g. a detail page linking directly to delete) can append `?back=<their_url>` to the delete link.

The three existing demo delete views (`ProductDeleteView`, `ProductDeleteWithRelatedView`, `ProductDeleteWithConfirmView`) require no changes — their fallback "Go Back" destination of the list URL is appropriate.

---

### Testing

Update existing tests in `tests/test_views/test_delete_view.py`:

- `test_context_next_url_defaults_to_list` — assert `back_url` also defaults to list when `?back` is absent.
- Add `test_context_back_url_from_query_param` — GET with `?back=/products/1/edit/` → `back_url == "/products/1/edit/"`.
- Add `test_context_back_url_rejects_external_url` — GET with `?back=https://evil.com/` → `back_url == list_url`.
- Update `MVPUpdateView` tests to assert the generated delete URL contains both `back` and `next` params.

No migration required. No new models, forms, or URLs.

---

## Summary of Changes

| File | Change |
|---|---|
| `mvp/views/edit.py` | Add `get_back_url()` to `MVPDeleteView`; add `back_url` to context; update `get_delete_url()` in `MVPUpdateView` to use `urlencode({"back": ..., "next": ...})` |
| `mvp/templates/delete_view.html` | Go Back button: `href="{{ next_url }}"` → `href="{{ back_url }}"` |
| `tests/test_views/test_delete_view.py` | Add/update tests for `back_url` context key and open-redirect protection |
