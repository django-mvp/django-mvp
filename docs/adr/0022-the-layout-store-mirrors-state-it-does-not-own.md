# 0022 — The layout store mirrors state it does not own

**Status:** accepted

**Date:** 2026-09-15

## Context

The shell used to keep its layout state in three disconnected places: the sidebar's open state in
an expression on the drawer, the header's scroll state in a second one on the header, and a third
copy of the sidebar's remembered default in a script that ran before either. None of it was
readable from anywhere else, so a project that wanted its own markup to respond to the shell had to
reimplement the logic against the package's internal structure.

Publishing that state as one store is the obvious fix. The question the fix raises is whether the
store should then *own* the state — whether it becomes the single source of truth that everything
else, including the markup, follows.

It cannot, for the same reason responsive visibility cannot be script-driven
([ADR 0021](0021-responsive-visibility-is-resolved-by-the-browser.md)). The drawer's open state is
established during parse, by a blocking script, precisely so that a sidebar left open on the last
visit is already open on the first frame. A store's state is established when the deferred bundle
runs, which is later. Making the store authoritative would move the sidebar's resting position
behind the bundle and undo that.

There is a second reason. The drawer's state lives in a checkbox, and the stylesheet reacts to that
checkbox directly through the package's drawer-state variants. The sidebar's width, the icon rail
and the drawer's side panel all depend on it, and they cost nothing because the browser is doing
the work. A store that owned the state would have to drive those too.

## Decision

The store reports state it does not own. Where the shell already has a source of truth, the store
reads it and stays in agreement with it in both directions, and the stylesheet keeps reacting to
that source directly.

Nothing about the shell's appearance at first paint depends on the store existing. Everything that
decides what the first frame looks like is resolved before it — and the store reads *that*, rather
than computing the same thing a second time. A page that renders no shell at all still gets a
store, reporting package defaults rather than throwing.

The store carries the shell's layout settings and nothing else. The theme reaches the browser by
its own route, and the remaining settings are read on the server to decide what to render, with
nothing on the page reacting to them. Publishing them would add surface the package has to keep
stable in exchange for no capability.

## Consequences

A project writes one attribute against a documented name to make its own markup follow the sidebar,
the collapse mode, the viewport, or whether the header has scrolled. It does not duplicate a
setting, hard-code a pixel width its own configuration can change underneath it, or read the
package's class names.

Because the store reads rather than recomputes, facts the shell resolves have one definition each.
The sidebar's remembered default and its storage key are resolved once, before first paint, and
handed to the store through the markup.

A boosted navigation is the one place the mirror needs care: the body is replaced, the drawer is a
new element rendered closed, and a store that simply carried its old value across would leave a
mobile overlay open where the package closes it. The store re-derives its state when that happens.

The store is public surface from the day it ships. It is named, documented, and carries the same
compatibility expectations as any component attribute.
