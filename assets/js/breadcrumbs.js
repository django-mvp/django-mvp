// Alpine.data("mvpBreadcrumbs"), registered in index.js.
//
// A breadcrumb trail that fits the width of its own container, not the window.
// The server renders every crumb, so without this script the trail is a plain
// list that shrinks and ellipsises (base.css). With it, the trail is measured
// once and then laid out by arithmetic on every resize: the first of these
// layouts that fits is the one shown.
//
//   1. every crumb
//   2. crumbs folded into a "…" menu from the middle outwards, keeping the
//      first step, the parent and the current page
//   3. the first step shrunk to its icon, when it has one
//   4. the first step folded as well: menu, parent, current page
//   5. the parent cut short to a few words, and the current page's name too
//   6. menu and current page only
//
// This follows the published practice: show the whole path where there is room
// (NN/g), collapse the middle behind an ellipsis that expands (MUI, Atlassian),
// keep the parent as the one step up on a phone (NN/g, GOV.UK), and measure the
// container rather than the viewport (Fluent UI, Primer), because the same
// trail sits in a full-width header, a sidebar or a card.
import { upgradeDropdown } from "./dropdown.js";

const CURRENT_REM = 16; // what the current page keeps before ancestors fold away
const TIGHT_REM = 7; // the parent's width once it is cut short
const LAST_REM = 8; // what the current page keeps before the parent folds too

function rem(n) {
  return n * parseFloat(getComputedStyle(document.documentElement).fontSize);
}

function outerWidth(element) {
  const style = getComputedStyle(element);
  return (
    element.getBoundingClientRect().width +
    parseFloat(style.marginLeft) +
    parseFloat(style.marginRight)
  );
}

function separatorWidth(li) {
  const before = getComputedStyle(li, "::before");
  if (before.content === "none" || before.display === "none") {
    return 0;
  }
  return (
    parseFloat(before.width) +
    parseFloat(before.marginLeft) +
    parseFloat(before.marginRight) +
    parseFloat(before.paddingLeft) +
    parseFloat(before.paddingRight)
  );
}

function crumbText(li) {
  const text = li.querySelector(".mvp-crumb-text") || li.querySelector("a, span");
  return (text ? text.textContent : li.textContent).trim();
}

