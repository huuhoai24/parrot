// ============================================================
// Caption/phụ đề dùng chung (index.html + study.html)
// Nạp phụ đề qua /api/transcript (cache theo video_id, tránh fetch lại)
// và cập nhật #caption-text theo Player.time() mỗi 250ms.
// Yêu cầu: player.js đã nhúng (dùng Player.time()/Player.ready).
// Options của init: { selector } — phần tử caption, mặc định #caption-text.
// ============================================================
const Transcript = (() => {
  const cache = {};   // video_id -> cues
  let cues = [];      // phụ đề của video đang phát
  let wantId = null;  // video được yêu cầu gần nhất (chống race khi chuyển nhanh)
  let selector = "#caption-text";

  function init(options = {}) {
    if (options.selector) selector = options.selector;
    setInterval(show, 250);
  }

  async function load(videoId) {
    if (!videoId) return;
    wantId = videoId;
    if (!cache[videoId]) {
      const r = await fetch("/api/transcript?video_id=" + videoId);
      const data = await r.json();
      cache[videoId] = data.transcript;
    }
    if (wantId === videoId) cues = cache[videoId];
  }

  function show() {
    const el = document.querySelector(selector);
    if (!el || !Player.ready || cues.length === 0) return;
    const t = Player.time();
    for (const c of cues) {
      if (t >= c.start_time && t < c.end_time) {
        if (el.textContent !== c.text) el.textContent = c.text;
        return;
      }
    }
  }

  // Cue phụ đề đang phát (dùng cho nút Save: front + mốc start/end)
  function currentCue() {
    if (!Player.ready || cues.length === 0) return null;
    const t = Player.time();
    return cues.find(c => t >= c.start_time && t < c.end_time) || null;
  }

  return { init, load, currentCue };
})();
