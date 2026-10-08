"use strict";

(() => {
  const modelSelect = document.querySelector("#gallery-model");
  const bitSelect = document.querySelector("#gallery-bit");
  const sampleSelect = document.querySelector("#gallery-sample");
  const media = document.querySelector("#gallery-media");
  const status = document.querySelector("#gallery-status");
  const play = document.querySelector("#gallery-play");
  const seek = document.querySelector("#gallery-seek");
  const speed = document.querySelector("#gallery-speed");
  let models = [];
  let players = [];
  let playing = false;
  let generation = 0;
  const selectedModel = () => models.find((model) => model.id === modelSelect.value);
  const paradigm = (model) => (["self_forcing", "longlive"].includes(model.id) ? "Next-frame" : "Next-scale");
  function options(select, entries, preferred) {
    select.replaceChildren();
    entries.forEach(([value, label]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      select.append(option);
    });
    if (entries.some(([value]) => value === preferred)) select.value = preferred;
    select.disabled = entries.length === 0;
  }
  function pause() {
    players.forEach((video) => video.pause());
    playing = false;
    play.textContent = "Play all";
  }
  function updateDuration() {
    if (players.length && players.every((video) => Number.isFinite(video.duration))) {
      seek.max = String(Math.min(...players.map((video) => video.duration)));
      seek.disabled = false;
    }
  }
  function renderSample() {
    generation += 1;
    pause();
    players.forEach((video) => {
      video.removeAttribute("src");
      video.load();
    });
    players = [];
    media.replaceChildren();
    const model = selectedModel();
    const sample = model.samples[bitSelect.value]?.[Number(sampleSelect.value)];
    const isVideo = model.type === "video";
    document.querySelector("#gallery-playback").hidden = !isVideo;
    document.querySelector("#gallery-task").textContent = `${paradigm(model)} · ${model.label} · ${model.task} · ${
      model.bitLabels[bitSelect.value]
    } KV cache`;
    document.querySelector("#gallery-prompt").textContent = sample?.prompt
      ? `“${sample.prompt}”`
      : `${model.task} — sample ${Number(sampleSelect.value) + 1}`;
    seek.value = "0";
    seek.disabled = true;
    document.querySelector("#gallery-time").textContent = "0.0 s";
    status.textContent = isVideo
      ? "Use Play all to start the paired videos together. The shared timeline controls every method."
      : "Paired outputs from the project’s original sample collection. Baseline uses BF16; other methods use the selected KV precision.";
    if (!sample) {
      status.textContent = "No samples are available for this configuration.";
      return;
    }
    media.dataset.columns = String(model.methods.length);
    model.methods.forEach((method) => {
      const source = sample.media[method];
      const cell = document.createElement("figure");
      cell.className = `gallery-cell${method === "VARQ" ? " gallery-ours" : ""}`;
      const label = document.createElement("figcaption");
      label.textContent =
        method === "VARQ"
          ? `VAR-Q · ${model.bitLabels[bitSelect.value]}`
          : method === "Baseline"
            ? "BF16 reference"
            : `${model.methodLabels[method]} · ${model.bitLabels[bitSelect.value]}`;
      cell.append(label);
      if (source && source.startsWith("samples/") && !source.includes("..")) {
        const item = document.createElement(isVideo ? "video" : "img");
        if (isVideo) {
          item.muted = true;
          item.playsInline = true;
          item.preload = "metadata";
          item.setAttribute("aria-label", `${label.textContent}: ${sample.prompt || model.task}`);
          item.playbackRate = Number(speed.value);
          item.addEventListener("loadedmetadata", updateDuration);
          item.addEventListener("ended", pause);
          item.addEventListener("error", () => {
            pause();
            status.textContent = "A video could not load. Try another sample, or reload this page.";
          });
          players.push(item);
        } else {
          item.alt = `${label.textContent}: ${sample.prompt || model.task}`;
          item.loading = "lazy";
          item.addEventListener("error", () => {
            status.textContent = "An image could not load. Try another sample, or reload this page.";
          });
        }
        item.src = source;
        cell.append(item);
      } else {
        const missing = document.createElement("p");
        missing.className = "missing-media";
        missing.textContent = "Not available for this setting";
        cell.append(missing);
      }
      media.append(cell);
    });
    if (players[0]) {
      players[0].addEventListener("timeupdate", () => {
        const leader = players[0];
        seek.value = String(leader.currentTime);
        document.querySelector("#gallery-time").textContent = `${leader.currentTime.toFixed(1)} s`;
        if (playing)
          players.slice(1).forEach((video) => {
            if (Math.abs(video.currentTime - leader.currentTime) > 0.2 && video.readyState >= 2) video.currentTime = leader.currentTime;
          });
      });
    }
  }
  function renderSamples() {
    const samples = selectedModel().samples[bitSelect.value] || [];
    options(
      sampleSelect,
      samples.map((_, index) => [String(index), `Sample ${index + 1} of ${samples.length}`]),
    );
    renderSample();
  }
  function renderModel() {
    const model = selectedModel();
    options(
      bitSelect,
      model.bits.map((bit) => [bit, model.bitLabels[bit]]),
      bitSelect.value,
    );
    renderSamples();
  }
  modelSelect.addEventListener("change", renderModel);
  bitSelect.addEventListener("change", renderSamples);
  sampleSelect.addEventListener("change", renderSample);
  play.addEventListener("click", async () => {
    if (playing) {
      pause();
      return;
    }
    if (!players.length) return;
    const currentGeneration = generation;
    const start = players[0].ended ? 0 : players[0].currentTime;
    players.forEach((video) => {
      video.currentTime = start;
      video.playbackRate = Number(speed.value);
    });
    playing = true;
    play.textContent = "Pause all";
    status.textContent = "Starting paired videos…";
    const results = await Promise.allSettled(players.map((video) => video.play()));
    if (currentGeneration !== generation) return;
    if (results.some((result) => result.status === "rejected")) {
      pause();
      status.textContent = "Playback could not start for every video. Wait for loading, then try Play all again.";
    } else {
      status.textContent = "Videos use a shared playhead. Seek or restart to compare the same moment across methods.";
    }
  });
  document.querySelector("#gallery-restart").addEventListener("click", () => {
    pause();
    players.forEach((video) => {
      video.currentTime = 0;
    });
    seek.value = "0";
    document.querySelector("#gallery-time").textContent = "0.0 s";
  });
  seek.addEventListener("input", () => {
    players.forEach((video) => {
      video.currentTime = Number(seek.value);
    });
    document.querySelector("#gallery-time").textContent = `${Number(seek.value).toFixed(1)} s`;
  });
  speed.addEventListener("change", () => {
    players.forEach((video) => {
      video.playbackRate = Number(speed.value);
    });
  });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) pause();
  });
  fetch("manifest.json")
    .then((response) => {
      if (!response.ok) throw new Error("Sample index unavailable");
      return response.json();
    })
    .then((data) => {
      models = data.models;
      modelSelect.replaceChildren();
      ["Next-scale", "Next-frame"].forEach((name) => {
        const group = document.createElement("optgroup");
        group.label = name === "Next-scale" ? "Next-scale · Images & video" : "Next-frame · Video";
        models
          .filter((model) => paradigm(model) === name)
          .forEach((model) => {
            const option = document.createElement("option");
            option.value = model.id;
            option.textContent = model.label;
            group.append(option);
          });
        modelSelect.append(group);
      });
      modelSelect.value = "Infinity8B";
      modelSelect.disabled = false;
      renderModel();
    })
    .catch(() => {
      status.textContent = "The sample gallery could not load. Reload this page to try again; the paper figures remain available below.";
    });
})();
