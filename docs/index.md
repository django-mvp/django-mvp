# django-mvp Documentation

django-mvp gets a Django project to a polished, production-looking application as fast
as possible: a settings-configurable app layout (DaisyUI 5 + Tailwind CSS v4), a library
of [django-cotton](https://github.com/wrabit/django-cotton) UI components, and enhanced
class-based views with search, ordering and pagination out of the box.

**The overriding design goal: things should just work.** Sensible defaults everywhere,
configuration through Django settings, customization through template overrides.

## Guides

| Guide | What it covers |
| --- | --- |
| [Getting Started](getting-started.md) | Installation, settings, your first page |
| [Layout](layout.md) | The app shell and its `MVP_CONFIG` configuration — sidebar breakpoint, collapse modes, navbar widgets |
| [Components](components.md) | The Cotton component library reference |
| [Navigation](navigation.md) | Sidebar and mobile-dock menus via django-flex-menus |
| [Views](views.md) | List/form/detail/delete views and mixins |
| [Styling](styling.md) | Tailwind/DaisyUI, theming, and building your own CSS |
| [Integrations](integrations.md) | Optional third-party integrations (django-tables2, django-filter, crispy forms) |

## Design philosophy

1. **Configuration-driven** — layout and behavior are controlled from `settings.MVP_CONFIG`,
   in the spirit of pydata-sphinx-theme's layout configuration.
2. **Basic, consistent components** — components expose a small attribute API. django-mvp
   is deliberately *not* a highly-customizable component framework: if you need more than
   the attributes offer, override the component's template in your project.
3. **Template overrides are the extension point** — drop a template at the same path in
   your project to replace any packaged component.
4. **Optional integrations, not extras** — views that build on third-party packages live
   in guarded modules under `mvp.integrations` and only require the package when imported.
