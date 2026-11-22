# ADR 0045 — Reordering announces its start and end on the list

**Status:** accepted

## Decision

A reorderable list dispatches `mvp:reorder-start` and `mvp:reorder-end` on its own root element when reordering starts and ends. Both bubble and carry `detail.source`, one of `drag`, `button` or `mode`. A drag and a move by button each fire a pair, and a reorder mode fires one pair around the whole mode.

Other behaviour on a list's rows listens for these events and pauses itself. The list never reaches into that behaviour to turn it off.

## Why

A row that can both be dragged and acted on by another gesture, such as being swiped for its actions, would answer one touch two ways. The list could switch the other behaviour off itself, but then it would depend on every behaviour that might share its rows, and each new one would have to be found and edited into it.

Announcing on the list inverts that. The list knows nothing about its neighbours, and a neighbour that needs to pause adds one listener. It also keeps the two features buildable at the same time, since neither one's code names the other.

## Revisit if

A behaviour needs to refuse a drag before it starts rather than pause after it, which would need a cancelable event.
