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

// daisyUI leaves trigger and panel touching; a margin utility would fight
// the browser's own positioning, so the gap belongs in the calculation.
const GAP = 8;

// How close a panel may come to the edge of the viewport before shift() pulls
// it back and size() starts capping its height.
const VIEWPORT_PADDING = 8;

// Floating UI does not reject an unknown side — it stacks the panel on its
// own trigger. The fallback below keeps today's behaviour (a bogus valign
// drops the daisyUI class, panel stays at daisyUI's default) instead.
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

// Every autoUpdate loop currently running. A panel open when a boosted
// navigation replaces the body is removed without firing `toggle`, so its
// teardown never runs and its listeners would outlive the markup.
const tracking = new Set();

function upgrade(wrapper) {
  const panel = wrapper.querySelector(":scope > .dropdown-content");
  const trigger = wrapper.firstElementChild;

  if (!panel || !trigger || trigger === panel) {
    return;
  }

  const declared = wrapper.dataset.mvpPlacement;
  const placement = PLACEMENTS.includes(declared) ? declared : DEFAULT_PLACEMENT;

  // `w-full` worked while the panel was a child of the trigger's box; in the
  // top layer it would resolve against the viewport instead, so it has to
  // be measured and applied manually.
  const matchTriggerWidth = panel.classList.contains("w-full");

  panel.setAttribute("popover", "auto");

  // Open/closed state stops being inferrable from focus once the script
  // takes the panel over (daisyUI opens on `:focus-within`), so a popover
  // toggled from script needs its own ARIA.
  //
  // Set here and not in the template: without this script running, adding
  // it there would report "closed" on a hover/focus-opened panel — worse
  // than reporting nothing.
  trigger.setAttribute("aria-expanded", "false");

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
            // The top layer does not scroll with the document, so capping
            // height here and scrolling internally keeps the last item
            // reachable instead of letting it run off the page.
            elements.floating.style.maxHeight = `${availableHeight}px`;
          },
        }),
      ],
    }).then(({ x, y }) => {
      Object.assign(panel.style, { left: `${x}px`, top: `${y}px` });
    });

  let stop = null;

  panel.addEventListener("toggle", (event) => {
    trigger.setAttribute("aria-expanded", String(event.newState === "open"));

    if (event.newState === "open") {
      // Costs a set of listeners and two observers per panel, so started
      // here rather than once at upgrade time.
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

  // Reading state at click would always find the popover already dismissed
  // by the browser's own pointerdown handling. Live state is also checked,
  // for keyboard activation, which fires click with no pointerdown first.
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
    // The panel stays a DOM descendant of the wrapper despite drawing in the
    // top layer, so one listener pair here covers trigger and panel, and
    // moving between them does not close the dropdown on the way.
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
