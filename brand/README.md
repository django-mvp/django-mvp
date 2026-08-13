# Brand assets

The DjangoMVP mark, in the placements the application does not serve itself.

Everything here is a master. There is exactly one copy of each asset in this repository, so
nothing in this directory duplicates anything under `mvp/static/brand/`.

## What is here

| File | What it is for |
| --- | --- |
| `django-mvp-logo-stacked.svg` | Mark above wordmark. A column too narrow for the inline lockup: a sidebar, a centred header, a splash |
| `django-mvp-avatar.svg` | The mark on a solid 512 square. The GitHub organisation image |
| `django-mvp-avatar-inline.svg` | The inline lockup on the square. Wide profile slots and cards |
| `django-mvp-avatar-stacked.svg` | The stacked lockup on the square. Square slots only ever seen large |

Each has a `-dark` counterpart.

## What is not here

The inline lockup and the compact mark are served by the application through the `logo_url` and
`icon_url` template tags, so they live where those resolvers look for them:

| Asset | Path |
| --- | --- |
| Inline lockup, light and dark | `mvp/static/brand/logo.svg`, `logo_dark.svg` |
| Mark, light and dark | `mvp/static/brand/icon.svg`, `icon_dark.svg` |

Only `mvp/` ships in the wheel, so this directory is version-controlled and not distributed.

## Using them

**The mark is uncontained.** No tile, circle, badge or border anywhere it sits inside a page. The
avatar files are the exception and they exist for one reason: a profile slot is a fixed square that
gets filled with something whatever we do, so those carry their own background and padding. Placing
an avatar file inline in a document is how that rule gets broken by accident.

**Use the plain avatar for a profile picture.** A profile image is shown at 20 to 60px far more
often than at full size, and at those sizes the stacked wordmark is an unreadable smudge while the
mark alone stays sharp. The plain avatar also survives a circular crop. The inline and stacked
avatars do not, and are for square slots.

**Which lockup.** The inline lockup is the default. Below about 96px wide, use the stacked one;
below 16px for the mark, there is nothing left to use.

**Clear space** is the height of the navbar block in the mark, one quarter of the mark's height, on
every side. Nothing enters it.

**Colour.** Chrome (the navbar and rail blocks) is `#171F1D` on light and `#ECE9E3` on dark. The
content region is `#375B78` on light and `#7FA6C2` on dark. Where a reproduction genuinely cannot
carry two colours, set both regions to the chrome colour rather than inventing a value.

**Nothing else.** No recolouring, no rearrangement, no gradient, shadow, outline or rotation, and no
arrangement that is not one of the supplied files. The wordmark is outlines rather than live text:
it needs no font installed, and re-setting it in a font would differ in kerning from every asset
already in circulation.

## Rasters

None are supplied. Every consumer of these files rasterises from the vector, and a PNG set is a
second copy that goes stale the first time the mark is touched. A platform that demands a PNG takes
one exported from the SVG at the size it asks for.
