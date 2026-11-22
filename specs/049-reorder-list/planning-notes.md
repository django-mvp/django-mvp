# Planning notes: Reorder a list by dragging

Notes for research and planning to answer by name. None of them is settled.

## The engine

1. Established packages over custom code. SortableJS, used directly or through Alpine's official
   Sort plugin (`@alpinejs/sort`, which wraps SortableJS), is the default over hand-written drag
   code. The package already bundles Alpine 3.16.1, and the Sort plugin is published at the same
   version. Hand-written pointer code is chosen only if research shows the plugin cannot meet a
   requirement (the held row following the pointer while the others make room, scrolling near the
   screen's edges, Escape returning the row, the touch rules in FR-011), and then the reason is
   recorded.
2. Every asset is vendored and shipped with the package (goal G14), never loaded from a CDN. The
   bundle in `assets/js/index.js` is where a new dependency joins Alpine and htmx.

## Shared pieces

3. Django formsets' `can_order` / `ORDER` field and a model's position field are the two things a
   reordered list saves to. django-mvp's existing formset rendering
   (`mvp/templates/cotton/mvp/form/formset/`, `mvp/static/js/formset.js`) is where the formset
   case plugs in (goal G4). Read ADR 0004 first: removed rows stay in the document and rows are
   never re-indexed, and reordering must keep to that.
4. FS-048 (https://github.com/django-mvp/django-mvp/issues/688, row actions) makes rows
   swipeable. This feature does not depend on it. The reorderable list announces on the list
   element when reordering starts and ends (documented events, named at planning, for example
   `mvp:reorder-start` and `mvp:reorder-end`), and FS-048 listens for them to turn swiping off and
   shut open rows. Document the events where the list's other public names are documented.

## Design rules

5. Edit modes copy the platform conventions: a reorder mode behaves like the edit mode of a
   phone's music app, started from a control, ended by Done or Escape.
6. `prefers-reduced-motion` is respected.
7. The look is agreed and is ported, never redrawn. Each row carries its position number, its
   title, up and down buttons and a drag handle at its end. The held row lifts, and the rows it
   passes slide out of its way. The build is given the reference markup and styles.
