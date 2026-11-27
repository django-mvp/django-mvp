# ADR 0047 — The card and the modal override daisy-cotton's, and are built from parts

**Status:** accepted. Supersedes [ADR 0030](0030-the-packages-components-carry-a-prefix.md) for the card
and the modal.

## Decision

The package's card is `<c-card>` and its dialog is `<c-modal>`. Both sit at daisy-cotton's own
paths, `cotton/card/index.html` and `cotton/modal.html`, and replace daisy-cotton's components of
the same name for every caller, daisy-cotton's own templates included. `<c-mvp.card>`,
`<c-mvp.card.wrapper>` and `<c-mvp.modal>` are removed, with no aliases.

Each is built from parts the caller writes:

- `<c-card>` holds `<c-card.header>` (title, icon, badges, actions, and `href` for a card that is
  one link), `<c-card.body>` (`tight` drops its padding) and `<c-card.footer>` (a start group and
  an `end` slot). With no parts the content sits straight on the card's surface. It keeps
  daisy-cotton's styling options: `size`, `border`, `dash`, `side`, `image-full` and the `figure`
  slot.
- `<c-modal>` holds `<c-modal.header>` (title, icon, actions), `<c-modal.body>` and
  `<c-modal.footer>`. It keeps daisy-cotton's `placement`, `closable`, `open`, `content_class` and
  `class`, the package's `size`, and writes its own `<dialog>`, box, close button and backdrop. The
  header's title names the dialog.

`view` on either lays it out by a layout code (django-mvp-layout). The header and footer parts then
take the layout's header and footer places, with `<c-layout.sidebar>` and `<c-layout.page>` between
them. The two headers and the two footers are drawn by one shared pair of rows,
`cotton/mvp/box/header.html` and `cotton/mvp/box/footer.html`.

## Why

Props and named slots on one tag gave the card and the dialog a fixed shape: a title row, a body
and a footer, each switched on by whether a prop or slot was filled. Every new arrangement, such as
a card with sidebars, meant another prop and another branch. Parts the caller declares put the shape
in the caller's markup, where it can be read, and the same parts serve a plain card and one laid out
by a code.

daisy-cotton is meant to be customised by placing a component at its path, above it in
`INSTALLED_APPS`. ADR 0030 kept that for the icon only, because the package's card and modal took
different attributes from daisy-cotton's and a project could not tell from the tag which it got.
Built from parts, the card and the modal keep daisy-cotton's styling options, so its documentation
for those still applies, and there is one card and one dialog in a project rather than two of each.

## Consequences

- A simple card is longer than it was: a title and a line of text is a `<c-card>`, a
  `<c-card.header>` and a `<c-card.body>`. A project that wants the old shorthand writes its own
  wrapper component.
- Every existing `<c-mvp.card>` and `<c-mvp.modal>` call breaks, as do calls to daisy-cotton's
  card or modal that pass `title` or `actions`, which move into the header and footer parts.
- The card and the modal now depend on `mvp` sitting above `daisy_cotton` in `INSTALLED_APPS`, as
  the icon already does. With the order reversed, daisy-cotton's card and modal are drawn and the
  parts have nothing to sit in.
- The prefix rule of ADR 0030 stands for every other component the package owns.
