"use strict";

// Each comparison owns a shared playhead. Original video files are never retimed.
(() => {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const controllers = [];
  fetch("showcase-data.json")
    .then((response) => {
      if (!response.ok) throw new Error("Video index unavailable");
      return response.json();
    })
    .then((data) => {
      document.querySelectorAll("[data-feature]").forEach((card) => {
        const config = data[card.dataset.feature];
        const players = [...card.querySelectorAll("video")];
        const play = card.querySelector(".feature-play");
        const select = card.querySelector("select");
        const seek = card.querySelector(".feature-seek");
        const time = card.querySelector(".feature-time");
        const status = card.querySelector(".feature-status");
        let visible = false;
        let loaded = false;
        let wanted = !reducedMotion.matches;
        let active = false;
        let revision = 0;
        function announce(message) {
          status.textContent = message;
          status.classList.remove("sr-only");
        }
        function pause() {
          active = false;
          players.forEach((video) => video.pause());
          play.textContent = "Play pair";
          play.setAttribute("aria-label", `Play ${config.model} comparison`);
          play.setAttribute("aria-pressed", "false");
        }
        function load() {
          if (loaded) return;
          loaded = true;
          players.forEach((video) => {
            video.src = video.dataset.src;
            video.load();
          });
        }
        async function start() {
          if (document.hidden || !visible || active) return;
          load();
          const current = ++revision;
          const startAt = players[0].ended ? 0 : players[0].currentTime;
          players.forEach((video) => {
            if (video.readyState >= 1) video.currentTime = startAt;
          });
          active = true;
          play.textContent = "Pause pair";
          play.setAttribute("aria-label", `Pause ${config.model} comparison`);
          play.setAttribute("aria-pressed", "true");
          const results = await Promise.allSettled(players.map((video) => video.play()));
          if (revision !== current) return;
          if (results.some((result) => result.status === "rejected")) {
            wanted = false;
            pause();
            announce("Select Play pair to start both videos.");
          } else {
            status.textContent = "";
            status.classList.add("sr-only");
          }
        }
        function duration() {
          if (!players.every((v) => Number.isFinite(v.duration))) return;
          seek.max = String(Math.min(...players.map((v) => v.duration)));
          seek.disabled = false;
        }
        players.forEach((video) => {
          video.loop = false;
          video.addEventListener("loadedmetadata", duration);
          video.addEventListener("error", () => {
            wanted = false;
            revision += 1;
            pause();
            announce("This video could not load. Choose another sample or reload the page.");
          });
          video.addEventListener("ended", () => {
            if (!active) return;
            pause();
            players.forEach((v) => {
              v.currentTime = 0;
            });
            if (wanted && visible) start();
          });
        });
        players[0].addEventListener("timeupdate", () => {
          const t = players[0].currentTime;
          seek.value = String(t);
          time.textContent = `${t.toFixed(1)} s`;
          if (active && players[1].readyState >= 2 && Math.abs(players[1].currentTime - t) > 0.15) players[1].currentTime = t;
        });
        play.disabled = false;
        select.disabled = false;
        play.setAttribute("aria-pressed", "false");
        play.addEventListener("click", () => {
          wanted = !active;
          revision += 1;
          if (active) pause();
          else start();
        });
        select.addEventListener("change", () => {
          revision += 1;
          pause();
          const index = Number(select.value);
          const clip = config.clips[index];
          loaded = false;
          players.forEach((video, i) => {
            const method = i ? "VARQ" : "Baseline";
            video.removeAttribute("src");
            video.dataset.src = clip.sources[method];
            video.poster = clip.posters[method];
            video.setAttribute("aria-label", `${config.model} ${method === "VARQ" ? "VAR-Q " + config.bits : "BF16 reference"}: ${clip.prompt}`);
            video.load();
          });
          card.querySelector(".feature-index").textContent = `${String(index + 1).padStart(2, "0")} / ${String(config.clips.length).padStart(
            2,
            "0",
          )}`;
          card.querySelector(".feature-prompt").textContent = clip.prompt;
          time.textContent = "0.0 s";
          seek.value = "0";
          seek.disabled = true;
          status.textContent = "";
          status.classList.add("sr-only");
          load();
          if (wanted && visible) start();
        });
        seek.addEventListener("input", () => {
          const t = Number(seek.value);
          players.forEach((v) => {
            if (v.readyState >= 1) v.currentTime = t;
          });
          time.textContent = `${t.toFixed(1)} s`;
        });
        const controller = {
          pauseForPage() {
            revision += 1;
            pause();
          },
          resumeForPage() {
            if (wanted && visible) start();
          },
          reduceMotion() {
            wanted = false;
            revision += 1;
            pause();
          },
        };
        controllers.push(controller);
        new IntersectionObserver(
          ([entry]) => {
            visible = entry.isIntersecting;
            if (visible) {
              if (wanted) start();
            } else {
              revision += 1;
              pause();
            }
          },
          { threshold: 0.25 },
        ).observe(card);
      });
    })
    .catch(() => {
      document.querySelectorAll(".feature-card").forEach((card) => {
        const status = card.querySelector(".feature-status");
        status.textContent = "Paired controls unavailable. Use the individual video controls below.";
        status.classList.remove("sr-only");
        card.querySelectorAll("video").forEach((video) => {
          video.src = video.dataset.src;
          video.controls = true;
        });
      });
    });
  document.addEventListener("visibilitychange", () => controllers.forEach((c) => (document.hidden ? c.pauseForPage() : c.resumeForPage())));
  reducedMotion.addEventListener("change", () => {
    if (reducedMotion.matches) controllers.forEach((c) => c.reduceMotion());
  });
})();
