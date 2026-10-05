# ADR 0032 — A packaged template isolates every call to a daisy-cotton component

**Status:** accepted

## Decision

Every call a template under `mvp/templates/` makes to one of
[daisy-cotton](https://github.com/django-mvp/daisy-cotton)'s components carries Cotton's `only`:

```html
<c-button text="{% trans "Save" %}" variant="primary" only />
```

The rule covers the templates the package ships. Demo pages and documented examples are written
the way a project writes them and do not carry `only`.

It does not cover calls to this package's own components. Several of those declare an attribute
with no default and can still pick a page variable up. That is a separate fault, tracked in
[#485](https://github.com/django-mvp/django-mvp/issues/485).

## Why

Cotton fills an attribute the caller did not pass from the surrounding template context when the
component declares it with no default. Many of daisy-cotton's components declare `text`, `class`,
`icon`, `items`, `variant` or `size` that way. A packaged template renders inside pages this
package has never seen, so a view that puts an ordinary name such as `text` or `items` in its
context could change a link in the shell or the breadcrumb trail, with no error.

`only` stops the component seeing anything but what the tag passes. Content between the tags is
still rendered with the page's context, so a message's text or a list of records inside an alert
is unaffected.

The alternative was to ask daisy-cotton to give every attribute an empty default. That may still
happen, but this package's pages would depend on every later component and release keeping to
it. A rule at the call site, checked by a test, does not.

A missing `only` shows only on a page that happens to use the colliding name, which is why the
rule is checked mechanically and not left to review.

## Revisit if

django-cotton stops filling undeclared attributes from the surrounding context, or isolates
components by default. The attribute and the test would then be redundant.
