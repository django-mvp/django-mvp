# Planning notes: Swipe and menu actions on list rows

Notes for research and planning to answer by name. None of them is settled.

## Shared pieces

1. The ⋯ menu opens in FS-047's sheet (https://github.com/django-mvp/django-mvp/issues/687) on a
   touch screen and in `c-mvp.dropdown` with a mouse. Build waits for FS-047 to merge.
2. The row builds on the package's existing list row components (daisy-cotton `list/row`, and
   django-mvp's list pages) rather than a new row of its own.
3. FS-049 (https://github.com/django-mvp/django-mvp/issues/689, reorder list) needs swiping turned
   off while a list is being reordered: the row exposes a way to switch swiping off for a list and
   to shut an open row.
4. Gesture code is the package's own small script, shipped with the package (goal G14), never
   from a CDN.

## The look

5. The look is agreed and already exists. At build time its templates, styles and gesture script
   are copied across and cleaned to this package's standards, never redrawn. The build session is
   told where they are. That includes the row narrowing rather than sliding, so the start of its
   content stays where it was and the reader can still see which row the actions act on, and the
   main action widening to fill the row past the 60% point.
6. Rows, ⋯ menus and edit modes copy the platform conventions of music and mail apps. No status
   badges in list rows.

## Defects the existing implementation has, not to be carried forward

7. Its menu is drawn twice and one copy hidden with CSS, so ids and form hooks appear twice
   (FR-005, D10).
8. Its script interface is published under one global name while a caller looks for another, so
   an open row never shuts when reordering starts. The script interface is one named thing that
   this feature documents and its siblings use (FR-024, D7).
