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
| [Configuration](configuration.md) | Every `MVP_CONFIG` key, its default, and how a value resolves |
| [Layout](layout.md) | The app shell — template blocks, breadcrumbs, per-page overrides, full-height pages |
| [Components](components.md) | The Cotton component library reference |
| [Navigation](navigation.md) | Sidebar and mobile-dock menus via django-flex-menus |
| [Icons](icons.md) | How a name resolves, what the packaged set defines, and using a different one |
| [Mounted apps](mounted-apps.md) | Running one django-mvp app inside another project: declaring, mounting, the host's menu entry, and what changes on the app's pages |
| [Account Center](account-center.md) | The account area any installed app can add a page to |
| [Views](views.md) | List/form/detail/delete views and mixins |
| [Formsets](formsets.md) | A parent record and its related rows, and the standalone formset case |
| [Styling](styling.md) | Tailwind/DaisyUI, the two build tiers, and the shell's class hooks |
| [Theming](theming.md) | Every theme variable, why the theme plugin computes nothing, and writing a custom theme from scratch |
| [Utility Classes](utility-classes.md) | Every Tailwind utility and daisyUI component the packaged stylesheet ships pre-built |
| [Installable app](installable-app.md) | Letting people install the project as an app: the setting, the root include, the packaged worker and the warnings |
| [Integrations](integrations.md) | Optional third-party integrations (django-tables2, django-filter, htmx) |
| [Troubleshooting](troubleshooting.md) | Common symptoms, their causes, and the fix |

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
