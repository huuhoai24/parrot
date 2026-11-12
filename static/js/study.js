// Luồng học thẻ: load thẻ đến hạn -> hiện mặt trước -> Show Answer (checkbox #flip,
// lật bằng CSS) -> hiện lưng + video -> chấm điểm -> thẻ tiếp theo.
// Video + nút điều khiển dùng Player dùng chung (static/js/player.js).
// Khi Show Answer: search ngầm theo field BACK của thẻ (searchVideos, static/js/search.js)
// -> playlist kết quả -> phát như trang index; Previous/Next chuyển giữa các kết quả.
let queue = [];
let current = null;  // thẻ đang học
let playlist = [];   // kết quả search theo field back
let pIndex = 0;      // video đang phát trong playlist

const $ = (sel) => document.querySelector(sel);

Player.init({
  getStart: () =>
    playlist.length ? playlist[pIndex].start_time : (current ? current.start_time : 0),
  onPrev: () => play(pIndex - 1),
  onNext: () => play(pIndex + 1),
});

Transcript.init();

async function loadDue() {
  const res = await fetch("/api/study/due");
  const data = await res.json();
  queue = data.cards;
  nextCard();
}

function nextCard() {
  current = queue.shift();
  $("#flip").checked = false; // quay lại mặt trước cho thẻ mới
  Player.pause(); // dừng video của thẻ cũ (.a-card tự ẩn nhờ CSS #flip)
  if (!current) {
    $("#front-text").textContent = "Không còn thẻ đến hạn 🎉";
    $("#study-progress").textContent = "Hết thẻ";
    $("#ansarea").style.display = "none";
    return;
  }
  $("#front-text").textContent = current.front ?? ""; // front có thể null
  $("#back-text").textContent = current.back;
  $("#study-progress").textContent = `Còn ${queue.length + 1} thẻ`;
}

async function play(i) {
  if (i < 0 || i >= playlist.length) return;
  pIndex = i;
  Player.load(playlist[i].video_id, playlist[i].start_time);
  Transcript.load(playlist[i].video_id);
}

async function showBack() {
  // search ngầm theo field back của thẻ -> phát video đầu tiên tìm được
  playlist = await searchVideos(current.back);
  if (playlist.length) { play(0); return; }
  // không có kết quả -> dùng video gắn với thẻ
  Player.load(current.video_id, current.start_time);
  Transcript.load(current.video_id);
}

async function rate(rating) {
  await fetch(`/api/cards/${current.id}/review?rating=${rating}`, { method: "POST" });
  if (rating === "again") queue.push(current); // quên -> gặp lại trong phiên
  nextCard();
}

$("#btn-show").addEventListener("click", showBack);
document.querySelectorAll(".a-state button[data-rating]").forEach((btn) =>
  btn.addEventListener("click", () => rate(btn.dataset.rating))
);
loadDue();
