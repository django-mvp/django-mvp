/*
 * Places the icon rail's tooltips and group fly-outs beside their item.
 *
 * A collapsed rail taller than the window scrolls on its own (#563), and a
 * scroll box clips everything drawn against it, which is where a tooltip or
 * a fly-out used to be drawn. base.css now draws them against the window
 * instead, which takes them out of the clip and also loses the item they were
 * placed by. This module hands each item's position back to the stylesheet as
 * custom properties, whenever the item is pointed at or focused and again
 * whenever the rail scrolls under it.
 *
 * Listeners sit on the document, so the sidebar a boosted navigation swaps in
 * needs nothing rebound.
 */

const RAIL = ".mvp-sidebar--icons";

// An item is a menu row (its fly-out reads the row's top) or anything that
// carries a tooltip (which is centred on it).
const ITEM = "li, [data-tip]";

// The items placed last, so a scroll can move what is showing now.
let placed = [];

function place(item) {
  const rect = item.getBoundingClientRect();
  const rtl = getComputedStyle(item).direction === "rtl";
  // The fly-out opens from the rail's inline end, which in a right-to-left
  // page is measured from the window's right edge.
  const end = rtl ? document.documentElement.clientWidth - rect.left : rect.right;
  item.style.setProperty("--mvp-rail-item-top", `${rect.top}px`);
  item.style.setProperty("--mvp-rail-item-middle", `${rect.top + rect.height / 2}px`);
  item.style.setProperty("--mvp-rail-item-right", `${rect.right}px`);
  item.style.setProperty("--mvp-rail-item-end", `${end}px`);
}

function placeFrom(target) {
  const rail = target instanceof Element ? target.closest(RAIL) : null;
  if (!rail) {
    return;
  }
  placed = [];
  for (let item = target.closest(ITEM); item && rail.contains(item); ) {
    place(item);
    placed.push(item);
    item = item.parentElement.closest(ITEM);
  }
}

export function startRail() {
  document.addEventListener("pointerover", (event) => placeFrom(event.target));
  document.addEventListener("focusin", (event) => placeFrom(event.target));
  // Scroll does not bubble; listening in the capture phase hears the rail's.
  document.addEventListener(
    "scroll",
    (event) => {
      if (event.target instanceof Element && event.target.matches(RAIL)) {
        placed.filter((item) => item.isConnected).forEach(place);
      }
    },
    { capture: true, passive: true },
  );
}
