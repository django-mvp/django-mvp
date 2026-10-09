// The theme-color tag follows the applied theme (#516). Only a script that
// runs after the stylesheet can read a theme's colours, so the server's
// value stays in the tag until this has run.

const TAG_SELECTOR = 'meta[name="theme-color"]';
const HEADER_SELECTOR = ".mvp-header";

// Made on the first reading, so a page with the feature off makes none.
let pixel = null;

// Painted and read back, because a computed colour keeps the notation its
// theme was written in and a browser may not read that from the tag.
function paintedColour(colour) {
  pixel ??= document.createElement("canvas").getContext("2d", {
    willReadFrequently: true,
  });
  pixel.clearRect(0, 0, 1, 1);
  pixel.fillStyle = colour;
  pixel.fillRect(0, 0, 1, 1);
  const [red, green, blue, alpha] = pixel.getImageData(0, 0, 1, 1).data;
  if (alpha < 255) {
    return null;
  }
  const hex = (channel) => channel.toString(16).padStart(2, "0");
  return `#${hex(red)}${hex(green)}${hex(blue)}`;
}

// A see-through header shows whatever is behind it, and a page with no
// header (the entrance page, the error pages) puts its body under the toolbar.
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

export function startThemeColor() {
  const tag = document.querySelector(TAG_SELECTOR);
  if (!tag) {
    return;
  }
  const sync = () => {
    const colour = colourUnderTheToolbar();
    if (colour) {
      tag.setAttribute("content", colour);
    }
  };
  sync();
  // The attribute, not the theme controls: a theme applied by a project's
  // own script recolours the header just the same.
  new MutationObserver(sync).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme"],
  });
}
