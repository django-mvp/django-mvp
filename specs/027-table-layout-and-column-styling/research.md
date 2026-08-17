# Research — 027 Full-screen tables and column styling helpers

Everything below was read out of the installed source or the built stylesheet on 2026-08-17, not
recalled. Versions: django-tables2 3.0.0, daisyUI as bundled in `mvp/static/css/django-mvp.css`.

## R1 — Sticky heading and footer rows already exist in the shipped stylesheet

daisyUI's pinned-row utilities are present in the built CSS:

```css
.table :where(.table-pin-rows thead tr){z-index:1;background-color:var(--color-base-100);position:sticky;top:0}
.table :where(.table-pin-rows tfoot tr){z-index:1;background-color:var(--color-base-100);position:sticky;bottom:0}
```

That is FR-003 and FR-004 in two class names, against the scroll container the table sits in. No
bespoke sticky CSS is needed, and none should be written.

**The catch, and it is a real one.** These rules are emitted only because
`assets/tailwind.css:37-38` blanket-scans the whole daisyUI component and utility source. Nothing
safelists them by name, and `mvp/tailwind/base.css` — the preset a consumer project imports when it
generates its own stylesheet with `mvp_tailwind` — carries no `table-*` entry at all. A consumer
building their own CSS would get the packaged markup without the rules behind it. So the classes go
into the `@source inline(...)` block in `mvp/tailwind/base.css`, alongside the existing drawer,
button and grid entries. The package already treats this as a standing obligation: two template tags
carry comments tying their emitted classes to that safelist.

## R2 — A column's model field is reachable, but only from Python

`Accessor.get_field(model)` exists and does exactly what the feature needs
(`django_tables2/utils.py:415-431`): it walks the accessor's `__`-separated bits through
`model._meta.get_field`, follows relations, and returns `None` when the model is not a model. The
library's only caller is `BoundColumn.verbose_name`, which sources the model from
`self._table.data.model`.

Two facts decide the shape of the implementation:

- `table.data.model` is `None` for data that is not a queryset. That is FR-018 and FR-021 for free:
  no model, no field, no alignment, and the table renders as it does today.
- `BoundColumn._table` is private, and Django's template engine refuses to resolve names beginning
  with an underscore. **A template cannot reach the table from a bound column.** So the inference
  cannot be a filter over a column alone — it has to be a tag taking the column and the table
  together, which is what the table template has in scope.

This is why the intake's instinct was right. A tag reads both, and no author has to import or
subclass anything.

There is no numeric column class to key off. django-tables2 registers thirteen column classes and
dispatches per model field through `library.column_for_field`, and `IntegerField`, `DecimalField`
and `FloatField` all fall through to the base `Column`. The model field is the only thing that
distinguishes a number from a string.

**Action columns.** `BoundColumn` has no "is an action" flag, and `column.accessor` is never empty —
when an author declares no accessor, `BoundColumn.__init__` fills it in from the column's name
(`columns/base.py:449-450`). So an action column looks structurally like any other. The workable
signal is the pair: `get_field()` returns `None` *and* the column is not orderable. That is what a
buttons column looks like and what a plain unresolvable text column does not.

## R3 — How author-declared classes and inferred ones have to combine

`BoundColumn.attrs` (`columns/base.py:458-502`) merges the table's attrs with the column's by
`dict.update`, per key. A column declaring `attrs={"td": {"class": "..."}}` **replaces** the table's
`td` dict wholesale — there is no concatenation anywhere in the library. The computed class string
comes out of `get_td_class`/`get_th_class` as `" ".join(sorted(classes))`.

Consequence for FR-019: the tag must not blindly append. It reads the already-computed class string
for the cell, and contributes an alignment class only when none is present. An author who wrote one
keeps it. This also keeps the tag idempotent, which matters because `attrs` is a property
re-evaluated on every access.

`Table.get_column_class_names(classes_set, bound_column)` (`tables.py:644-676`) is the library's
documented Python-side hook and is a passthrough by default. It was considered as the insertion
point and rejected: it would put the behaviour on a table base class the author has to inherit,
which is the surface the intake ruled out.

## R4 — Where the new code goes, by existing convention

