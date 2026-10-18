# ADR 0032 — A packaged template isolates its calls to components that need nothing else

**Status:** accepted; extended to the package's own components ([#485](https://github.com/django-mvp/django-mvp/issues/485))

## Decision

Every call a template under `mvp/templates/` makes to one of
[daisy-cotton](https://github.com/django-mvp/daisy-cotton)'s components carries Cotton's `only`:

```html
<c-button text="{% trans "Save" %}" variant="primary" only />
```

So does every call it makes to one of this package's own components when that component reads
nothing beyond its attributes and slots: the text, rule, group, grid, toolbar, container, card,
modal, dropdown, page shell, page title and info, pager wrapper, table toolbar and entrance
components, and the list page's search box, summary, refinements and empty state.

A component that needs something from the context processors (the request, the user, the CSRF
token, the messages, the mounted menu, `mvp_config`) cannot take `only`, which would hide those
too. Its call passes every value the view supplies explicitly instead, so the component draws
the same whether or not a project switches on django-cotton's `COTTON_ISOLATE_BY_DEFAULT`. Each
such component declares the names it reads in `<c-vars>`, with no default, so a project template
calling it bare still reads them from its page with the setting off.

The rule covers the templates the package ships. Demo pages and documented examples are written
the way a project writes them and do not carry `only`.

## Why

Cotton fills an attribute the caller did not pass from the surrounding template context when the
component declares it with no default. Many components declare `text`, `class`, `icon`, `items`,
`variant` or `size` that way. A packaged template renders inside pages this package has never
seen, so a view that puts an ordinary name such as `text` or `items` in its context could change
a link in the shell or the breadcrumb trail, with no error.

`only` stops the component seeing anything but what the tag passes. Content between the tags is
still rendered with the page's context, so a message's text or a list of records inside an alert
is unaffected.

The alternative was to give every attribute an empty default. That hides the leak in one
component while the templates calling it still depend on reading the page, and this package's
pages would depend on every later component and release keeping to it. A rule at the call site
does not.

The components that cannot take `only` are protected by `COTTON_ISOLATE_BY_DEFAULT`, and only if
the package's pages still work with it on. Until #485 they did not: the list page lost its
search box, sort, filter and add controls, and the shell lost its breadcrumb trail, because those
components read the view's values from the page instead of being handed them. A test renders
the list, table, detail, form, create, dashboard and error pages with the setting off and on and
fails when the two draw different controls.

A project override of a component whose call carries `only` sees only what that call passes.
That is the cost of the rule, and the reason it is limited to components that read nothing else.

## Revisit if

django-cotton stops filling undeclared attributes from the surrounding context, or isolates
components by default. `only` would then be redundant.
