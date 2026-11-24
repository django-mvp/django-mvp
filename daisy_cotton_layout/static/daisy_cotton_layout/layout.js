/*
 * The behaviour of <c-layout>: sidebar toggles, drawers, remembered state.
 *
 * Load it in the head, without defer. Each layout mounts itself from a script
 * right after its markup, so its sidebars and toggles are settled before the
 * first paint. Layouts added later (htmx, a modal's content) mount the same
 * way, and a MutationObserver catches any that arrive without running scripts.
 *
 * Whether a sidebar is beside the page or a drawer over it is decided by the
 * stylesheet, from the layout's own width (container queries). The script
 * reads that decision from the sidebar's --dcl-mode and never makes it.
 */
(function () {
  "use strict";
  if (window.DaisyCottonLayout) return;

  var ROOT = "[data-dcl]";
  var FOCUSABLE =
    'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
  var observers = new WeakMap();
  var openers = new WeakMap();
  var stack = [];

  function grid(root) {
    return root.querySelector(":scope > .dcl-grid");
  }
  function sidebars(root) {
    var g = grid(root);
    return g ? Array.prototype.slice.call(g.querySelectorAll(":scope > .dcl-sidebar")) : [];
  }
  function sidebar(root, side) {
    var g = grid(root);
    return g ? g.querySelector(':scope > .dcl-sidebar[data-side="' + side + '"]') : null;
  }
  function panel(sb) {
    return sb.querySelector(":scope > .dcl-panel");
  }
  function ownRoot(el) {
    var id = el.getAttribute("data-dcl-layout");
    return id ? document.getElementById(id) : el.closest(ROOT);
  }
  function mode(sb) {
    return getComputedStyle(sb).getPropertyValue("--dcl-mode").trim() || "docked";
  }
  function isVisible(sb) {
    if (!sb) return false;
    if (mode(sb) === "overlay") return sb.getAttribute("data-overlay") === "open";
    return sb.getAttribute("data-state") === "open" || sb.getAttribute("data-collapse") === "none";
  }
  function canToggle(sb) {
    return !!sb && !(mode(sb) === "docked" && sb.getAttribute("data-collapse") === "none");
  }

  function state(root) {
    var out = {};
    ["left", "right"].forEach(function (side) {
      var sb = sidebar(root, side);
      out[side] = sb
        ? {
            present: true,
            mode: mode(sb),
            state: sb.getAttribute("data-state"),
            collapse: sb.getAttribute("data-collapse"),
            rail: sb.hasAttribute("data-dcl-rail"),
            visible: isVisible(sb),
          }
        : { present: false };
    });
    return out;
  }

  // Everything a toggle, or an element shown only in one state, needs to know
  // about its own layout, and nothing about a layout nested inside it.
  function controls(root) {
    return Array.prototype.slice
      .call(document.querySelectorAll("[data-dcl-toggle], [data-dcl-when]"))
      .filter(function (el) {
        return ownRoot(el) === root;
      });
  }

  function measure(root) {
    var g = grid(root);
    if (!g) return;
    var header = g.querySelector(":scope > .dcl-header");
    var footer = g.querySelector(":scope > .dcl-footer");
    root.style.setProperty("--dcl-header-h", (header ? header.offsetHeight : 0) + "px");
    root.style.setProperty("--dcl-footer-h", (footer ? footer.offsetHeight : 0) + "px");
  }

  function lockPage() {
    var locked = !!document.querySelector(
      '.dcl:not([data-dcl-container]) > .dcl-grid > .dcl-sidebar[data-overlay="open"]'
    );
    document.documentElement.classList.toggle("dcl-locked", locked);
    document.documentElement.style.overflow = locked ? "hidden" : "";
  }

  function sync(root) {
    if (!root || !root.isConnected) return;
    sidebars(root).forEach(function (sb) {
      var now = mode(sb);
      var before = sb.getAttribute("data-mode");
      if (before && before !== now && sb.getAttribute("data-overlay") === "open") {
        closeOverlay(sb, false);
      }
      sb.setAttribute("data-mode", now);
      sb.toggleAttribute(
        "data-dcl-rail",
        now === "docked" && sb.getAttribute("data-state") === "closed" && sb.getAttribute("data-collapse") === "icons"
      );
    });
    controls(root).forEach(function (el) {
      if (el.hasAttribute("data-dcl-toggle")) {
        var sb = sidebar(root, el.getAttribute("data-dcl-toggle"));
        var when = el.getAttribute("data-dcl-when");
        var show = canToggle(sb);
        if (show && when === "closed") show = !isVisible(sb);
        if (show && when === "open") show = isVisible(sb);
        el.hidden = !show;
        if (sb) {
          el.setAttribute("aria-controls", sb.id);
          el.setAttribute("aria-expanded", String(isVisible(sb)));
        }
      } else {
        var parts = (el.getAttribute("data-dcl-when") || "").split("-");
        var target = sidebar(root, parts[0]);
        var visible = isVisible(target);
        el.hidden = !(target && (parts[1] === "closed" ? !visible : visible));
      }
    });
    measure(root);
    lockPage();
    root.dispatchEvent(new CustomEvent("dcl:change", { bubbles: true, detail: state(root) }));
  }

  function openOverlay(sb, opener) {
    var root = ownRoot(sb);
    var p = panel(sb);
    sb.setAttribute("data-overlay", "open");
    openers.set(sb, opener || document.activeElement);
    // What the backdrop covers can't be reached while the drawer is open.
    Array.prototype.forEach.call(grid(root).children, function (child) {
      if (child !== sb && !child.inert) {
        child.inert = true;
        child.setAttribute("data-dcl-inerted", "");
      }
    });
    p.setAttribute("role", "dialog");
    p.setAttribute("aria-modal", "true");
    if (sb.getAttribute("aria-label")) p.setAttribute("aria-label", sb.getAttribute("aria-label"));
    if (!p.hasAttribute("tabindex")) p.setAttribute("tabindex", "-1");
    stack.push(sb);
    var first = Array.prototype.find.call(p.querySelectorAll(FOCUSABLE), function (el) {
      return el.checkVisibility ? el.checkVisibility() : true;
    });
    (first || p).focus({ preventScroll: true });
  }

  function closeOverlay(sb, returnFocus) {
    if (sb.getAttribute("data-overlay") !== "open") return;
    var root = ownRoot(sb);
    var p = panel(sb);
    sb.removeAttribute("data-overlay");
    if (root) {
      Array.prototype.forEach.call(grid(root).querySelectorAll(":scope > [data-dcl-inerted]"), function (child) {
        child.inert = false;
        child.removeAttribute("data-dcl-inerted");
      });
    }
    p.removeAttribute("role");
    p.removeAttribute("aria-modal");
    stack = stack.filter(function (other) {
      return other !== sb;
    });
    var opener = openers.get(sb);
    openers.delete(sb);
    if (returnFocus && opener && opener.isConnected) opener.focus({ preventScroll: true });
  }

  function remember(sb) {
    var name = sb.getAttribute("data-persist");
    if (!name) return;
    document.cookie =
      "dcl-" + name + "=" + sb.getAttribute("data-state") + "; path=/; max-age=31536000; samesite=lax";
  }

  function toggle(root, side, opener) {
    var sb = sidebar(root, side);
    if (!canToggle(sb)) return;
    if (mode(sb) === "overlay") {
      if (sb.getAttribute("data-overlay") === "open") closeOverlay(sb, true);
      else openOverlay(sb, opener);
    } else {
      sb.setAttribute("data-state", sb.getAttribute("data-state") === "open" ? "closed" : "open");
      remember(sb);
    }
    sync(root);
  }

  function resolve(rootOrId) {
    return typeof rootOrId === "string" ? document.getElementById(rootOrId) : rootOrId;
  }

  function mount(root) {
    if (!root) return;
    if (!observers.has(root)) {
      var observer = new ResizeObserver(function () {
        sync(root);
      });
      observer.observe(root);
      var g = grid(root);
      if (g) {
        Array.prototype.forEach.call(g.querySelectorAll(":scope > .dcl-header, :scope > .dcl-footer"), function (el) {
          observer.observe(el);
        });
      }
      observers.set(root, observer);
    }
    sync(root);
  }

  document.addEventListener("click", function (event) {
    var target = event.target instanceof Element ? event.target : null;
    if (!target) return;
    var button = target.closest("[data-dcl-toggle]");
    if (button) {
      var root = ownRoot(button);
      if (root) toggle(root, button.getAttribute("data-dcl-toggle"), button);
      return;
    }
    var closer = target.closest("[data-dcl-close]");
    if (closer) {
      var sb = closer.closest(".dcl-sidebar");
      if (sb) {
        closeOverlay(sb, true);
        sync(ownRoot(sb));
      }
      return;
    }
    // Following a link from a drawer closes it, as leaving the page would.
    var link = target.closest("a[href]");
    var drawer = link && link.closest('.dcl-sidebar[data-overlay="open"]');
    if (drawer && !event.defaultPrevented) {
      closeOverlay(drawer, false);
      sync(ownRoot(drawer));
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape" || !stack.length) return;
    var sb = stack[stack.length - 1];
    closeOverlay(sb, true);
    sync(ownRoot(sb));
    // Escape closes the drawer and nothing else, such as a dialog around it.
    event.preventDefault();
    event.stopPropagation();
  });

  // The header of a layout that has been scrolled gets a line under it.
  document.addEventListener(
    "scroll",
    function (event) {
      var target = event.target;
      if (target === document) {
        document.querySelectorAll(".dcl:not([data-dcl-container])").forEach(function (root) {
          root.toggleAttribute("data-dcl-scrolled", window.scrollY > 0);
        });
      } else if (target instanceof Element && target.matches(".dcl[data-dcl-container] > .dcl-grid")) {
        target.parentElement.toggleAttribute("data-dcl-scrolled", target.scrollTop > 0);
      }
    },
    { capture: true, passive: true }
  );

  new MutationObserver(function (records) {
    records.forEach(function (record) {
      record.addedNodes.forEach(function (node) {
        if (!(node instanceof Element)) return;
        if (node.matches(ROOT)) mount(node);
        node.querySelectorAll(ROOT).forEach(mount);
        // A control outside its layout, such as a dock after the shell.
        var outside = node.matches("[data-dcl-layout]") ? [node] : [];
        node.querySelectorAll("[data-dcl-layout]").forEach(function (el) {
          outside.push(el);
        });
        outside.forEach(function (el) {
          var root = ownRoot(el);
          if (root && observers.has(root)) sync(root);
        });
      });
    });
    stack = stack.filter(function (sb) {
      return sb.isConnected;
    });
    lockPage();
  }).observe(document.documentElement, { childList: true, subtree: true });

  window.DaisyCottonLayout = {
    mount: mount,
    sync: sync,
    state: state,
    toggle: function (rootOrId, side) {
      var root = resolve(rootOrId);
      if (root) toggle(root, side, document.activeElement);
    },
    // Show a sidebar, whatever its mode: opens the drawer, or the docked sidebar.
    open: function (rootOrId, side) {
      var root = resolve(rootOrId);
      var sb = root && sidebar(root, side);
      if (sb && !isVisible(sb)) toggle(root, side, document.activeElement);
    },
    close: function (rootOrId, side) {
      var root = resolve(rootOrId);
      var sb = root && sidebar(root, side);
      if (sb && isVisible(sb) && canToggle(sb)) toggle(root, side, document.activeElement);
    },
  };
})();