- **Template tags**: one library, `mvp`, one module, `mvp/templatetags/mvp.py` (342 lines), tested by
  `tests/test_templatetags.py`. Tags are registered with `@register.simple_tag`, some
  `takes_context=True`; there is no `inclusion_tag` in the package. A tag that builds class strings
  carries a comment tying it to the safelist — the convention to follow here.
- **Configuration**: `mvp/config.py` is a module-level dict literal with four top-level sections
  today — `view_names`, `brand`, `theme`, `layout` — merged once at import with the project's
  `settings.MVP_CONFIG` via `mergedeep.merge`, and exposed to templates as `mvp_config` by a context
  processor. Each default carries a comment above it stating accepted values and why the default is
  what it is. Tests deep-copy the defaults and merge directly rather than patching settings, because
  the config is a process-wide singleton merged at import.
- **Table markup**: `mvp/templates/django_tables2/bootstrap5-mvp.html`, 94 lines, the only file in
  that directory. It applies the daisyUI `table` class at line 19 via
  `{% render_attrs table.attrs class="table" %}`, so `table-pin-rows` can arrive either there or
  through a table's `Meta.attrs`. It carries an inline `<style>` block (lines 5-18) for sort-icon
  visibility that is emitted on every render.
- **The reusable component**: `mvp/templates/cotton/addons/django_table.html`, four lines, currently
  `overflow-x-auto` plus a `min_height` interpolated into an inline `style`. Both `.table-container`
  and the `table-compact` class used by `table_view.html` are undefined — dead classes with no rule
  behind them anywhere.

## R5 — The height chain is already solved and must not be re-solved

`<c-page fill>` marks itself `.mvp-page-fill`, and one scoped rule in `mvp/tailwind/base.css` gives
`.drawer-content:has(.mvp-page-fill)` a flex column and a `100dvh` floor. `<c-page.content>` is
already `flex-1 min-h-0 flex flex-col`, which is the flex-child scroll primitive this feature needs
between the page and the scroll container. The `min-h-0` matters: without it a flex child refuses to
shrink below its content and the scroll container never scrolls.

The `100dvh` floor rather than inheritance is deliberate and documented: above the sidebar
breakpoint `.drawer-side` is a persistent `100dvh` grid column that `.drawer-content` stretches to
match, but below it `.drawer-side` is `position: fixed` and out of flow, so a page relying on
inheritance fills the shell on a desktop and collapses to zero height on a phone. This is why FR-011
insists on both viewports and why the existing end-to-end suite runs every case at 1440x900 and
390x844.

## R6 — What the scrollbar requirement actually asks for

FR-005 wants the vertical scrollbar to span the full height of the table area, alongside the fixed
heading and footer rather than starting below the heading. That falls out of putting `overflow-y`
on the container and the sticky positioning on the rows, which is what the daisyUI utilities do —
the rows are sticky *within* the scrolling container, so the container's scrollbar is full height by
construction. The alternative shape, a separately scrolling `tbody`, is what produces a short
scrollbar and misaligned columns, and is not used here.

`scrollbar-gutter: stable` is worth carrying over from the sidebar rule at `base.css:327-334`, so the
table does not shift horizontally when the scrollbar appears between pages of differing length.

## R7 — Accessibility of the scroll container

A `div` with `overflow: auto` is scrollable by wheel and trackpad everywhere, but only Chromium
gives it keyboard focus automatically. Firefox and Safari require an explicit tab stop, so without
`tabindex="0"` a keyboard-only reader cannot scroll a read-only table's rows at all — there is no
focusable element inside them to tab to. Paired with `role="region"` and an accessible name, this is
the standard scrollable-region pattern and satisfies FR-025 and Article XIII.

## R8 — Test strategy the constitution allows

Article XIV reserves browser tests for behaviour that genuinely needs a browser and asks for
rendered-template assertions everywhere else. That splits cleanly here:

- **Browser** — that the window does not scroll, that the heading stays visible at the last scroll
  position, and that both hold at 390x844 as well as 1440x900. Computed geometry is the only
  evidence for these, and `tests/test_full_page_fill_e2e.py` is the precedent for the shape.
- **Rendered template** — every class the markup emits, the config resolution order, the inferred
  alignment per column kind, an author's explicit class winning, and the no-model fallback. None of
  these needs a browser.
- **Python** — that a table view declaring an ordering fails with the message naming the table.

The two viewports fail for different reasons, so one is not evidence about the other. That is stated
in the existing suite's commit message and holds here.