export function registerBreadcrumbs(Alpine) {
  Alpine.data("mvpBreadcrumbs", () => ({
    crumbs: [],
    fold: null,
    widths: null,
    frame: 0,

    init() {
      const list = this.$el.querySelector(":scope > ol");
      this.fold = list.querySelector("[data-mvp-crumbs-fold]");
      this.crumbs = Array.from(list.children).filter((li) => li !== this.fold);
      this.number();
      if (this.crumbs.length < 2) {
        return;
      }

      this.$el.classList.add("is-enhanced");
      const dropdown = this.fold.querySelector("[data-mvp-dropdown]");
      upgradeDropdown(dropdown);
      const panel = dropdown.querySelector(".dropdown-content");
      panel.addEventListener("toggle", (event) => {
        if (event.newState === "open") {
          const first = panel.querySelector("a");
          if (first) {
            first.focus({ preventScroll: true });
          }
        }
      });

      this.measure();
      this.observer = new ResizeObserver(() => this.schedule());
      this.observer.observe(this.$el);
      // Web fonts change every width measured so far.
      if (document.fonts && document.fonts.status !== "loaded") {
        document.fonts.ready.then(() => {
          this.measure();
        });
      }
    },

    destroy() {
      if (this.observer) {
        this.observer.disconnect();
      }
      cancelAnimationFrame(this.frame);
    },

    schedule() {
      cancelAnimationFrame(this.frame);
      this.frame = requestAnimationFrame(() => this.layout());
    },

    // The schema.org position of every step, whether it came from the items
    // list or from steps written in a template.
    number() {
      this.crumbs.forEach((li, index) => {
        let meta = li.querySelector(':scope > meta[itemprop="position"]');
        if (!meta) {
          meta = document.createElement("meta");
          meta.setAttribute("itemprop", "position");
          li.append(meta);
        }
        meta.content = String(index + 1);
      });
    },

    // Every crumb's natural width, read in one pass with everything shown.
    measure() {
      const nav = this.$el;
      const root = this.crumbs[0];
      const parent = this.crumbs[this.crumbs.length - 2];

      nav.classList.add("is-measuring");
      this.applied = null;
      this.fold.hidden = false;
      this.fold.parentElement.insertBefore(this.fold, this.fold.parentElement.firstChild);
      this.crumbs.forEach((li) => {
        li.hidden = false;
        li.classList.remove("is-compact", "is-tight");
      });

      const separator = separatorWidth(this.crumbs[0]);
      const full = this.crumbs.map(outerWidth);
      const foldWidth = outerWidth(this.fold);

      let compact = null;
      if (root.querySelector(".mvp-crumb-icon")) {
        root.classList.add("is-compact");
        compact = outerWidth(root);
        root.classList.remove("is-compact");
      }
      parent.classList.add("is-tight");
      const tight = outerWidth(parent);
      parent.classList.remove("is-tight");

      nav.classList.remove("is-measuring");
      this.widths = { separator, full, foldWidth, compact, tight };
      this.layout();
    },

    // The layouts from widest to narrowest, as what each hides and shrinks.
    stages() {
      const n = this.crumbs.length;
      const range = (from, to) => {
        const set = new Set();
        for (let i = from; i <= to; i += 1) {
          set.add(i);
        }
        return set;
      };
      const stages = [{ hidden: new Set() }];
      for (let k = 1; k <= n - 3; k += 1) {
        stages.push({ hidden: range(1, k) });
      }
      if (this.widths.compact !== null && n >= 2) {
        stages.push({ hidden: range(1, n - 3), compact: true });
      }
      if (n >= 3) {
        stages.push({ hidden: range(0, n - 3) });
      }
      stages.push({ hidden: n >= 3 ? range(0, n - 3) : new Set(), tight: true });
      stages.push({ hidden: range(0, n - 2) });
      return stages;
    },

    widthOf(stage) {
      const { separator, full, foldWidth, compact, tight } = this.widths;
      const n = this.crumbs.length;
      const current = n - 1;
      let total = 0;
      let first = true;

      if (stage.hidden.size) {
        total += foldWidth;
        first = false;
      }
      for (let i = 0; i < n; i += 1) {
        if (stage.hidden.has(i)) {
          continue;
        }
        let width = full[i];
        if (i === 0 && stage.compact) {
          width = compact;
        }
        if (i === n - 2 && stage.tight) {
          width = Math.min(width, tight);
        }
        if (i === current) {
          const keep = stage.tight ? LAST_REM : CURRENT_REM;
          width = Math.min(width, rem(keep) + separator);
        }
        // Widths were read with the fold leading, so every crumb carried a
        // separator; whichever is drawn first in this layout has none.
        if (first) {
          width -= separator;
          first = false;
        }
        total += width;
      }
      return total;
    },

    layout() {
      if (!this.widths) {
        return;
      }
      const available = this.$el.clientWidth;
      const stages = this.stages();
      const chosen =
        stages.find((stage) => this.widthOf(stage) <= available + 0.5) ||
        stages[stages.length - 1];
      this.apply(chosen);
    },

    apply(stage) {
      const n = this.crumbs.length;
      const key = `${[...stage.hidden].join(",")}|${stage.compact ? 1 : 0}|${stage.tight ? 1 : 0}`;
      if (key === this.applied) {
        this.markTruncated();
        return;
      }
      this.applied = key;

      this.crumbs.forEach((li, i) => {
        li.hidden = stage.hidden.has(i);
      });
      this.crumbs[0].classList.toggle("is-compact", Boolean(stage.compact));
      this.crumbs[n - 2].classList.toggle("is-tight", Boolean(stage.tight));

      const hidden = [...stage.hidden].sort((a, b) => a - b);
      if (!hidden.length) {
        this.fold.hidden = true;
      } else {
        this.fold.hidden = false;
        const after = this.crumbs[hidden[hidden.length - 1] + 1];
        after.parentElement.insertBefore(this.fold, after);
        this.fillMenu(hidden);
      }
      this.$el.dataset.folded = String(hidden.length);
      this.$dispatch("mvp-breadcrumbs-layout", { folded: hidden.length, total: n });
      this.markTruncated();
    },

    fillMenu(hidden) {
      const menu = this.fold.querySelector("[data-mvp-crumbs-menu]");
      const button = this.fold.querySelector("[data-mvp-crumbs-fold-button]");
      const { labelOne, labelMany } = this.$el.dataset;
      button.setAttribute(
        "aria-label",
        hidden.length === 1
          ? labelOne
          : labelMany.replace("{count}", String(hidden.length)),
      );
      button.title = hidden.map((i) => crumbText(this.crumbs[i])).join(" › ");

      // Each folded step's own link, icon and label, copied rather than rebuilt.
      menu.replaceChildren(
        ...hidden.map((i) => {
          const target = this.crumbs[i].firstElementChild.cloneNode(true);
          target.removeAttribute("title");
          target.removeAttribute("itemprop");
          target.querySelectorAll("[itemprop]").forEach((node) => {
            node.removeAttribute("itemprop");
          });
          const item = document.createElement("li");
          item.append(target);
          return item;
        }),
      );
    },

    // A crumb that had to be cut short says what it is on hover.
    markTruncated() {
      this.crumbs.forEach((li) => {
        const text = li.querySelector(".mvp-crumb-text") || li.querySelector("a, span");
        if (!text || li.hidden) {
          return;
        }
        const target = li.querySelector("a, span[aria-current]") || text;
        if (text.scrollWidth > text.clientWidth + 1 || li.classList.contains("is-compact")) {
          target.title = crumbText(li);
        } else {
          target.removeAttribute("title");
        }
      });
    },
  }));
}
