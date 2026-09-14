# 0020 — An area gates its own pages and never another app's

**Status:** accepted

**Date:** 2026-09-14

## Context

The Account Center is a place where apps put pages about a person's own account: notification
preferences, API keys, a billing summary. Every one of those pages is for a signed-in person, which
makes it tempting to say the area requires a signed-in person — one rule, stated once, inherited by
everything inside.

The package cannot keep that promise. What the area gives a contributed page is a menu entry and a
layout. Neither sits in the request path of the view behind that page. The app owns its own URL,
its own view and its own dispatch, and a template it extends has no say in who reached it. An area
that claimed to require sign-in would be describing a guarantee enforced nowhere, which is worse
than not claiming it: a contributor who believes it would stop writing the check themselves.

There is a second, quieter version of the same mistake. A menu entry can be hidden from people it
does not apply to, and hiding an entry feels like access control. It is not. It decides what is
drawn, not what is reachable.

## Decision

An area requires a signed-in person for the pages it serves itself. The Account Center's landing
page does, and sends an anonymous visitor to the project's configured sign-in location.

A page an app contributes to an area decides its own access rules, exactly as any other view in
that project does. The area supplies no mixin for the page at all — not for access, and not for
its trail either, which the page declares itself — so a contributing app composes
`LoginRequiredMixin` or whatever its own rule is onto a plain view of its own.

A visibility check on a menu entry controls whether the entry is drawn, and is never described as
protecting the page behind it.

## Consequences

A contributor writes one more line — their own access mixin — and the documentation says so at the
point where they add a page.

The area cannot be blamed for an unprotected page, and cannot be trusted to protect one. Both halves
matter: the first is honest, the second is what stops a contributor relying on something that was
never there.

An entry hidden by a check still points at a reachable URL. Anyone who guesses the address reaches
the view, subject to whatever that view enforces. That is the correct behaviour for navigation, and
it is why the check is documented as visibility rather than permission.

## Alternatives considered

**Wrap contributed views in the area's own access rule.** It would need a registry of contributed
views and middleware or a URL wrapper to sit in front of them, turning a menu and a layout into a
framework that owns other apps' request handling. Article III rules that out, and it would still
miss any page reached by a URL the area does not know about.

**Say nothing, and let contributors infer.** Silence would be read as inheritance, because the area
is plainly about a signed-in person. The stated rule costs one sentence and removes the inference.
