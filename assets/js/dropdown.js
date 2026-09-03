/*
 * Smart placement for the dropdown component.
 *
 * daisyUI positions a dropdown entirely in CSS, so where a panel opens is
 * decided when the template is written rather than when the page is drawn.
 * That is fine for the five dropdowns this package ships, which all live in
 * the top-right corner and all say so. It is wrong everywhere else: the same
 * component in a table row or near the foot of a page opens off the edge of
 * the viewport, and even a correctly placed panel is cut off by a scrolling
 * ancestor or painted under the sticky navbar, because it renders in normal
 * flow like any other element.
 *
 * This module upgrades each dropdown once the page is live. The panel is
 * promoted into the top layer with the Popover API, which is what takes it out
 * of reach of an ancestor's `overflow: hidden` and out of the z-index contest
 * altogether, and Floating UI then measures the space actually available and
 * puts it where it fits.
 *
 * The upgrade is deliberately not baked into the template. Writing `popover`
 * into the markup would hide the panel outright wherever this script does not
 * run — no JavaScript, an older browser, a bundle that failed to load — and
 * turn an enhancement into a hard dependency. Marked up as it is, a page that
 * never gets this far still opens its dropdowns the way daisyUI always has.
 *
 * `flip()` and not `autoPlacement()`, which Floating UI documents as mutually
 * exclusive. The two want opposite things: `flip()` keeps the placement the
 * author declared unless there is genuinely no room for it, `autoPlacement()`
 * always takes whichever side has the most space. Only the first leaves
 * `halign`/`valign` meaning anything, and the second would have a dropdown
 * opening upwards and downwards by turns as the page scrolled under it.
 */

import {
  autoUpdate,
  computePosition,
  flip,
  offset,
  shift,
  size,
} from "@floating-ui/dom";

// The gap between the trigger and the panel. daisyUI leaves them touching and
// consumers add a margin utility when they want air, but a margin on an
// element the browser is positioning itself fights the position, so the gap
// belongs in the placement calculation instead.
const GAP = 8;

// How close a panel may come to the edge of the viewport before shift() pulls
// it back and size() starts capping its height.
const VIEWPORT_PADDING = 8;

// The placements the component's halign/valign pairs resolve to. An unknown
// value reaches Floating UI as an unknown side, which it does not reject — it
// just returns coordinates that put the panel on top of its own trigger. Today
// a bogus valign drops the daisyUI class and leaves the panel at daisyUI's own
// default, so the fallback below is what keeps that behaviour rather than
// trading a mildly wrong dropdown for a visibly broken one.
const PLACEMENTS = [
  "top",
  "top-start",
  "top-end",
  "bottom",
  "bottom-start",
  "bottom-end",
  "left",
  "left-start",
  "left-end",
  "right",
  "right-start",
  "right-end",
];

const DEFAULT_PLACEMENT = "bottom-start";

// Every autoUpdate loop currently running. A panel that is open when a boosted
// navigation replaces the body is removed from the document while showing, and
// the specification closes it *without* firing `toggle` — so the per-panel
// teardown below never runs, and that panel's scroll and resize listeners
// would outlive the markup they were tracking. Clicking a link inside an open
// dropdown is the ordinary way to leave a page, so this is the common case
// rather than a corner of one.
const tracking = new Set();

function upgrade(wrapper) {
  const panel = wrapper.querySelector(":scope > .dropdown-content");
  const trigger = wrapper.firstElementChild;

  if (!panel || !trigger || trigger === panel) {
    return;
  }

  const declared = wrapper.dataset.mvpPlacement;
  const placement = PLACEMENTS.includes(declared) ? declared : DEFAULT_PLACEMENT;

  // `full` means "as wide as the trigger", which the template says with
  // `w-full`. That worked while the panel was a child of the trigger's box.
  // In the top layer it is not, and `w-full` would resolve against the
  // viewport, so the width has to be measured and applied instead.
  const matchTriggerWidth = panel.classList.contains("w-full");

  panel.setAttribute("popover", "auto");

  const position = () =>
    computePosition(trigger, panel, {
      placement,
      strategy: "fixed",
      middleware: [
        offset(GAP),
        flip({ padding: VIEWPORT_PADDING }),
        shift({ padding: VIEWPORT_PADDING }),
        size({
          padding: VIEWPORT_PADDING,
          apply({ rects, availableHeight, elements }) {
            if (matchTriggerWidth) {
              elements.floating.style.width = `${rects.reference.width}px`;
            }
            // A panel taller than the room below it used to run off the
            // bottom of the page. The top layer does not scroll with the
            // document, so capping it here and letting it scroll internally
            // is the only way the last item stays reachable.
            elements.floating.style.maxHeight = `${availableHeight}px`;
          },
        }),
      ],
    }).then(({ x, y }) => {
      Object.assign(panel.style, { left: `${x}px`, top: `${y}px` });
    });

  let stop = null;

  panel.addEventListener("toggle", (event) => {
    if (event.newState === "open") {
      // autoUpdate re-runs the calculation while the panel is open: the page
      // scrolls, the window resizes, the trigger moves. It costs a set of
      // listeners and two observers per panel, which is why it is started
      // here and not once at upgrade time.
      stop = autoUpdate(trigger, panel, position);
      tracking.add(stop);
      return;
    }

    if (stop) {
      tracking.delete(stop);
      stop();
      stop = null;
    }
  });

  // The browser dismisses an open popover on pointerdown anywhere outside it,
  // and the trigger is outside it. A click handler that read the state after
  // that had happened would find the panel closed and open it straight back
  // up, so the trigger could never close what it opened. Reading the state as
  // the pointer goes down, before dismissal runs, is what tells the two apart.
  // Keyboard activation fires click with no pointerdown ahead of it, so the
  // live state is consulted as well rather than instead.
  let openAtPointerDown = false;

  trigger.addEventListener("pointerdown", () => {
    openAtPointerDown = panel.matches(":popover-open");
  });

  trigger.addEventListener("click", () => {
    const open = openAtPointerDown || panel.matches(":popover-open");
    openAtPointerDown = false;

    if (open) {
      panel.hidePopover();
    } else {
      panel.showPopover();
    }
  });

  if (wrapper.classList.contains("dropdown-hover")) {
    // The panel draws in the top layer but stays a descendant of the wrapper
    // in the DOM, so pointer traffic over the panel still reads as inside the
    // wrapper. That is what lets a single pair of listeners on the wrapper
    // cover the trigger and the panel both, and it is why moving the pointer
    // from one to the other does not close the dropdown on the way.
    wrapper.addEventListener("mouseenter", () => panel.showPopover());
    wrapper.addEventListener("mouseleave", () => panel.hidePopover());
  }
}

export function startDropdowns() {
  // Everything here is built on the Popover API. Where it is missing there is
  // nothing to enhance and nothing to repair: the markup is untouched daisyUI
  // and already works.
  if (!HTMLElement.prototype.showPopover) {
    return;
  }

  tracking.forEach((stop) => stop());
  tracking.clear();

  document.querySelectorAll("[data-mvp-dropdown]").forEach(upgrade);
}
