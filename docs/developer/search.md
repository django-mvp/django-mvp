# Search

One search across the kinds of result a site has: its pages, its people, its
documents, whatever the project registers. Each kind answers the query on its
own and the answers are shown side by side, one group per kind.

## Register a function kind

A function kind is the shortest way to make something searchable. Write a
function that takes the query and the request and returns a list of `Result`,
then register it once the apps are loaded.

1. Write the function. It returns the results best match first, and decides
   from the request what the visitor may see.

    ```python
    # pages/search.py
    from mvp.search import Result


    def find_pages(query, request):
        pages = Page.objects.visible_to(request.user).filter(title__icontains=query)
        return [
            Result(
                title=page.title,
                url=page.get_absolute_url(),
                where="Pages",
                passage=page.summary,
            )
            for page in pages
        ]
    ```

2. Register it from `AppConfig.ready`. Nothing is found on its own, so a kind
   you have not registered is never searched.

    ```python
    # pages/apps.py
    from django.apps import AppConfig
    from django.utils.translation import gettext_lazy as _


    class PagesConfig(AppConfig):
        name = "pages"

        def ready(self):
            from mvp.search import register

            from .search import find_pages

            register(
                find_pages,
                name="pages",
                label=_("Pages"),
                icon="file-text",
                description=_("Pages of the site"),
            )
    ```

`name`, `label` and `icon` are required. `name` is unique: registering a second
kind under a name already taken raises `ImproperlyConfigured`. `label` and
`description` are shown to visitors, so pass lazy translations.

## Register a kind class

When a kind needs more than a function, subclass `Kind`, define `find()` and
register an instance. `find(query, request)` returns a sliceable, countable
sequence. Override `result(item)` to turn each item into a `Result`, and
`more_url(query)` to say where all of the kind's results can be seen.

```python
from mvp.search import Kind, register


class PeopleKind(Kind):
    name = "people"
    label = _("People")
    icon = "users"

    def find(self, query, request):
        return list(Person.objects.filter(name__icontains=query))

    def result(self, item):
        return Result(title=item.name, url=item.get_absolute_url(), where="People")


register(PeopleKind())
```

## Where kinds are kept

Registered kinds live in one `SearchRegistry`, held in
`mvp.search.registry.default_registry`. `register()`, `registered()` and
`search()` act on it. `registered()` returns the kinds in registration order.
A function registered this way is wrapped in a `FunctionKind`, which you can
also build yourself and register as an instance.

## What comes back

A kind's answer is a `Group`: the kind, the `results` to show, the `total` the
kind found, `more` (how many are not shown) and `more_url`. `more_url` is the
address the kind gives for its own full list, or `None`.

Results are never ranked across kinds. Each kind keeps its own order, and the
groups follow the order of registration.

## Choose which kinds are searched

By default a search asks every registered kind, in the order they were
registered. To search only some, or to change the order the groups come back
in, name the kinds in `MVP_CONFIG`.

1. Set `search.kinds` to the names, in the order you want the groups.

    ```python
    # settings.py
    MVP_CONFIG = {
        "search": {"kinds": ["people", "pages"]},
    }
    ```

A kind left out is never asked. A name no kind is registered under is skipped.
An empty list, the default, uses every registered kind.

## Run a search from Python

`mvp.search.search(request, query, limit)` returns one `Group` per active kind.

```python
from mvp.search import search

groups = search(request, "invoice", 4)
```

The query is stripped and cut to 100 characters before any kind sees it, and a
query that is empty or only spaces returns no groups. `limit` is the most
results in each group. An error raised inside a kind is not caught, so a broken
kind shows up as an error rather than a quietly empty group.
