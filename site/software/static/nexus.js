(function () {
  var root = document.querySelector("[data-nexus-root]");
  if (!root || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return;
  }

  var portals = Array.prototype.slice.call(document.querySelectorAll(".world-portal"));
  var targetX = 0.5;
  var targetY = 0.45;
  var currentX = targetX;
  var currentY = targetY;
  var ticking = false;

  function setActiveTheme(theme) {
    if (!theme) {
      return;
    }
    document.documentElement.dataset.activeWorld = theme;
    if (theme === "data") {
      root.style.setProperty("--active", "var(--nx-emerald)");
      root.style.setProperty("--active-2", "var(--nx-teal)");
      root.style.setProperty("--active-soft", "rgba(56, 230, 165, 0.18)");
    } else if (theme === "production") {
      root.style.setProperty("--active", "var(--nx-amber)");
      root.style.setProperty("--active-2", "var(--nx-gold)");
      root.style.setProperty("--active-soft", "rgba(255, 184, 77, 0.2)");
    } else {
      root.style.setProperty("--active", "var(--nx-cyan)");
      root.style.setProperty("--active-2", "var(--nx-blue)");
      root.style.setProperty("--active-soft", "rgba(55, 213, 255, 0.2)");
    }
  }

  function animate() {
    currentX += (targetX - currentX) * 0.12;
    currentY += (targetY - currentY) * 0.12;
    root.style.setProperty("--mouse-x", (currentX * 100).toFixed(2) + "%");
    root.style.setProperty("--mouse-y", (currentY * 100).toFixed(2) + "%");
    ticking = Math.abs(targetX - currentX) > 0.001 || Math.abs(targetY - currentY) > 0.001;
    if (ticking) {
      window.requestAnimationFrame(animate);
    }
  }

  window.addEventListener("pointermove", function (event) {
    targetX = event.clientX / Math.max(window.innerWidth, 1);
    targetY = event.clientY / Math.max(window.innerHeight, 1);
    if (!ticking) {
      ticking = true;
      window.requestAnimationFrame(animate);
    }
  }, { passive: true });

  portals.forEach(function (portal) {
    portal.addEventListener("pointermove", function (event) {
      var rect = portal.getBoundingClientRect();
      var x = ((event.clientX - rect.left) / rect.width - 0.5).toFixed(3);
      var y = ((event.clientY - rect.top) / rect.height - 0.5).toFixed(3);
      portal.style.setProperty("--mx", x);
      portal.style.setProperty("--my", y);
    }, { passive: true });

    portal.addEventListener("pointerenter", function () {
      setActiveTheme(portal.dataset.world);
    });

    portal.addEventListener("focus", function () {
      setActiveTheme(portal.dataset.world);
    });

    portal.addEventListener("click", function (event) {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
        return;
      }
      event.preventDefault();
      portal.classList.add("is-entering");
      root.classList.add("is-transitioning");
      setActiveTheme(portal.dataset.world);
      window.setTimeout(function () {
        window.location.href = portal.href;
      }, 720);
    });
  });
}());
