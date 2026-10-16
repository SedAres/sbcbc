(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  const root = $("#player-page");
  if (!root) return;
  const dataNode = $("#player-data");
  let data;
  try { data = JSON.parse(dataNode.textContent); } catch (_) { return; }

  const media = $("[data-media]");
  const state = {
    playing: false,
    duration: Number(data.duration || 0),
    currentTime: Number(data.startTime || 0),
    userVolume: 1,
    userMuted: false,
    baseRate: Number(data.settings?.playback_speed || 1),
    selectedTrack: data.tracks?.[0]?.key || "",
    cues: [],
    activeCue: -1,
    transcriptQuery: "",
    manualTranscriptScrollAt: 0,
    saveTimer: 0,
    saving: false,
    epubChapters: [],
    epubIndex: 0,
    epubFontSize: 18,
  };

  const fileById = new Map((data.files || []).map(file => [Number(file.file_id), file]));
  const fileByHash = new Map((data.files || []).map(file => [file.file_hash, file]));
  const progressFill = $("[data-progress-fill]");
  const seekbar = $("[data-seekbar]");
  const timeCurrent = $("[data-current-time]");
  const timeDuration = $("[data-duration]");
  const playIcon = $("[data-play-icon]");
  const saveState = $("[data-save-state]");

  const fmt = seconds => {
    const value = Math.max(0, Math.floor(Number(seconds) || 0));
    const hours = Math.floor(value / 3600);
    const minutes = Math.floor((value % 3600) / 60);
    const secs = value % 60;
    return hours ? `${hours}:${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}` : `${minutes}:${String(secs).padStart(2, "0")}`;
  };
  const notify = (message, kind = "success") => window.LocalAcademy?.toast(message, kind);
  const isTextInput = target => target instanceof HTMLElement && (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName));

  class SilenceSkipController {
    constructor(element, options = {}) {
      this.media = element;
      this.threshold = Number(options.threshold ?? -42);
      this.minDuration = Number(options.minDuration ?? 0.65);
      this.skipRate = Number(options.skipRate ?? 8);
      this.enabled = false;
      this.isSkipping = false;
      this.userMuted = false;
      this.lastDb = -100;
      this.silenceStart = null;
      this.audioContext = null;
      this.source = null;
      this.outputGain = null;
      this.worklet = null;
      this.analyser = null;
      this.sampleBuffer = null;
      this.raf = 0;
      this.onState = () => {};
      this.onFailure = () => {};
    }

    configure(options = {}) {
      if (Number.isFinite(Number(options.threshold))) this.threshold = Number(options.threshold);
      if (Number.isFinite(Number(options.minDuration))) this.minDuration = Number(options.minDuration);
      if (Number.isFinite(Number(options.skipRate))) this.skipRate = Number(options.skipRate);
      this.applyRate();
    }

    async prepare() {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) throw new Error("Audio analysis is not supported by this browser.");
      if (!this.audioContext) {
        this.audioContext = new AudioContextClass();
        this.userMuted = this.userMuted || Boolean(this.media.muted);
        // Keep the media element's signal live for analysis; mute only the output gain.
        this.media.muted = false;
        this.source = this.audioContext.createMediaElementSource(this.media);
        this.outputGain = this.audioContext.createGain();
        this.outputGain.gain.value = this.userMuted || this.isSkipping ? 0 : 1;
        this.outputGain.connect(this.audioContext.destination);
        let connected = false;
        if (this.audioContext.audioWorklet && window.AudioWorkletNode) {
          const workletSource = `
            class LocalAcademyLevelMeter extends AudioWorkletProcessor {
              constructor() { super(); this.sum = 0; this.count = 0; this.frames = 0; }
              process(inputs, outputs) {
                const input = inputs[0] || [];
                const output = outputs[0] || [];
                for (let channel = 0; channel < output.length; channel++) {
                  const source = input[channel] || input[0];
                  const target = output[channel];
                  if (!source) { target.fill(0); continue; }
                  target.set(source);
                  for (let i = 0; i < source.length; i++) { const sample = source[i]; this.sum += sample * sample; this.count++; }
                  this.frames += source.length;
                }
                if (this.frames >= 512) {
                  const rms = this.count ? Math.sqrt(this.sum / this.count) : 0;
                  const db = 20 * Math.log10(Math.max(rms, 0.0000001));
                  this.port.postMessage(db);
                  this.sum = 0; this.count = 0; this.frames = 0;
                }
                return true;
              }
            }
            registerProcessor('local-academy-level-meter', LocalAcademyLevelMeter);
          `;
          let moduleUrl;
          try {
            moduleUrl = URL.createObjectURL(new Blob([workletSource], { type: "text/javascript" }));
            await this.audioContext.audioWorklet.addModule(moduleUrl);
            URL.revokeObjectURL(moduleUrl);
            this.worklet = new AudioWorkletNode(this.audioContext, "local-academy-level-meter", {
              numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [2],
            });
            this.worklet.port.onmessage = event => {
              if (Number.isFinite(event.data)) this.lastDb = event.data;
            };
            this.source.connect(this.worklet);
            this.worklet.connect(this.outputGain);
            connected = true;
          } catch (error) {
            if (moduleUrl) URL.revokeObjectURL(moduleUrl);
            this.source.disconnect();
            this.worklet?.disconnect();
            this.worklet = null;
          }
        }
        if (!connected) {
          this.analyser = this.audioContext.createAnalyser();
          this.analyser.fftSize = 2048;
          this.sampleBuffer = new Float32Array(this.analyser.fftSize);
          this.source.connect(this.analyser);
          this.analyser.connect(this.outputGain);
        }
      }
      if (this.audioContext.state === "suspended") await this.audioContext.resume();
    }

    async setEnabled(enabled) {
      if (!enabled) {
        this.enabled = false;
        cancelAnimationFrame(this.raf);
        this.raf = 0;
        this.silenceStart = null;
        this.leaveQuietSection();
        this.onState(false);
        return true;
      }
      try {
        await this.prepare();
        this.enabled = true;
        this.watch();
        this.onState(this.isSkipping);
        return true;
      } catch (error) {
        this.enabled = false;
        this.leaveQuietSection();
        if (!this.outputGain) this.media.muted = this.userMuted;
        this.onFailure(error);
        this.onState(false);
        return false;
      }
    }

    async resume() {
      if (this.audioContext?.state === "suspended") {
        try { await this.audioContext.resume(); } catch (_) { /* playback can continue without analysis */ }
      }
      if (this.enabled) this.watch();
    }

    setOutputMuteState() {
      if (!this.media) return;
      const muted = this.userMuted || this.isSkipping;
      if (!this.outputGain) {
        this.media.muted = muted;
        return;
      }
      this.media.muted = false;
      const parameter = this.outputGain.gain;
      const now = this.audioContext.currentTime;
      parameter.cancelScheduledValues(now);
      parameter.setTargetAtTime(muted ? 0 : 1, now, 0.015);
    }

    setUserMuted(muted) {
      this.userMuted = Boolean(muted);
      this.setOutputMuteState();
    }

    setBaseRate(rate) {
      this.baseRate = Math.min(4, Math.max(0.25, Number(rate) || 1));
      this.applyRate();
    }

    applyRate() {
      if (this.media) this.media.playbackRate = this.isSkipping ? this.skipRate : this.baseRate;
    }

    watch() {
      if (this.raf || !this.enabled) return;
      const sample = () => {
        this.raf = 0;
        if (!this.enabled) return;
        if (!this.media || this.media.paused || this.media.ended || this.media.seeking) {
          this.silenceStart = null;
          if (this.isSkipping && (!this.media || this.media.paused || this.media.ended)) this.leaveQuietSection();
          return;
        }
        if (this.analyser && this.sampleBuffer) {
          this.analyser.getFloatTimeDomainData(this.sampleBuffer);
          let sum = 0;
          for (let index = 0; index < this.sampleBuffer.length; index++) sum += this.sampleBuffer[index] * this.sampleBuffer[index];
          const rms = Math.sqrt(sum / this.sampleBuffer.length);
          this.lastDb = 20 * Math.log10(Math.max(rms, 0.0000001));
        }
        const time = Number(this.media.currentTime || 0);
        const releaseThreshold = this.threshold + 5;
        if (!this.isSkipping) {
          if (this.lastDb <= this.threshold) {
            if (this.silenceStart === null) this.silenceStart = time;
            if (time - this.silenceStart >= this.minDuration) this.enterQuietSection();
          } else if (this.lastDb >= releaseThreshold) {
            this.silenceStart = null;
          }
        } else if (this.lastDb >= releaseThreshold) {
          this.silenceStart = null;
          this.leaveQuietSection();
        }
        this.raf = requestAnimationFrame(sample);
      };
      this.raf = requestAnimationFrame(sample);
    }

    enterQuietSection() {
      if (this.isSkipping) return;
      this.isSkipping = true;
      this.setOutputMuteState();
      this.applyRate();
      this.onState(true);
    }

    leaveQuietSection() {
      if (!this.isSkipping) return;
      this.isSkipping = false;
      this.setOutputMuteState();
      this.applyRate();
      this.onState(false);
    }

    destroy() {
      cancelAnimationFrame(this.raf);
      try { this.worklet?.disconnect(); this.analyser?.disconnect(); this.source?.disconnect(); } catch (_) {}
      this.audioContext?.close().catch(() => {});
    }
  }

  const skipper = media ? new SilenceSkipController(media, {
    threshold: data.settings?.skip_silence_db_threshold,
    minDuration: data.settings?.skip_silence_min_duration,
    skipRate: data.settings?.skip_silence_speed,
  }) : null;

  function updateMediaUI() {
    if (!media) return;
    state.currentTime = Number(media.currentTime || 0);
    if (Number.isFinite(media.duration)) state.duration = media.duration;
    const fraction = state.duration ? Math.max(0, Math.min(1, state.currentTime / state.duration)) : 0;
    if (progressFill) progressFill.style.width = `${fraction * 100}%`;
    if (seekbar) {
      seekbar.setAttribute("aria-valuenow", String(Math.round(fraction * 100)));
      seekbar.setAttribute("aria-valuetext", `${fmt(state.currentTime)} of ${fmt(state.duration)}`);
    }
    if (timeCurrent) timeCurrent.textContent = fmt(state.currentTime);
    if (timeDuration && state.duration) timeDuration.textContent = fmt(state.duration);
    if (playIcon && playIcon.dataset.state !== String(media.paused)) {
      playIcon.replaceChildren(window.LocalAcademy.icon(media.paused ? "play" : "pause"));
      playIcon.dataset.state = String(media.paused);
    }
    $$('[data-action="toggle-play"]').forEach(button => button.setAttribute("aria-label", media.paused ? "Play lesson" : "Pause lesson"));
    state.playing = !media.paused;
    $("#media-stage")?.classList.toggle("is-paused", media.paused);
    renderActiveCue();
    updateNoteTime();
  }

  function updateNoteTime() {
    const display = $("[data-note-time]");
    if (display) display.textContent = fmt(state.currentTime);
  }

  function seekTo(seconds) {
    if (!media || !Number.isFinite(Number(seconds))) return;
    const maximum = Number.isFinite(media.duration) ? media.duration : Number.MAX_SAFE_INTEGER;
    media.currentTime = Math.max(0, Math.min(maximum, Number(seconds)));
    skipper && (skipper.silenceStart = null);
    updateMediaUI();
  }

  async function togglePlay() {
    if (!media) return;
    if (media.paused) {
      if (skipper && data.settings?.skip_silence_enabled && !skipper.enabled) await skipper.setEnabled(true);
      await skipper?.resume();
      try { await media.play(); } catch (error) { notify("Press play to start this lesson.", "error"); }
    } else {
      media.pause();
    }
    updateMediaUI();
  }

  function setSpeed(rate) {
    state.baseRate = Number(rate) || 1;
    if (skipper) skipper.setBaseRate(state.baseRate);
    else if (media) media.playbackRate = state.baseRate;
    const select = $("[data-speed]");
    if (select && [...select.options].some(option => Number(option.value) === state.baseRate)) select.value = String(state.baseRate);
  }

  function updateMuteUI() {
    if (!media) return;
    const muted = media.volume === 0 || (skipper ? skipper.userMuted : media.muted);
    const button = $('[data-action="mute"]');
    button?.classList.toggle("is-muted", muted);
    button?.setAttribute("aria-pressed", String(Boolean(muted)));
    button?.setAttribute("aria-label", muted ? "Unmute" : "Mute");
  }

  function adjustVolume(delta) {
    if (!media) return;
    media.volume = Math.max(0, Math.min(1, media.volume + delta));
    if (skipper) skipper.setUserMuted(media.volume === 0);
    const slider = $("[data-volume]");
    if (slider) slider.value = String(media.volume);
    updateMuteUI();
  }

  function seekBy(offset) { if (media) seekTo((media.currentTime || 0) + offset); }

  function formatTimeStamp(seconds) { return fmt(seconds); }

  function setPanelTab(tabName) {
    if (!$$('[data-panel-tab]').some(button => !button.hidden && button.dataset.panelTab === tabName)) tabName = "lessons";
    $$('[data-panel-tab]').forEach(button => {
      const active = button.dataset.panelTab === tabName;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", String(active));
      button.tabIndex = active ? 0 : -1;
    });
    $$('[data-panel-view]').forEach(panel => {
      const active = panel.dataset.panelView === tabName;
      panel.hidden = !active;
      panel.classList.toggle("is-active", active);
    });
  }

  function cueButton(cue, index) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "transcript-cue";
    button.dataset.cueIndex = String(index);
    button.dataset.cueStart = String(cue.start);
    const time = document.createElement("span");
    time.className = "transcript-cue-time";
    time.textContent = formatTimeStamp(cue.start);
    const text = document.createElement("span");
    text.className = "transcript-cue-text";
    text.textContent = cue.text;
    button.append(time, text);
    button.addEventListener("click", () => seekTo(cue.start));
    return button;
  }

  function renderTranscript() {
    const list = $("[data-transcript-list]");
    if (!list) return;
    list.replaceChildren();
    state.cues.forEach((cue, index) => {
      const button = cueButton(cue, index);
      if (state.transcriptQuery && !cue.text.toLocaleLowerCase().includes(state.transcriptQuery)) button.hidden = true;
      list.append(button);
    });
    const count = $("[data-transcript-count]");
    if (count) count.textContent = `${state.cues.length} ${state.cues.length === 1 ? "caption" : "captions"}`;
    const empty = $("[data-transcript-empty]");
    const footer = $("[data-transcript-footer]");
    if (empty) empty.hidden = data.tracks.length > 0;
    if (footer) footer.hidden = data.tracks.length === 0;
    if (!state.cues.length && data.tracks.length) {
      const message = document.createElement("p");
      message.className = "transcript-message";
      message.textContent = "No readable captions were found in this track.";
      list.append(message);
    }
    updateTrackControls();
  }

  async function loadTranscript(trackKey = state.selectedTrack) {
    state.selectedTrack = trackKey || "";
    if (!trackKey) {
      state.cues = [];
      renderTranscript();
      return;
    }
    const list = $("[data-transcript-list]");
    if (list) list.innerHTML = '<p class="reader-loading">Loading transcript…</p>';
    try {
      const response = await fetch(`/player/api/${encodeURIComponent(data.fileHash)}/transcript?track=${encodeURIComponent(trackKey)}`, { headers: { "Accept": "application/json" } });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Could not load this transcript.");
      state.cues = result.cues || [];
      state.activeCue = -1;
      renderTranscript();
      applyNativeCaptions();
    } catch (error) {
      if (list) {
        list.replaceChildren();
        const message = document.createElement("p");
        message.className = "transcript-message";
        message.textContent = error.message;
        list.append(message);
      }
    }
  }

  function renderActiveCue() {
    if (!state.cues.length) return;
    const time = Number(media?.currentTime || 0);
    let low = 0;
    let high = state.cues.length - 1;
    let found = -1;
    while (low <= high) {
      const mid = (low + high) >> 1;
      if (state.cues[mid].start <= time) { found = mid; low = mid + 1; }
      else high = mid - 1;
    }
    if (found >= 0 && time > state.cues[found].end) found = -1;
    if (found === state.activeCue) return;
    state.activeCue = found;
    $$('.transcript-cue.is-active').forEach(row => row.classList.remove("is-active"));
    if (found < 0) return;
    const current = $(`[data-cue-index="${found}"]`);
    current?.classList.add("is-active");
    const list = $("[data-transcript-list]");
    if (current && list && Date.now() - state.manualTranscriptScrollAt > 3500) {
      const target = current.offsetTop - list.offsetTop - list.clientHeight * 0.43;
      list.scrollTo({ top: Math.max(0, target), behavior: "smooth" });
    }
  }

  function updateTrackControls() {
    const select = $("[data-track-select]");
    const wrap = $("[data-track-select-wrap]");
    const uploadButton = $("[data-caption-upload-button]");
    if (select) {
      const selected = state.selectedTrack;
      select.replaceChildren();
      (data.tracks || []).forEach(track => {
        const option = document.createElement("option");
        option.value = track.key;
        option.textContent = `${track.label}${track.source === "attached" ? " · attached" : ""}`;
        option.selected = track.key === selected;
        select.append(option);
      });
      if (wrap) wrap.hidden = !data.tracks.length;
    }
    if (uploadButton) uploadButton.hidden = !["video", "audio"].includes(data.fileType);
    const removeButton = $("[data-delete-track]");
    const activeTrack = data.tracks.find(track => track.key === state.selectedTrack);
    if (removeButton) removeButton.hidden = !activeTrack || activeTrack.source !== "attached";
  }

  function applyNativeCaptions() {
    if (!media?.textTracks) return;
    const tracks = [...media.textTracks];
    const elements = $$('track[kind="subtitles"]', media);
    const selectedTrack = data.tracks.find(track => track.key === state.selectedTrack);
    const selectedIndex = selectedTrack ? data.tracks.indexOf(selectedTrack) : -1;
    tracks.forEach((track, index) => {
      track.mode = data.settings?.subtitle_enabled && index === selectedIndex ? "showing" : "hidden";
    });
    if (elements[selectedIndex]) elements[selectedIndex].default = Boolean(data.settings?.subtitle_enabled);
    const button = $('[data-action="captions"]');
    if (button) {
      button.classList.toggle("is-on", Boolean(data.settings?.subtitle_enabled && selectedTrack));
      button.setAttribute("aria-pressed", String(Boolean(data.settings?.subtitle_enabled && selectedTrack)));
      button.disabled = data.tracks.length === 0;
    }
  }

  function addNativeTrack(track) {
    if (!media) return;
    const element = document.createElement("track");
    element.kind = "subtitles";
    element.src = track.url;
    element.srclang = track.language || "und";
    element.label = track.label;
    media.append(element);
    element.track.mode = "hidden";
  }

  function initTranscript() {
    const select = $("[data-track-select]");
    select?.addEventListener("change", () => loadTranscript(select.value));
    $("[data-transcript-search]")?.addEventListener("input", event => {
      state.transcriptQuery = event.target.value.trim().toLocaleLowerCase();
      renderTranscript();
    });
    $("[data-transcript-list]")?.addEventListener("scroll", () => { state.manualTranscriptScrollAt = Date.now(); }, { passive: true });
    $$('[data-caption-upload-button]').forEach(button => button.addEventListener("click", () => $("[data-caption-file]")?.click()));
    $("[data-caption-file]")?.addEventListener("change", async event => {
      const file = event.target.files?.[0];
      if (!file) return;
      const form = $("#caption-upload-form");
      const formData = new FormData(form);
      const button = $("[data-caption-upload-button]");
      button && (button.disabled = true);
      try {
        const response = await fetch(`/player/${encodeURIComponent(data.fileHash)}/subtitles`, { method: "POST", body: formData, headers: { "Accept": "application/json" } });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Could not attach captions.");
        data.tracks.push(result.track);
        addNativeTrack(result.track);
        state.selectedTrack = result.track.key;
        setPanelTab("transcript");
        updateTrackControls();
        await loadTranscript(result.track.key);
        notify(`Caption track “${result.track.label}” attached.`);
      } catch (error) { notify(error.message, "error"); }
      finally { if (button) button.disabled = false; event.target.value = ""; }
    });
    $("[data-delete-track]")?.addEventListener("click", async () => {
      const track = data.tracks.find(item => item.key === state.selectedTrack);
      if (!track || track.source !== "attached") return;
      if (!await window.LocalAcademy.confirm({ title: "Remove this caption track?", message: `The attached “${track.label}” track will be removed. Your lesson and original sidecar captions stay unchanged.`, confirmLabel: "Remove track", danger: true })) return;
      try {
        const response = await fetch(`/player/subtitles/attached/${track.id}`, { method: "DELETE" });
        if (!response.ok) throw new Error("Could not remove this caption track.");
        data.tracks = data.tracks.filter(item => item.key !== track.key);
        if (media) $$('track[kind="subtitles"]', media).forEach(element => {
          if (element.src.endsWith(`/attached/${track.id}.vtt`)) element.remove();
        });
        state.selectedTrack = data.tracks[0]?.key || "";
        updateTrackControls();
        await loadTranscript(state.selectedTrack);
        applyNativeCaptions();
        notify("Caption track removed.");
      } catch (error) { notify(error.message, "error"); }
    });
    if (data.tracks?.length) loadTranscript(state.selectedTrack || data.tracks[0].key);
    else updateTrackControls();
  }

  function initPanelTabs() {
    const tabs = $$('[data-panel-tab]').filter(button => !button.hidden);
    tabs.forEach(button => {
      button.addEventListener("click", () => setPanelTab(button.dataset.panelTab));
      button.addEventListener("keydown", event => {
        const keys = ["ArrowLeft", "ArrowRight", "Home", "End"];
        if (!keys.includes(event.key)) return;
        event.preventDefault();
        const current = tabs.indexOf(button);
        const index = event.key === "Home" ? 0 : (event.key === "End" ? tabs.length - 1 : (current + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length);
        setPanelTab(tabs[index].dataset.panelTab);
        tabs[index].focus();
      });
    });
    const requested = location.hash.slice(1);
    setPanelTab(tabs.some(button => button.dataset.panelTab === requested) ? requested : (data.tracks.length ? "transcript" : "lessons"));
  }

  function buildSavedItem(type, item) {
    const entry = document.createElement("article");
    entry.className = `saved-item ${type}-item`;
    const jump = document.createElement("button");
    jump.type = "button";
    jump.className = "saved-item-jump";
    const file = fileById.get(Number(item.file_id));
    const timedLesson = ["audio", "video"].includes(file?.file_type);
    const time = document.createElement("span");
    time.className = "saved-item-time";
    time.textContent = item.timestamp == null ? "General note" : (timedLesson ? fmt(item.timestamp) : "Lesson");
    const copy = document.createElement("span");
    copy.className = "saved-item-copy";
    const title = document.createElement("strong");
    title.textContent = type === "note" ? item.content : (item.label || (timedLesson ? "Saved moment" : "Saved lesson"));
    const source = document.createElement("small");
    source.textContent = file?.title || "Course lesson";
    copy.append(title, source);
    jump.append(time, copy);
    jump.addEventListener("click", () => {
      const target = fileById.get(Number(item.file_id));
      if (target && target.file_hash !== data.fileHash) {
        window.location.assign(`/player/${target.file_hash}${timedLesson && item.timestamp != null ? `?t=${Math.floor(item.timestamp)}` : ""}`);
      } else if (media && item.timestamp != null) {
        seekTo(item.timestamp);
      }
    });
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "saved-item-delete";
    remove.append(window.LocalAcademy.icon("close"));
    remove.setAttribute("aria-label", type === "note" ? "Delete note" : "Delete bookmark");
    remove.addEventListener("click", event => {
      event.stopPropagation();
      type === "note" ? deleteNote(item.id) : deleteBookmark(item.id);
    });
    entry.append(jump, remove);
    return entry;
  }

  function renderSavedItems() {
    const notes = (data.allNotes || []).slice().sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
    const bookmarks = (data.allBookmarks || []).slice().sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
    const noteList = $("[data-notes-list]");
    const bookmarkList = $("[data-bookmarks-list]");
    if (noteList) {
      noteList.replaceChildren(...notes.map(note => buildSavedItem("note", note)));
      $("[data-notes-empty]").hidden = notes.length > 0;
    }
    if (bookmarkList) {
      bookmarkList.replaceChildren(...bookmarks.map(bookmark => buildSavedItem("bookmark", bookmark)));
      $("[data-bookmarks-empty]").hidden = bookmarks.length > 0;
    }
  }

  function initNoteComposer() {
    const composer = $("[data-note-composer]");
    const form = $("[data-note-form]");
    const timestampOption = $('input[name="timestamped"]', form);
    $$('[data-action="note"]').forEach(button => button.addEventListener("click", () => {
      const error = $("[data-note-error]", form);
      if (error) error.hidden = true;
      window.LocalAcademy.openModal(composer);
      updateNoteTime();
      $("textarea", form)?.focus();
    }));
    $$('[data-action="close-note"]').forEach(button => button.addEventListener("click", () => window.LocalAcademy.closeModal(composer)));
    composer?.addEventListener("click", event => { if (event.target === composer) window.LocalAcademy.closeModal(composer); });
    form?.addEventListener("submit", async event => {
      event.preventDefault();
      const textarea = $("textarea", form);
      const errorBox = $("[data-note-error]", form);
      const content = textarea.value.trim();
      if (!content) return;
      const timestamp = timestampOption.checked ? state.currentTime : null;
      const submit = $('button[type="submit"]', form);
      if (submit.disabled) return;
      submit.disabled = true;
      submit.textContent = "Saving note…";
      composer.setAttribute("aria-busy", "true");
      try {
        const response = await fetch(`/player/notes/${encodeURIComponent(data.fileHash)}`, {
          method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify({ content, timestamp }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Could not save your note.");
        data.notes.unshift(result.note);
        data.allNotes.unshift(result.note);
        textarea.value = "";
        composer.removeAttribute("aria-busy");
        window.LocalAcademy.closeModal(composer);
        setPanelTab("notes");
        renderSavedItems();
        notify("Note saved to this course.");
      } catch (error) {
        if (errorBox) { errorBox.textContent = error.message; errorBox.hidden = false; }
      } finally {
        submit.disabled = false;
        submit.textContent = "Save note";
        composer.removeAttribute("aria-busy");
      }
    });
  }

  async function deleteNote(noteId) {
    if (!await window.LocalAcademy.confirm({ title: "Delete this note?", message: "This note will be removed from your course notebook. This can’t be undone.", confirmLabel: "Delete note", danger: true })) return;
    try {
      const response = await fetch(`/player/notes/${noteId}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Could not delete this note.");
      data.notes = data.notes.filter(item => item.id !== noteId);
      data.allNotes = data.allNotes.filter(item => item.id !== noteId);
      renderSavedItems();
      notify("Note deleted.");
    } catch (error) { notify(error.message, "error"); }
  }

  function initBookmarkComposer() {
    const composer = $("[data-bookmark-composer]");
    const form = $("[data-bookmark-form]");
    $$('[data-action="bookmark"]').forEach(button => button.addEventListener("click", () => {
      window.LocalAcademy.openModal(composer);
      const label = $('input[name="label"]', form);
      if (label) { label.value = ""; label.focus(); }
      const time = $("[data-bookmark-time]", form);
      if (time) time.textContent = fmt(state.currentTime);
    }));
    $$('[data-action="close-bookmark"]').forEach(button => button.addEventListener("click", () => window.LocalAcademy.closeModal(composer)));
    composer?.addEventListener("click", event => { if (event.target === composer) window.LocalAcademy.closeModal(composer); });
    form?.addEventListener("submit", async event => {
      event.preventDefault();
      const label = $('input[name="label"]', form).value.trim() || `Moment at ${fmt(state.currentTime)}`;
      const submit = $('button[type="submit"]', form);
      if (submit.disabled) return;
      submit.disabled = true;
      submit.textContent = "Saving moment…";
      composer.setAttribute("aria-busy", "true");
      try {
        const response = await fetch(`/player/bookmarks/${encodeURIComponent(data.fileHash)}`, {
          method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify({ timestamp: state.currentTime, label }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Could not save this moment.");
        data.bookmarks.push(result.bookmark);
        data.allBookmarks.push(result.bookmark);
        composer.removeAttribute("aria-busy");
        window.LocalAcademy.closeModal(composer);
        setPanelTab("bookmarks");
        renderSavedItems();
        notify("Moment saved.");
      } catch (error) { notify(error.message, "error"); }
      finally {
        submit.disabled = false;
        submit.textContent = "Save moment";
        composer.removeAttribute("aria-busy");
      }
    });
  }

  async function deleteBookmark(bookmarkId) {
    if (!await window.LocalAcademy.confirm({ title: "Remove this saved moment?", message: "The bookmark will be removed. Your lesson and learning progress stay unchanged.", confirmLabel: "Remove bookmark", danger: true })) return;
    try {
      const response = await fetch(`/player/bookmarks/${bookmarkId}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Could not remove this saved moment.");
      data.bookmarks = data.bookmarks.filter(item => item.id !== bookmarkId);
      data.allBookmarks = data.allBookmarks.filter(item => item.id !== bookmarkId);
      renderSavedItems();
      notify("Saved moment removed.");
    } catch (error) { notify(error.message, "error"); }
  }

  async function saveProgress(completed = data.completed) {
    if (!media || state.saving) return;
    state.saving = true;
    try {
      const response = await fetch(`/player/progress/${encodeURIComponent(data.fileHash)}`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_time: media.currentTime || 0, completed: Boolean(completed) }),
        keepalive: true,
      });
      if (response.ok) {
        data.completed = Boolean(completed);
        if (saveState) {
          saveState.textContent = "Progress saved";
          saveState.classList.add("is-saved");
          window.setTimeout(() => saveState.classList.remove("is-saved"), 1200);
        }
      }
    } catch (_) { /* a later heartbeat will retry */ }
    finally { state.saving = false; }
  }

  function updateCompletionUI() {
    $$("[data-complete-label]").forEach(label => { label.textContent = data.completed ? "Completed" : "Mark complete"; });
    $$('[data-action="mark-complete"]').forEach(button => {
      button.classList.toggle("is-complete", data.completed);
      button.setAttribute("aria-pressed", String(data.completed));
    });
  }

  async function markComplete() {
    if (state.completionSaving) return;
    state.completionSaving = true;
    const buttons = $$('[data-action="mark-complete"]');
    buttons.forEach(button => { button.disabled = true; });
    const nextValue = !data.completed;
    try {
      const response = await fetch(`/api/mark-watched/${encodeURIComponent(data.fileHash)}`, {
        method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ completed: nextValue }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Could not update lesson completion.");
      data.completed = Boolean(result.completed);
      updateCompletionUI();
      if (media) saveProgress(data.completed);
      notify(data.completed ? "Lesson marked complete." : "Lesson marked incomplete.");
    } catch (error) { notify(error.message, "error"); }
    finally {
      state.completionSaving = false;
      buttons.forEach(button => { button.disabled = false; });
    }
  }

  async function shareTimestamp() {
    try {
      const response = await fetch("/player/timestamp-link", {
        method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ timestamp: state.currentTime, file_hash: data.fileHash }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Could not create a link.");
      const shareUrl = new URL(result.link, window.location.origin);
      shareUrl.protocol = window.location.protocol;
      shareUrl.host = window.location.host;
      const formatted = (result.markdown || result.link).replaceAll(result.link, shareUrl.href);
      await navigator.clipboard.writeText(formatted);
      notify("Timestamp link copied.");
    } catch (_) { notify("Clipboard access is unavailable in this browser.", "error"); }
  }

  function setTheater(enabled) {
    document.body.classList.toggle("theater-active", Boolean(enabled));
    const button = $('[data-action="theater"]');
    button?.setAttribute("aria-pressed", String(Boolean(enabled)));
  }

  function toggleFullscreen() {
    const stage = $("#media-stage");
    if (!stage) return;
    if (!document.fullscreenElement) stage.requestFullscreen?.().catch(() => {});
    else document.exitFullscreen?.().catch(() => {});
  }

  function initControls() {
    $$('[data-action="toggle-play"]').forEach(button => {
      button.addEventListener("click", togglePlay);
      if (button.getAttribute("role") === "button") button.addEventListener("keydown", event => {
        if (event.key === "Enter") { event.preventDefault(); togglePlay(); }
      });
    });
    $('[data-action="seek-back"]')?.addEventListener("click", () => seekBy(-5));
    $('[data-action="seek-forward"]')?.addEventListener("click", () => seekBy(5));
    $('[data-action="mute"]')?.addEventListener("click", () => {
      if (!media) return;
      const muted = !(skipper ? skipper.userMuted : media.muted);
      if (skipper) skipper.setUserMuted(muted);
      else media.muted = muted;
      updateMuteUI();
    });
    $("[data-volume]")?.addEventListener("input", event => {
      if (!media) return;
      media.volume = Number(event.target.value);
      if (skipper) skipper.setUserMuted(media.volume === 0);
      updateMuteUI();
    });
    $("[data-speed]")?.addEventListener("change", event => setSpeed(event.target.value));
    $('[data-action="silence"]')?.addEventListener("click", async buttonEvent => {
      if (!skipper) return;
      const button = buttonEvent.currentTarget;
      button.disabled = true;
      const enabled = !skipper.enabled;
      const ok = await skipper.setEnabled(enabled);
      if (ok) {
        data.settings.skip_silence_enabled = enabled;
        button.classList.toggle("is-on", enabled);
        button.setAttribute("aria-pressed", String(enabled));
        notify(enabled ? "Silence skip is on." : "Silence skip is off.");
      }
      button.disabled = false;
    });
    $('[data-action="captions"]')?.addEventListener("click", () => {
      if (!data.tracks.length) { setPanelTab("transcript"); return; }
      data.settings.subtitle_enabled = !data.settings.subtitle_enabled;
      applyNativeCaptions();
    });
    $('[data-action="theater"]')?.addEventListener("click", () => setTheater(!document.body.classList.contains("theater-active")));
    $('[data-action="fullscreen"]')?.addEventListener("click", toggleFullscreen);
    $('[data-action="copy-link"]')?.addEventListener("click", shareTimestamp);
    $$('[data-action="mark-complete"]').forEach(button => button.addEventListener("click", markComplete));
    $("[data-action=zoom-image]")?.addEventListener("click", event => {
      const image = $("#lesson-image");
      image?.classList.toggle("is-zoomed");
      const zoomed = Boolean(image?.classList.contains("is-zoomed"));
      event.currentTarget.replaceChildren(window.LocalAcademy.icon(zoomed ? "minus" : "plus"));
      event.currentTarget.setAttribute("aria-label", zoomed ? "Zoom out" : "Zoom image");
      event.currentTarget.setAttribute("aria-pressed", String(zoomed));
    });

    const seekFromPointer = event => {
      if (!media || !state.duration) return;
      const rect = seekbar.getBoundingClientRect();
      seekTo(((event.clientX - rect.left) / rect.width) * state.duration);
    };
    seekbar?.addEventListener("pointerdown", event => {
      if (!media) return;
      seekbar.setPointerCapture?.(event.pointerId);
      seekFromPointer(event);
    });
    seekbar?.addEventListener("pointermove", event => {
      if (event.buttons) seekFromPointer(event);
    });
    seekbar?.addEventListener("keydown", event => {
      if (event.key === "ArrowLeft") { event.preventDefault(); seekBy(-5); }
      if (event.key === "ArrowRight") { event.preventDefault(); seekBy(5); }
      if (event.key === "Home") seekTo(0);
      if (event.key === "End" && state.duration) seekTo(state.duration);
    });

    document.addEventListener("keydown", event => {
      if (event.defaultPrevented) return;
      if (event.key === "Escape" && document.body.classList.contains("theater-active")) { setTheater(false); return; }
      if (isTextInput(event.target) || (event.target instanceof HTMLElement && event.target.closest("button, a, select, [role='slider']")) || event.metaKey || event.ctrlKey || event.altKey) return;
      if (event.key === " " || event.code === "Space") { event.preventDefault(); togglePlay(); }
      else if (event.key === "ArrowLeft" && event.shiftKey) { event.preventDefault(); navigateLesson(-1); }
      else if (event.key === "ArrowRight" && event.shiftKey) { event.preventDefault(); navigateLesson(1); }
      else if (event.key === "ArrowLeft") { event.preventDefault(); seekBy(-5); }
      else if (event.key === "ArrowRight") { event.preventDefault(); seekBy(5); }
      else if (event.key === "ArrowUp" && media) { event.preventDefault(); adjustVolume(0.05); }
      else if (event.key === "ArrowDown" && media) { event.preventDefault(); adjustVolume(-0.05); }
      else if (event.key.toLowerCase() === "t") setTheater(!document.body.classList.contains("theater-active"));
      else if (event.key.toLowerCase() === "f") toggleFullscreen();
      else if (event.key.toLowerCase() === "c") $('[data-action="captions"]')?.click();
      else if (event.key.toLowerCase() === "n") $('[data-action="note"]')?.click();
      else if (event.key.toLowerCase() === "b") $('[data-action="bookmark"]')?.click();
    });

    if (data.settings?.theater_mode) setTheater(true);
  }

  function navigateLesson(direction) {
    const next = data.files?.[Number(data.currentIndex) + direction];
    if (next) window.location.assign(`/player/${next.file_hash}`);
  }

  function initMedia() {
    if (!media) return;
    media.volume = state.userVolume;
    updateMuteUI();
    media.addEventListener("loadedmetadata", async () => {
      state.duration = Number.isFinite(media.duration) ? media.duration : state.duration;
      const wanted = Number(data.startTime || 0);
      if (wanted > 0 && Number.isFinite(media.duration)) media.currentTime = Math.min(wanted, Math.max(0, media.duration - 0.25));
      setSpeed(state.baseRate);
      updateMediaUI();
      if (data.duration === 0 && state.duration > 0) {
        fetch(`/api/set-duration/${encodeURIComponent(data.fileHash)}`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ duration: state.duration }),
        }).catch(() => {});
      }
      if (media.videoWidth && media.videoHeight) $("#media-stage")?.classList.toggle("is-portrait", media.videoHeight > media.videoWidth);
      applyNativeCaptions();
      if (data.settings?.skip_silence_enabled && skipper) await skipper.setEnabled(true);
      updateMuteUI();
    });
    media.addEventListener("timeupdate", updateMediaUI);
    media.addEventListener("durationchange", updateMediaUI);
    media.addEventListener("play", () => { updateMediaUI(); if (skipper?.enabled) skipper.watch(); });
    media.addEventListener("pause", () => { updateMediaUI(); saveProgress(); });
    media.addEventListener("seeking", () => { if (skipper) skipper.silenceStart = null; });
    media.addEventListener("seeked", () => { if (skipper?.enabled && !media.paused) skipper.watch(); });
    media.addEventListener("ended", async () => {
      state.currentTime = state.duration;
      updateMediaUI();
      await saveProgress(true);
      if (!data.completed) {
        data.completed = true;
        updateCompletionUI();
      }
      if (data.settings?.auto_advance) window.setTimeout(() => navigateLesson(1), 900);
    });
    media.addEventListener("error", () => notify("This file could not be played in the browser. Try downloading it or use a supported format.", "error"));
    window.setInterval(() => saveProgress(), 8000);
    window.addEventListener("pagehide", () => { if (media && !media.paused) saveProgress(); skipper?.destroy(); });
    if (skipper) {
      skipper.onState = active => {
        const button = $('[data-action="silence"]');
        const status = $("[data-silence-status]");
        button?.classList.toggle("is-skipping", active);
        if (status) status.hidden = !active;
      };
      skipper.onFailure = error => notify(error.message, "error");
    }
  }

  function initTextReader() {
    const reader = $("[data-text-reader]");
    if (!reader) return;
    fetch(reader.dataset.url).then(response => {
      if (!response.ok) throw new Error("This document could not be opened.");
      return response.text();
    }).then(text => { $("[data-text-content]", reader).textContent = text; })
      .catch(error => { $("[data-text-content]", reader).textContent = error.message; });
  }

  async function initEpubReader() {
    const reader = $("[data-epub-reader]");
    if (!reader) return;
    const toc = $("[data-epub-toc]", reader);
    const content = $("[data-epub-content]", reader);
    const loadChapter = async index => {
      if (!state.epubChapters.length) return;
      state.epubIndex = Math.max(0, Math.min(state.epubChapters.length - 1, index));
      toc.value = String(state.epubIndex);
      content.innerHTML = "";
      const loading = document.createElement("p");
      loading.className = "reader-loading";
      loading.textContent = "Opening chapter…";
      content.append(loading);
      try {
        const response = await fetch(`${reader.dataset.url}?chapter=${state.epubIndex}`);
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Could not read this chapter.");
        content.replaceChildren();
        const heading = document.createElement("h2");
        heading.textContent = result.chapter.title;
        const text = document.createElement("div");
        text.className = "epub-chapter-text";
        text.textContent = result.chapter.text;
        content.append(heading, text);
        content.style.setProperty("--reader-size", `${state.epubFontSize}px`);
        content.scrollTop = 0;
      } catch (error) {
        content.textContent = error.message;
      }
    };
    try {
      const response = await fetch(reader.dataset.url);
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Could not open this EPUB.");
      state.epubChapters = result.chapters || [];
      toc.replaceChildren();
      state.epubChapters.forEach(chapter => {
        const option = document.createElement("option");
        option.value = String(chapter.index);
        option.textContent = `${String(chapter.index + 1).padStart(2, "0")} · ${chapter.title}`;
        toc.append(option);
      });
      if (!state.epubChapters.length) throw new Error("No readable chapters were found.");
      await loadChapter(0);
    } catch (error) { content.textContent = error.message; }
    toc.addEventListener("change", () => loadChapter(Number(toc.value)));
    $("[data-epub-prev]", reader)?.addEventListener("click", () => loadChapter(state.epubIndex - 1));
    $("[data-epub-next]", reader)?.addEventListener("click", () => loadChapter(state.epubIndex + 1));
    $("[data-epub-font]", reader)?.addEventListener("click", () => {
      state.epubFontSize = state.epubFontSize >= 23 ? 16 : state.epubFontSize + 2;
      content.style.setProperty("--reader-size", `${state.epubFontSize}px`);
    });
  }

  function initHotkeyBridge() {
    const actions = {
      play_pause: togglePlay,
      rewind_5s: () => seekBy(-5),
      forward_5s: () => seekBy(5),
      prev_file: () => navigateLesson(-1),
      next_file: () => navigateLesson(1),
      volume_up: () => adjustVolume(0.05),
      volume_down: () => adjustVolume(-0.05),
      speed_up: () => setSpeed(state.baseRate + 0.25),
      speed_down: () => setSpeed(state.baseRate - 0.25),
      toggle_subtitles: () => $('[data-action="captions"]')?.click(),
    };
    window.setInterval(async () => {
      try {
        const response = await fetch("/api/hotkey/poll", { headers: { "Accept": "application/json" } });
        const result = await response.json();
        (result.actions || []).forEach(action => actions[action]?.());
      } catch (_) { /* the optional desktop helper may not be running */ }
    }, 700);
  }

  function init() {
    initPanelTabs();
    initTranscript();
    initNoteComposer();
    initBookmarkComposer();
    initControls();
    initMedia();
    initTextReader();
    initEpubReader();
    renderSavedItems();
    updateCompletionUI();
    if (media) {
      if (state.currentTime > 0 && !Number.isFinite(media.duration)) state.currentTime = Number(data.startTime || 0);
      updateNoteTime();
      updateMediaUI();
    }
    initHotkeyBridge();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
