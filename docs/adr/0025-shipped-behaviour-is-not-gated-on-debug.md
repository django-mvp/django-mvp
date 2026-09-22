# 0025 — Shipped behaviour is not gated on `DEBUG`

**Status:** accepted

**Date:** 2026-09-22

## Context

The package ships a sign-in and a sign-out page meant for local development. Something that exists
for development invites a debug gate, so that it cannot reach production by accident.

The reflex is `if settings.DEBUG`. It is the first thing a reviewer asks for, and it is worth
recording why the answer is no, because the same question will arrive with the next development-only
surface.

## Decision

Nothing this package ships changes shape according to `settings.DEBUG`. The development sign-in
pages are registered, and behave identically, wherever they are mounted.

Where a shipped surface is meant for development only, it says so on itself. The two pages carry a
notice naming what they do not do and what to install instead.

## Why

A debug gate makes a project's URL configuration differ between environments. The first time
anyone discovers the pages are absent is after a deployment — on a staging build that still needs
to be signed in to, or in a test run that sets `DEBUG = False` and now cannot reverse a name the
shell's markup reverses.

It also contradicts the notice. Telling a reader to install account management before going to
production only means something if the pages would otherwise still be there. A gate turns that
sentence into a falsehood the code quietly corrects.

The failure the gate is imagined to prevent — someone shipping these as their real sign-in — is a
decision a person makes, not an accident the framework can catch. The honest place to intervene is
the page they are looking at while they make it.

## Consequences

A project that deploys without installing account management gets working sign-in pages that say
they are not for this. That is the intended outcome, and it is better than a broken link.

Tests exercise the same code paths production does, and no test needs to toggle `DEBUG` to reach
shipped behaviour.

Any future development-only surface in this package inherits the rule: make it self-describing on
the page, not conditional on a setting.

## Revisit if

A surface appears whose presence in production is genuinely dangerous rather than merely
inadequate — something that discloses data or bypasses a check. A notice is the right instrument
for "this is not enough yet"; it is the wrong one for "this must never run here", and that case
would deserve its own decision rather than an extension of this one.
