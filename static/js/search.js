// Tìm video theo từ khoá qua /api/search — dùng chung cho index.html + study.html.
// Trả về mảng kết quả: [{ video_id, start_time, ... }]
async function searchVideos(q) {
  const res = await fetch("/api/search?q=" + encodeURIComponent(q));
  const state = await res.json();
  return state.results;
}
