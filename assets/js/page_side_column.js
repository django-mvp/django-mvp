// Alpine.data("mvpPageSideColumn"), registered in index.js (docs/adr/0035-behaviour-lives-in-registered-alpine-components.md).
// Keeps a sticky side panel taller than the screen moving with the page (docs/adr/0036-a-tall-side-panel-moves-with-the-page.md).
const OFFSET_PROPERTY = "--mvp-page-side-top";

// A panel replaced out of band is a new element; it carries on from the offset the old one held.
const carried = new Map();

function clamp(value, low, high) {
  return Math.min(Math.max(value, low), high);
}

// header_height.js publishes pixels; until it has run the property is the stylesheet's 4rem.
function headerHeight(rem) {
  const value = getComputedStyle(document.documentElement).getPropertyValue("--mvp-header-height").trim();
  return value.endsWith("rem") ? parseFloat(value) * rem : parseFloat(value) || 0;
}

// The state lives in this closure, not on the Alpine object: the aside is nested inside the
// drawer's component, and a name on both would shadow the drawer's.
function pageSideColumn() {
  let aside = null;
  let root = null;
  let active = false;
  let top = 0;
  let low = 0;
  let high = 0;
  let gap = 0;
  let lastScroll = 0;
  let frame = 0;
  let focused = null;

  function release() {
    active = false;
    root.style.removeProperty(OFFSET_PROPERTY);
  }

  function write(value) {
    top = clamp(value, low, high);
    root.style.setProperty(OFFSET_PROPERTY, `${top}px`);
  }

  // Works out the offsets the panel moves between: `high` holds its top a gap under the header,
  // `low` holds its foot at the screen's foot (the root's own bottom padding is the gap there).
  function sync() {
    const sticky = getComputedStyle(root).position === "sticky";
    // A column no longer scrolls, so its aside is a tab stop only where it still does.
    aside.setAttribute("tabindex", sticky ? "-1" : "0");

    gap = parseFloat(getComputedStyle(document.documentElement).fontSize);
    const nextHigh = headerHeight(gap) + gap;
    const height = root.getBoundingClientRect().height;
    if (!sticky || height + nextHigh <= window.innerHeight) {
      release();
      return;
    }

    if (!active) {
      active = true;
      top = carried.get(root.id) ?? root.getBoundingClientRect().top;
      carried.delete(root.id);
      high = nextHigh;
    }
    const shift = nextHigh - high;
    high = nextHigh;
    low = window.innerHeight - height;
    write(top + shift);
  }

  // How far the page's content has scrolled. Measured on the layout rather than as scrollY, so the
  // browser's own scroll to keep the content in place when the header grows does not count.
  function scrolled() {
    return -root.parentElement.getBoundingClientRect().top;
  }

  // The panel moves with the content by what the content moved since the last frame.
  function follow() {
    const now = scrolled();
    if (active) {
      write(top - (now - lastScroll));
    }
    lastScroll = now;
  }

  // The browser scrolls to a focused control as if the panel stayed put, so once it has, the
  // panel moves the rest of the way to put the control clear of the header and the screen's foot.
  function reveal() {
    const control = focused;
    focused = null;
    if (!active || !control?.isConnected) {
      return;
    }
    const box = control.getBoundingClientRect();
    const foot = window.innerHeight - gap;
    if (box.top < high) {
      write(top + high - box.top);
    } else if (box.bottom > foot) {
      write(top + foot - box.bottom);
    }
  }

  function schedule() {
    if (!frame) {
      frame = requestAnimationFrame(() => {
        frame = 0;
        follow();
        reveal();
      });
    }
  }

  function onFocusIn(event) {
    focused = event.target;
    schedule();
  }

  const resizeObserver = new ResizeObserver(sync);
  // header_height.js writes the header's height to :root's style whenever it changes.
  const styleObserver = new MutationObserver(sync);

  return {
    init() {
      aside = this.$el;
      root = aside.closest(".mvp-page-side");
      lastScroll = scrolled();
      window.addEventListener("scroll", schedule, { passive: true });
      window.addEventListener("resize", sync);
      aside.addEventListener("focusin", onFocusIn);
      resizeObserver.observe(root);
      styleObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["style"] });
      sync();
    },

    destroy() {
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", sync);
      aside.removeEventListener("focusin", onFocusIn);
      resizeObserver.disconnect();
      styleObserver.disconnect();
      cancelAnimationFrame(frame);
      if (active && root.id) {
        const id = root.id;
        carried.set(id, top);
        requestAnimationFrame(() => carried.delete(id));
      }
    },
  };
}

export function registerPageSideColumn(Alpine) {
  Alpine.data("mvpPageSideColumn", pageSideColumn);
}
