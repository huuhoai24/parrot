// ============================================================
// Player dùng chung (index.html + study.html)
// Tự nạp YouTube IFrame API và tạo player trong #yt-player.
// Player CHỈ được tạo khi đã biết video đầu tiên: videoId + start
// được đưa thẳng vào constructor (playerVars.autoplay/start),
// không tạo player rỗng rồi loadVideoById sau -> không mất thời gian load 2 lần.
// Gắn nút điều khiển NẾU nút đó có mặt trên trang:
//   #btn-replay #btn-back-5 #btn-play -> luôn bind khi có
//   #btn-prev #btn-next               -> chỉ bind khi truyền onPrev/onNext
// Options: { playerId, getStart, onPrev, onNext, onReady }
//   getStart(): mốc start_time cho Replay/Back5 (theo trang đang dùng)
// Quy ước: id = JS hook, class = CSS (xem static/css/base.css)
// ============================================================
const Player = (() => {
  let yt = null;
  let ready = false;    // player đã tạo xong, nhận được lệnh
  let apiReady = false; // script YT API đã nạp xong
  let opts = {};
  let first = null;     // [videoId, startTime] — video đầu tiên, đưa vào constructor
  let queue = [];       // các video gọi load() khi player đang khởi tạo

  const PLAY_ICON = "/static/img/play.png";
  const PAUSE_ICON = "/static/img/pause.png";

  function loadApi() {
    // chống nạp trùng nếu player.js được nhúng nhiều lần
    if (document.querySelector("script[data-yt-api]")) return;
    const s = document.createElement("script");
    s.src = "https://www.youtube.com/iframe_api";
    s.dataset.ytApi = "1";
    document.head.appendChild(s);
  }

  // API gọi lại hàm toàn cục này khi nạp xong
  window.onYouTubeIframeAPIReady = function () {
    apiReady = true;
    if (first) create(); // đã có video chờ -> tạo player với video đó luôn
  };

  function create() {
    const [videoId, startTime] = first;
    // YT API ném "Invalid video id" nếu id rác (dữ liệu test) -> fallback player rỗng
    const vid = /^[A-Za-z0-9_-]{11}$/.test(videoId) ? videoId : "";
    yt = new YT.Player(opts.playerId, {
      width: "100%",
      height: "100%",
      videoId: vid,
      playerVars: { autoplay: 1, start: startTime || 0 },
      events: {
        onReady() {
          ready = true;
          queue.splice(0).forEach(([id, t]) => yt.loadVideoById(id, t));
          if (opts.onReady) opts.onReady();
        },
        onStateChange(e) {
          const btn = document.getElementById("btn-play");
          if (btn) btn.src = e.data === 1 ? PAUSE_ICON : PLAY_ICON;
        },
      },
    });
  }

  function bind(id, fn) {
    const el = document.getElementById(id);
    if (el) el.addEventListener("click", fn);
  }

  function init(options = {}) {
    opts = { playerId: "yt-player", ...options };
    loadApi();
    bind("btn-replay", restart);
    bind("btn-back-5", back5);
    bind("btn-play", togglePlay);
    if (opts.onPrev) bind("btn-prev", opts.onPrev);
    if (opts.onNext) bind("btn-next", opts.onNext);
  }

  function load(videoId, startTime) {
    if (!yt) {
      // player chưa tồn tại -> nhận video id từ đầu: tạo player với video này
      first = [videoId, startTime || 0];
      loadApi();
      if (apiReady) create(); // API đã nạp xong nhưng chưa có video nào
      return;
    }
    if (!ready) { queue.push([videoId, startTime || 0]); return; }
    yt.loadVideoById(videoId, startTime || 0);
  }

  function restart() {
    if (!ready) return;
    yt.seekTo(opts.getStart ? opts.getStart() : 0, true);
    yt.playVideo();
  }

  function back5() {
    if (!ready) return;
    const state = yt.getPlayerState();
    if (state === -1 || state === 5) { restart(); return; }
    const now = yt.getCurrentTime();
    const base = now > 0 ? now : (opts.getStart ? opts.getStart() : 0);
    yt.seekTo(Math.max(0, base - 5), true);
    yt.playVideo();
  }

  function togglePlay() {
    if (!ready) return;
    if (yt.getPlayerState() === 1) yt.pauseVideo();
    else yt.playVideo();
  }

  function pause() {
    if (ready && yt.getPlayerState() === 1) yt.pauseVideo();
  }

  function time() { return ready ? yt.getCurrentTime() : 0; }

  return { init, load, restart, back5, togglePlay, pause, time,
           get ready() { return ready; } };
})();
