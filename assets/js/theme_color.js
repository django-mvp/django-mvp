/*
 * The browser toolbar colour follows the applied theme.
 *
 * An installed app, and a mobile browser, colour the toolbar around the page
 * from the theme-color tag. The server writes that tag from
 * MVP_CONFIG["pwa"]["theme_color"], one colour, and a project with a light
 * and a dark theme has two: a visitor on the dark theme got a light toolbar
 * over a dark page.
 *
 * The toolbar sits against the application header, so the tag takes the
 * header's colour. That can only be read here. The inline script in
 * base.html that applies the theme runs before the stylesheet has loaded,
 * and a theme is CSS the server never reads. The configured colour stays in
 * the tag until this has run, and for good where it never does.
 *
 * A page with the feature off has no tag and nothing here does anything.
 */

const TAG_SELECTOR = 'meta[name="theme-color"]';
const HEADER_SELECTOR = ".mvp-header";

// One pixel, painted and read back. A theme may state its colours in any
// notation CSS has, and the computed value keeps that notation; a browser
// that reads the tag is only sure to understand the plain ones.
// Made on the first reading, so a page with the feature off makes none.
let pixel = null;

function paintedColour(colour) {
  pixel.clearRect(0, 0, 1, 1);
  pixel.fillStyle = colour;
  pixel.fillRect(0, 0, 1, 1);
  const [red, green, blue, alpha] = pixel.getImageData(0, 0, 1, 1).data;
  // A see-through background is not what the toolbar sits against: whatever
  // is behind it is.
  if (alpha < 255) {
    return null;
  }
  const hex = (channel) => channel.toString(16).padStart(2, "0");
  return `#${hex(red)}${hex(green)}${hex(blue)}`;
}

// The header's colour, or the colour of the nearest thing behind it that has
// one. A page with no header (the entrance page, the error pages) starts at
// the body, which is what its toolbar sits against.
function colourUnderTheToolbar() {
  let element = document.querySelector(HEADER_SELECTOR) ?? document.body;
  for (; element; element = element.parentElement) {
    const colour = paintedColour(getComputedStyle(element).backgroundColor);
    if (colour) {
      return colour;
    }
  }
  return null;
}

export function syncThemeColor() {
  const tag = document.querySelector(TAG_SELECTOR);
  if (!tag) {
    return;
  }
  pixel ??= document.createElement("canvas").getContext("2d", {
    willReadFrequently: true,
  });
  const colour = colourUnderTheToolbar();
  if (colour) {
    tag.setAttribute("content", colour);
  }
}

export function startThemeColor() {
  if (!document.querySelector(TAG_SELECTOR)) {
    return;
  }
  // The bundle is deferred, so the packaged stylesheet has applied by now. A
  // project stylesheet that arrives later can still recolour the header,
  // which is what the second reading is for.
  syncThemeColor();
  window.addEventListener("load", syncThemeColor);

  // Watches the attribute rather than the theme controls: a theme applied by
  // a project's own script changes the header just the same.
  new MutationObserver(syncThemeColor).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme"],
  });
}
