# Preferences

django-mvp stores each person's preferences on the user model and shows them on the Account
Center's preferences page. Any installed app can add a group of preferences to that page and read
a person's values back. This page covers declaring a group, reading values and why you read them
the way you do. The page itself, and the timezone and language group django-mvp declares, are
described in [Account Center](../account-center.md#the-preferences-page).

Your project needs three things for this to work, all covered in
[Getting started](../getting-started.md): `object_preferences` in `INSTALLED_APPS`, a user model
with `mvp.models.PreferencesMixin` (or a `PreferencesField` under a name of your choice), and
`mvp.middleware.PreferencesMiddleware` below `AuthenticationMiddleware`.

## Declare a group of preferences for people

A group is a Django form registered for the user model. Put it in a module named `preferences.py`
in your app, which is loaded when the apps load:

1. Create `yourapp/preferences.py`.
2. Write a form with a field for each preference. Give every field an `initial`: that is the
   value a person has until they choose one.
3. Register the form for the user model with a group name.

```python
# yourapp/preferences.py
from django import forms
from django.contrib.auth import get_user_model
from object_preferences.registry import register


@register(get_user_model(), name="reminders")
class ReminderPreferences(forms.Form):
    digest = forms.ChoiceField(
        label="Digest",
        choices=[("daily", "Daily"), ("weekly", "Weekly")],
        initial="weekly",
    )
    page_size = forms.IntegerField(
        label="Items per page", min_value=5, max_value=100, initial=20
    )
```

Nothing else is wired. The group appears on `/account/preferences/` as a fieldset of its own
beside the others, and one Save button saves every group together. If a value in any group is
invalid, nothing in any group is saved and the field is marked in its own fieldset. The fieldset's
heading is the group name.

## Read a person's values

Read a person's preferences through the registry, not through an attribute of the user:

```python
from object_preferences.registry import registry


def page_size_for(person) -> int:
    return registry.get_preferences(person)["reminders"]["page_size"]
```

`registry.get_preferences(person)` returns the person's preferences. Indexing it by group name
gives that group's values, and a field the person has not chosen reads as its form's `initial`.
A group that nobody has saved yet reads entirely as defaults, so there is nothing to check for
first.

## Change a person's values in code

Change values on the same object and save it:

```python
preferences = registry.get_preferences(person)
preferences.change("reminders", digest="daily")
preferences.save()
```

## Why read through the registry and never through the attribute name

The field that holds the preferences is called `preferences` when the user model uses
`PreferencesMixin`, but a project whose user model already has an attribute of that name
declares a `PreferencesField` under another name, such as `options`. The registry finds the
field whichever name it has. Code that reads `person.preferences` works on the first project and
breaks on the second, and so does an app that other projects install. Reading through
`registry.get_preferences` means your app works unchanged on both.
