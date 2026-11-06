# Planning notes

Sam's notes for research and planning, in his words or close to them. Each one is answered by name
when the feature is planned.

## Integrate django-object-preferences, don't rewrite it

django-object-preferences already stores per-record preferences declared as forms, and its README
names a person's theme and language as the example. django-mvp uses it as it is: its field, its
registry and its page. django-mvp gives the page the shell's look and places it in the Account
Center. (Sam, 2026-11-06: "integrate it, don't rewrite it.")

## A user model mixin, optional but strongly recommended

django-mvp provides a mixin a host project adds to its user model, so that any installed app
built on django-mvp can contribute to a person's preferences. The mixin is optional, and the
documentation strongly recommends it. (Sam, 2026-11-06: "Make the mixin optional but strongly
recommend it in documentation.")
