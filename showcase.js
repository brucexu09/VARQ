"use strict";

// Each BF16 / VAR-Q pair plays in sync while it is on screen. No controls: the videos are the comparison.
(() => {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const cards = [...document.querySelectorAll("[data-feature]")];
  const pairs = cards.map((card) => {
    const players = [...card.querySelectorAll("video")];
    const status = card.querySelector(".feature-status");
    let visible = false;
    let loaded = false;
    function load() {
      if (loaded) return;
      loaded = true;
      players.forEach((video) => {
        video.src = video.dataset.src;
        video.load();
      });
    }
    async function play() {
      if (document.hidden || !visible) return;
      load();
      if (reducedMotion.matches) {
        players.forEach((video) => (video.controls = true));
        return;
      }
      const t = players[0].currentTime;
      players.forEach((video) => {
        if (video.readyState >= 1 && Math.abs(video.currentTime - t) > 0.15) video.currentTime = t;
      });
      const results = await Promise.allSettled(players.map((video) => video.play()));
      if (results.some((r) => r.status === "rejected")) {
        players.forEach((video) => (video.controls = true));
        if (status) {
          status.textContent = "Autoplay is blocked; use the video controls.";
          status.classList.remove("sr-only");
        }
      }
    }
    function pause() {
      players.forEach((video) => video.pause());
    }
    players[0].addEventListener("timeupdate", () => {
      const t = players[0].currentTime;
      const other = players[1];
      if (!other.paused && other.readyState >= 2 && Math.abs(other.currentTime - t) > 0.15) other.currentTime = t;
    });
    players.forEach((video) =>
      video.addEventListener("error", () => {
        if (status) {
          status.textContent = "This video could not load.";
          status.classList.remove("sr-only");
        }
      }),
    );
    new IntersectionObserver(
      ([entry]) => {
        visible = entry.isIntersecting;
        if (visible) play();
        else pause();
      },
      { threshold: 0.3 },
    ).observe(card);
    return { play, pause };
  });
  document.addEventListener("visibilitychange", () => pairs.forEach((p) => (document.hidden ? p.pause() : p.play())));
  reducedMotion.addEventListener("change", () => pairs.forEach((p) => (reducedMotion.matches ? p.pause() : p.play())));
})();
