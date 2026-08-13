# 0011 — Theme names are not validated

**Status:** accepted

**Date:** 2026-08-13

## Context

A project names its theme in `MVP_CONFIG`. The name might be one the package ships, one the project
wrote itself, or a typo. The obvious instinct is to check it and report a clear error, and the
specification for this feature originally required exactly that: a start-up message naming the
setting and the unavailable theme.

## Decision

The package does not validate theme names. A name is applied as given. If no theme block matches it,
the document falls back to the default theme and renders normally.

## Consequences

**The check cannot be evaluated.** A project's own theme is a block of custom properties in a CSS
file the project loads and the package never reads. The package therefore has no way to know whether
a given name will resolve at page load. Validating against the themes it ships would reject every
custom theme, which is the case this feature exists to support.

The only way to keep a check would be a registration list in configuration, kept in step by hand with
the project's own stylesheet. That converts an extension point that costs nothing into a list that
has to be maintained, and it can still drift.

**Falling through is benign rather than broken.** The default theme is bound through a
zero-specificity `:where(:root)` rule, so an unmatched `data-theme` value leaves the default in
effect. There is no unstyled state to protect against, which is what makes silence safe here rather
than merely convenient.

**The obligation moves to documentation.** A developer whose theme does not appear needs to be told
the name simply matched nothing, or they will go looking for the fault inside their CSS.
`docs/theming.md` covers it, and a test guards the absence of validation so a later reader does not
mistake it for an oversight and add it back.

## The general form

A validation rule the package cannot evaluate completely is worse than none, because it converts an
open extension point into a closed list. This applies beyond themes, to anything a consuming project
can supply from its own files.
