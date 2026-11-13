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

## Search a model

A model kind searches the records of one model that
[django-modelsearch](https://github.com/django-modelsearch/django-modelsearch)
indexes. It decides what each request may see, so a record a visitor may not
open is neither listed nor counted.

1. Index the model. Add `SearchField`s for the text to search, an
   `AutocompleteField` for any field that should be found from a partly typed
   word, and a `FilterField` on the primary key. The primary key field must be
   named by its real name, `"id"` for an automatic key. `FilterField("pk")` is
   not recognised.

    ```python
    # notes/models.py
    from django.db import models
    from modelsearch import index


    class Note(index.Indexed, models.Model):
        title = models.CharField(max_length=100)
        body = models.TextField(blank=True)
        public = models.BooleanField(default=True)

        search_fields = [
            index.SearchField("title"),
            index.SearchField("body"),
            index.AutocompleteField("title"),
            index.FilterField("id"),
        ]
    ```

2. Add `modelsearch` to `INSTALLED_APPS` and run `migrate`, so the index has a
   table.

3. Subclass `ModelKind`, set `model` and define `get_queryset(request)`. It has
   no default: a model kind without it raises `ImproperlyConfigured`, so no kind
   searches records nobody decided a request may see. The queryset may filter on
   any field, indexed or not.

    ```python
    # notes/search.py
    from django.utils.translation import gettext_lazy as _
    from mvp.search import ModelKind

    from .models import Note


    class NoteKind(ModelKind):
        name = "notes"
        label = _("Notes")
        icon = "file-text"
        model = Note

        def get_queryset(self, request):
            return Note.objects.filter(public=True)
    ```

4. Register an instance from `AppConfig.ready`, as for a function kind.

A model kind searches whole words first. When that finds nothing and the model
has an `AutocompleteField`, it searches again by completion, so `hea` finds
"Heat flow". Double quotes are removed from the query before it is searched.

Each result is titled `str(obj)`, linked to `obj.get_absolute_url()`, labelled
with the model's `verbose_name` and has no passage. Override `title(obj)`,
`url(obj)`, `where(obj)`, `passage(obj)` or `more_url(query)` to change any of
them.

A kind's `label` and `description` are shown to every visitor, including one
who may open none of its records. Records are scoped by the request, so this
discloses only that the kind exists.

## Mount the search's pages

The search has two pages: the results page and a partial the search dialog
fetches as the reader types. Mounting them is how a project turns the search
on.

1. Include the search's addresses in the project's URLconf.

    ```python
    # urls.py
    from django.urls import include, path

    urlpatterns = [
        path("search/", include("mvp.search.urls")),
    ]
    ```

2. Open `/search/?q=heat`. Every active kind is a link above the results with
   how many it found, kinds that found nothing included. Each kind that found
   something shows its first six results and a link to the rest.

3. Follow a kind's link, or add `kind=<name>` to the address, to see only that
   kind. Its results come twenty to a page. A `kind` no active kind has is
   ignored.

The results page is `mvp.search.views.SearchView`, a shell page whose title is
"Search", so a project can subclass it to change the title or the template. Both
pages read the query with `mvp.search.views.clean_query(request)`, which strips
it and cuts it to 100 characters exactly as `search()` does. Both call
`mvp.search.registry.normalise_query(text)`, which you can call yourself to clean
a query typed somewhere else the same way.

The pages work for anonymous visitors. Each kind decides from the request what
the visitor may see, so a signed-out visitor sees only what the kind lets a
signed-out request see.

The partial is the function view `mvp.search.views.search_panel`, at `panel/`
under the same prefix. It shows up to four results
a group, leaves out kinds that found nothing, and for an empty query lists
every active kind with its description. A group with more results links to the
kind's own `more_url(query)` when it gives one, and otherwise to the results
page narrowed to that kind. The results page lists the narrowing link too, and
adds the kind's own address beside it.

## Place the search widget

The widget is the bundled navbar action `mvp.actions.search`: a search field on
a wide screen, a button on a narrow one, and the dialog both open. Ctrl K (⌘ K
on a Mac) opens the dialog from anywhere.

1. Mount the search's pages, as described above. The widget fetches its results
   from them.

2. Add the widget to `layout.navbar.end`.

    ```python
    # settings.py
    MVP_CONFIG = {
        "layout": {
            "navbar": {"end": ["mvp.actions.search", "mvp.actions.login"]},
        },
    }
    ```

Naming the widget without mounting the pages is reported as `mvp.E009`. The
widget replaced the earlier `c-mvp.actions.search` button, which linked to a
page of your own: it now opens this search, so a project that placed it before
needs the pages mounted.

## Ship a kind in a package

A package that has searchable content registers its own kind, so a project gets
the search by installing it.

1. Register the kind from the package's `AppConfig.ready`, as for a function
   kind. Give `name` a prefix the package owns, because names are unique across
   every installed package.

2. Tell the project's developers to add the name to `search.kinds` if they
   limit the kinds. A project that leaves the setting empty searches the
   package's kind with no further step.

3. For a model kind, document that the project needs `modelsearch` in
   `INSTALLED_APPS` and a run of `migrate`. A model kind registered without it is
   reported as `mvp.E008`.

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

## Fix a start-up check error

`manage.py check` reports a mistake in the search setup before a visitor meets
it. Each error says which kind or name is at fault.

| Error | Cause | Fix |
| --- | --- | --- |
| `mvp.E004` | `search.kinds` names a kind nothing registers | Register the kind from `AppConfig.ready`, or remove the name |
| `mvp.E005` | The search's addresses are mounted and no kind is active | Register a kind, and check `search.kinds` names one |
| `mvp.E006` | A model kind's model is not indexed | Make the model inherit `index.Indexed` and give it `search_fields` |
| `mvp.E007` | The model has no `FilterField` on its primary key | Add `index.FilterField("id")`, naming the key by its real field name. `FilterField("pk")` does not count |
| `mvp.E008` | A model kind is registered and `modelsearch` is not installed | Add `modelsearch` to `INSTALLED_APPS` and run `migrate` |
| `mvp.E009` | `mvp.actions.search` is in `layout.navbar.end` and the search's addresses are not mounted | Mount them with `path("search/", include("mvp.search.urls"))` |

## The demo

The demo registers three kinds in `demo/apps.py`: `ProductKind` and
`ArticleKind`, which search models indexed with `modelsearch`, and a function
kind over the component pages. Draft articles are listed only for staff. The
demo mounts the pages at `search/`, puts the widget in its navbar and sets
`search.kinds` to order the groups. Run `migrate` once, then
`rebuild_modelsearch_index` to index the records already in the database.

## Why a kind decides what a request sees

Each kind scopes its own records and nothing is filtered afterwards. A record a
visitor may not open is then never listed, never counted and never linked, which
a filter applied to a page of results could not promise. That is also why a
model kind has no default `get_queryset`: a kind that searched every record by
default would show a visitor whatever its author forgot to hide.
