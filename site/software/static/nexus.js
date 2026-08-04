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

  document.querySelectorAll(".career-card").forEach(function (card) {
    card.addEventListener("pointerenter", function () {
      var theme = card.dataset.world;
      var color = theme === "data" ? "var(--data)" : theme === "production" ? "var(--production)" : "var(--software)";
      var soft = theme === "data" ? "rgba(18, 168, 123, 0.14)" : theme === "production" ? "rgba(213, 138, 24, 0.15)" : "rgba(47, 111, 237, 0.14)";
      root.style.setProperty("--active", color);
      root.style.setProperty("--active-soft", soft);
    });
  });
}());
