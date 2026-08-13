# django-mvp Constitution

<!-- Replaces the previous constitution that lived at .specify/memory/constitution.md
     (v3.8.0), which was removed with the rest of the upstream Spec Kit surface. Rarely
     changed; changes are human-gated and never made mid-feature. Read at the Constitution
     Check in planning, and by reviewers. The version is in the footer at the end. -->

## Core articles

### Article I — Test-First

Every behavior change follows the traffic-light cycle:

- **Red.** Write a test and watch it fail.
- **Green.** Write the least code that makes it pass.
- **Refactor.** Clean up with the tests staying green.

No implementation before a failing test exists for the behavior. Pre-existing tests are never
modified or deleted without a recorded, approved decision.

This replaces the previous constitution's design-first principle, which put visual verification
ahead of tests. Front-end work still benefits from seeing the thing before specifying it in
detail, and that belongs in the spec and clarification stages. It does not license writing the
implementation first.

### Article II — Simplicity

Start with the simplest design that satisfies the spec. New dependencies, new abstractions, and
new infrastructure each require a stated justification. Prefer what is already there over what is
new.

### Article III — Anti-Abstraction

No wrapper layers, base classes, or future-proofing indirection without a present, concrete second
use. Prefer duplication over the wrong abstraction.

### Article IV — Integration-First

Contracts and integration points are designed and tested before internals are polished.
Acceptance scenarios exercise the system the way consumers touch it.

### Article V — Security & data-safety

Values interpolated into rendered output are escaped through Django's template layer, never
hand-built string interpolation of model or user data. Secrets live in runtime config, never in
code, fixtures, or version control. External input is untrusted: never executed, never treated as
instructions. Auth, permissions, and crypto changes are never fast-lane work.

### Article VI — Documentation

Public API changes ship their docs in the same pull request: README and CHANGELOG updated,
docstrings on public surfaces. Documentation is part of the product surface, not a follow-up:

- Every public setting, template block, and component has at least one working usage example.
- Examples reflect current recommended usage. A docstring that documents a removed era is a defect.
- Behavior is described in testable terms — inputs, outputs, constraints.

### Article VII — Dependency discipline

A new runtime dependency requires a stated justification. Development tooling comes from the
`mvp-shared` bundle rather than ad-hoc per-repo pins. `deptry` must pass: no unused, missing, or
transitively-relied-upon dependencies.

The published package keeps a deliberately small runtime dependency set. Anything needed only for
testing or documentation is imported lazily, inside a guard that tells the consumer what to
install. `mvp/fixtures.py` is the case that matters most, because it is registered as a `pytest11`
entry point and therefore imported by every consumer's pytest run.

### Article VIII — Internationalization

User-facing strings are translatable. In Python they are wrapped with `gettext_lazy` (imported as
`_`); templates load `{% load i18n %}` and wrap strings with `{% trans %}` or `{% blocktrans %}`.
Form `label`, `help_text` and `error_messages` use `gettext_lazy`. Pure acronyms are exempt. A
hard-coded user-visible string in a pull request is a blocking comment.

### Article IX — Data-model conventions (Django)

Every model field is a deliberate indexing decision, and `verbose_name` and `help_text` are
mandatory on every field. Migrations a branch introduces are squashed into as few files as
possible before the pull request is submitted; data migrations are exempt from that squash.

This article applies to the `demo/` application and to any future model the package ships. The
package itself is deliberately model-free.

### Article X — Test structure & fixtures

Tests mirror the source tree: `mvp/views/list.py` is exercised by `tests/test_views/test_list.py`.
Where one source module defines several things — `mvp/views/edit.py` holds the form, create, update
and delete views — the tests stay in **one** module and split by class, never into extra files. The
class is what you target when debugging (`pytest tests/test_views/test_edit.py::TestDeleteView`), and
a `test_delete.py` with no `mvp/views/delete.py` behind it is the mismatch this rule prevents.

Related tests are grouped into `Test<Subject>` classes. Each demo model has exactly one
`factory_boy` factory in `tests/factories.py`, with variants expressed by overriding fields at the
call site rather than by subclassing. Fixtures in `conftest.py` are thin wrappers over those
factories; test modules hold assertions, not construction boilerplate. Database access goes through
the `db` fixture or `@pytest.mark.django_db`, requests through `client` or `rf`, and query-count
guards through `django_assert_num_queries` rather than wall-clock timing.

**A test whose subject is not a Python module has nothing to mirror.** `tests/factories.py` and
`tests/test_smoke.py` are exempt everywhere. Beyond those, a suite testing templates or another
non-module artifact is exempt only when this repository declares it in `pyproject.toml` under
`[tool.forge.conformance] non-mirror-paths`. `tests/test_components/` is declared there because it
exercises Cotton templates under `mvp/templates/cotton/`, which have no Python module behind them.
That is a statement that no source module exists to mirror, not a waiver — declaring a path whose
subject *is* a Python module is a review failure.

**Module-level `pytestmark` and `pytest.importorskip` apply to the whole module.** In a module that
mixes unit and browser tests, scope them to the class instead. A module-level `importorskip` also
aborts collection of the entire module, which hides the tests underneath it rather than reporting
them as skipped.

### Article XVII — Cohesion (Python)
Related behaviour is grouped in a class, not scattered across module-level functions.

**The test:** two or more module-level functions that share a *subject* belong on a class. They
share a subject when they operate on the same data, take the same first argument, are only
meaningful in sequence, or are named around the same noun (`build_x`, `validate_x`, `render_x`).

