// Trang index: search -> playlist -> phát lần lượt + caption theo transcript.
// Phát video & nút điều khiển: Player (static/js/player.js)
// Caption/phụ đề: Transcript (static/js/transcript.js)
let playlist = [];
let current = 0;

async function search(q) {
  playlist = await searchVideos(q);
  document.getElementById("current-word").textContent = q;
  document.getElementById("total-count").textContent = playlist.length;
  if (playlist.length) {
    document.querySelector(".pronounce-header").hidden = false;
    play(0);
  }
}

async function play(i) {
  if (i < 0 || i >= playlist.length) return;
  current = i;
  const v = playlist[i];
  document.getElementById("current-index").textContent = i + 1;
  Player.load(v.video_id, v.start_time);
  Transcript.load(v.video_id);
}

function next() {play(current+1);}
function prev() { play(current - 1);}

Player.init({
  getStart: () => (playlist[current] ? playlist[current].start_time : 0),
  onPrev: prev,
  onNext: next,
  onReady: () => { if (playlist.length) play(current); },
});

Transcript.init();

document.getElementById("search-form").addEventListener("submit", function (e) {
  e.preventDefault();
  const q = document.querySelector("input[name=q]").value;
  search(q);
});

// Save: lưu cụm từ đang search thành thẻ học (POST /api/cards)
// back = cụm từ; front (tình huống) tạm thời null — bổ sung sau.
// video + mốc start/end = cue phụ đề đang phát (hoặc kết quả search đầu tiên)
document.getElementById("btn-save").addEventListener("click", async function () {
  if (!playlist.length) return;
  const q = document.querySelector("input[name=q]").value.trim();
  const v = playlist[current];
  const cue = Transcript.currentCue();
  const body = {
    front: null,
    back: q,
    video_id: v.video_id,
    start_time: cue ? Math.floor(cue.start_time) : v.start_time,
    end_time: cue ? Math.ceil(cue.end_time) : v.start_time + 3,
  };
  const res = await fetch("/api/cards", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.ok) {
    const btn = this;
    const old = btn.textContent;
    btn.textContent = "Đã lưu ✓";
    btn.disabled = true; // chống bấm đúp tạo thẻ trùng
    setTimeout(() => { btn.textContent = old; btn.disabled = false; }, 1500);
  }
});
