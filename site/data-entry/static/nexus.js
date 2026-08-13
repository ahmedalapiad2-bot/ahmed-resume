(function () {
  var root = document.querySelector("[data-nexus-root]");
  if (!root || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return;
  }

  var targetX = 0.5;
  var targetY = 0.4;
  var currentX = targetX;
  var currentY = targetY;
  var ticking = false;

  function animate() {
    currentX += (targetX - currentX) * 0.12;
    currentY += (targetY - currentY) * 0.12;
    root.style.setProperty("--mouse-x", (currentX * 100).toFixed(2) + "%");
    root.style.setProperty("--mouse-y", (currentY * 100).toFixed(2) + "%");
    ticking =
      Math.abs(targetX - currentX) > 0.001 ||
      Math.abs(targetY - currentY) > 0.001;
    if (ticking) {
      window.requestAnimationFrame(animate);
    }
  }

  window.addEventListener(
    "pointermove",
    function (event) {
      targetX = event.clientX / Math.max(window.innerWidth, 1);
      targetY = event.clientY / Math.max(window.innerHeight, 1);
      if (!ticking) {
        ticking = true;
        window.requestAnimationFrame(animate);
      }
    },
    { passive: true },
  );

  document.querySelectorAll(".career-card").forEach(function (card) {
    card.addEventListener("pointerenter", function () {
      var theme = card.dataset.world;
      var color =
        theme === "data"
          ? "var(--data)"
          : theme === "production"
            ? "var(--production)"
            : "var(--software)";
      var soft =
        theme === "data"
          ? "rgba(18, 168, 123, 0.14)"
          : theme === "production"
            ? "rgba(213, 138, 24, 0.15)"
            : "rgba(47, 111, 237, 0.14)";
      root.style.setProperty("--active", color);
      root.style.setProperty("--active-soft", soft);
    });
  });

  // Download CV modal behavior
  (function () {
    var btn = document.querySelector(".download-cv");
    var modal = document.querySelector(".download-modal");
    if (!btn || !modal) return;

    var closeSelectors = [".download-modal__close", "[data-modal-close]"];
    var previouslyFocused = null;

    function isHidden(el) {
      return el.hasAttribute("hidden");
    }

    function openModal() {
      previouslyFocused = document.activeElement;
      modal.removeAttribute("hidden");
      modal.setAttribute("aria-hidden", "false");
      btn.setAttribute("aria-expanded", "true");
      try {
        document.documentElement.style.overflow = "hidden";
      } catch (e) {}
      // focus first focusable inside modal (close button)
      var close = modal.querySelector(".download-modal__close");
      if (close && typeof close.focus === "function") close.focus();
    }

    function closeModal() {
      modal.setAttribute("hidden", "");
      modal.setAttribute("aria-hidden", "true");
      btn.setAttribute("aria-expanded", "false");
      try {
        document.documentElement.style.overflow = "";
      } catch (e) {}
      if (previouslyFocused && typeof previouslyFocused.focus === "function")
        previouslyFocused.focus();
    }

    btn.addEventListener("click", function (e) {
      e.preventDefault();
      if (isHidden(modal)) openModal();
    });

    // close handlers
    closeSelectors.forEach(function (sel) {
      modal.querySelectorAll(sel).forEach(function (el) {
        el.addEventListener("click", function (ev) {
          ev.preventDefault();
          closeModal();
        });
      });
    });

    // backdrop click: any click directly on backdrop element (data-modal-close)
    modal.addEventListener("click", function (ev) {
      var target = ev.target;
      if (target && target.matches && target.matches("[data-modal-close]")) {
        closeModal();
      }
    });

    // Escape key
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" || ev.key === "Esc") {
        if (!isHidden(modal)) {
          closeModal();
        }
      }
    });
  })();
})();
