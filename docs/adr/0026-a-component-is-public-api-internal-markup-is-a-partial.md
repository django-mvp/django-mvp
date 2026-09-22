# 0026 — A component is public API; markup with no consumer is an included partial

**Status:** accepted

**Date:** 2026-09-22

## Context

Reusable markup in this package is normally a Cotton component. That is the house answer, and it
is a good one: a component gets a name, a documented set of attributes, and a place a project can
override by name.

The development-only notice that appears on the sign-in and signed-out pages is reusable markup
appearing on two pages, so the reflex is to make it a component. Following the reflex would have
published a third name in the component library.

## Decision

A Cotton component is this package's public API — something a project is invited to use, compose
with, and override by name. Markup that is none of those is an included partial, named with a
leading underscore and placed beside the templates that include it.

The notice is `mvp/templates/mvp/account/_development_notice.html`, included by the two packaged
pages.

## Why

The notice exists to be read once by a developer and then to stop existing: installing an
account-management application takes the pages away, and the notice with them. A component is a
promise that something is there to be built on. Publishing one with no consumer and no successor
would be a promise the package intends to break.

The override point a project actually needs is the page template, which it already has. A project
that puts its own template at `mvp/account/login.html` decides for itself what appears there,
notice included.

There is also a cost to the library itself. Every component is a name the package owns and has to
keep working. Spending one on markup whose whole purpose is to disappear makes the public surface
larger and less meaningful at the same time.

## Consequences

The component library stays the list of things a project may compose with, and reading it tells
you what this package offers rather than how its own pages happen to be assembled.

Internal markup has an obvious home and an obvious signal: the underscore prefix says "this is
ours", so a contributor does not have to check whether something is part of the public surface
before changing it.

A project cannot override the notice by name. It can replace the page that includes it, which is
the coarser and more honest instrument.

## Alternatives considered

**Make it a component anyway, and document it as internal.** A documented-as-internal component is
still importable by name, and the documentation is the only thing stopping someone depending on
it. The template loader gives a stronger signal for free.

**Duplicate the markup in both templates.** Two copies of the same notice drift, and the second
one is the one nobody updates. The partial costs nothing and the pages are its only callers.