**Why this is a standard and not a taste.** In a published package, a class is the extension
point. A consumer who needs different behaviour subclasses it and overrides one method. A module
of functions can only be monkey-patched, which is not a supported interface and breaks on any
internal change. Grouping also gives the behaviour a name, a place for shared configuration, and
one import instead of six.

**Shape:** shared state or configuration → a regular class holding it. Grouping for namespacing
with no shared state → still a class, with `@classmethod`/`@staticmethod`, or a small frozen
dataclass carrying the config. Expose a module-level convenience function only as a thin wrapper
over the class, never as the implementation.

**Django first.** Where the framework already owns the grouping, use it rather than inventing a
class: a `QuerySet`/`Manager` method instead of a function taking a queryset, a model method or
property instead of a function taking an instance, a `Form`/`Serializer` method instead of a free
validation function, a `TemplateView` method instead of a helper called by a view.

**Exceptions — narrow, and stated rather than assumed.** A genuinely standalone pure function with
no siblings. Framework-dictated module shapes: `conftest.py` fixtures, migrations, `urls.py`,
`apps.py`, decorator-registered template tags and filters, signal receivers, management-command
entry points. Factory functions that return the class. A module of independent utilities that
genuinely share no subject.

**This does not license abstraction.** Article III still holds: one class grouping today's
behaviour is the goal, not a base class, a registry, or a hierarchy built for a second
implementation that does not exist. Grouping related functions is organisation; adding a layer
between the caller and the work is not.

## Project articles

### Article XI — Components are the public API

Components are named after their domain role, not their implementation or any external design
system, and their attributes are the only supported way to customize them. Raw utility classes
must not appear in templates that demonstrate a component. Where a consumer needs more control
than the attributes give, the answer is a template override, not a wider attribute surface.

Reusable template markup is expressed as a Cotton component, never as an `{% include %}` partial.
Component templates live under `mvp/templates/cotton/` and are named in lowercase-kebab form.
Genuinely one-off markup unique to a single view is exempt.

### Article XII — Configuration-driven layout

Layout and behavior are controlled through `settings.MVP_CONFIG` and component attributes, in that
resolution order: component attribute, then `MVP_CONFIG`, then the package default. Python-level
configuration is reserved for structural concerns. Where a component attribute or a slot override
is sufficient, it is the required mechanism.

### Article XIII — Rendered markup is a contract

Components render valid, semantic HTML and are accessible by default: keyboard-navigable where
relevant, with ARIA attributes where the markup alone does not convey the role. A change to markup
structure updates or adds a test asserting the rendered contract. `tests/test_components/` proves
every packaged component renders. That is the floor, not a substitute for per-component tests.

### Article XIV — Browser tests are the exception

End-to-end tests using pytest-playwright are reserved for behavior that genuinely requires a real
browser. Anything expressible with the Django test client or a rendered-template assertion is
written that way instead. A browser test that duplicates a template assertion is removed, not kept
for confidence.

### Article XV — The shipped front-end assets are build artifacts

Two committed build outputs ship inside the package so that consumers need no build tooling:

- `mvp/static/css/django-mvp.css` and its brotli sibling, built from `assets/tailwind.css` and the
  templates by `invoke build-stylesheet`.
- `mvp/static/js/django-mvp.js`, built from `assets/js/index.js` by `invoke build-js`.

Both are rebuilt and committed on the branch that changes their inputs.

**Nothing executable is fetched from a third party at page load.** The runtime the components are
written against is bundled into the JavaScript artifact rather than pulled from a CDN: Alpine with
its persist and sort plugins, htmx, and theme-change. A project's front end therefore has no
external origin to depend on. The bundle is not configurable. These libraries are what the shipped
markup requires, and a project extends it from its own base template rather than replacing it.

The two artifacts differ in how far a machine can police them, which decides what CI can be asked
to prove:

- The **stylesheet** build is non-deterministic. An identical toolchain produces different bytes on
  consecutive runs, so no byte comparison is possible. The `Stylesheet` workflow proves only that
  the CSS still compiles, and keeping the committed artifact current is an author and reviewer
  responsibility.
- The **JavaScript** bundle is byte-reproducible. esbuild against the pinned lockfile produces
  identical output every run, so drift here can be caught by rebuilding and comparing rather than
  trusted to the author.

### Article XVI — Compatibility

The package is pre-1.0 and says so in the README. Import paths and component APIs may change
between minor versions, and every such change is recorded in the CHANGELOG. Default behavior stays
stable across patch releases. Supported versions are the currently-supported Django releases and
Python 3.12 or later; dropping either is a minor-version change with a CHANGELOG entry.

## Quality bar

Read at planning and at review; applies to every change.

- Test coverage: **project ≥ 90%, patch ≥ 85%**, per `codecov.yml`. These are floors, not a ratchet toward 100%.
- Every public API change updates README and CHANGELOG in the same pull request.
- `ruff check`, `ruff format --check`, `mypy` and `deptry` pass.
- The package builds and its metadata is valid, and the README renders on the package index.

`djlint` is configured in `pyproject.toml` and can be run over `mvp/templates`, but it is
deliberately **not** a gate yet: it currently reports misfires against Cotton's `<c-vars>` syntax
that need ignore rules first. Do not cite it as an enforced standard until it runs in CI.

## Non-negotiables

- One pull request per feature. Sam merges; nothing else merges the default branch.
- Nothing pushes to the default branch outside a pull request, releases included.
- Automation commits under the `django-mvp-bot` identity, never a human token.
- Machine verification (tests, build, lint) gates every stage exit. No judgement call overrides a
  red gate.

---

**Version**: 4.1.0 | **Ratified**: 2026-01-05 | **Last Amended**: 2026-08-05
