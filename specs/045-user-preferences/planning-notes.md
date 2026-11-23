# Planning notes

Sam's notes for research and planning, in his words or close to them. Each one is answered by name
when the feature is planned.

## Integrate django-object-preferences, don't rewrite it

django-object-preferences already stores per-record preferences declared as forms, and its README
names a person's theme and language as the example. django-mvp uses it as it is: its field, its
registry and its page. django-mvp gives the page the shell's look and places it in the Account
Center. (Sam, 2026-11-06: "integrate it, don't rewrite it.")

## A user model mixin, required

django-mvp provides a mixin a host project adds to its user model, so that any installed app
built on django-mvp can contribute to a person's preferences. Every project needs it, or at least
the preferences field. (Sam, 2026-11-06: "The mixin (or at least the preferences field) becomes
required.")

## The field may have another name

A host project may already have a `preferences` attribute for another purpose, so the field must
be able to carry a different name. Sam suggested a class constant pointing at the field's name, or
a class method returning the field. django-object-preferences already finds the field by its type,
so the name is free today. What it lacks is a public way to read a record's preferences without
knowing the name, filed as https://github.com/django-mvp/django-object-preferences/issues/27.
