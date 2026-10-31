let yt, ytReady = false, pending = null;
  window.onYouTubeIframeAPIReady = function () {
    yt = new YT.Player("ytplayer", {
      width: "100%", height: "100%",
      videoId: "",
      events:{
        onReady: function(){
          ytReady = true;
          if (typeof playlist !== "undefined") play(0);
        },
        onStateChange: function (e) {
          document.getElementById("imgPlay").src =
            e.data === 1 ? "/static/img/pause.png" : "/static/img/play.png";
      },
      },
    });
};

function loadVideo(videoId, startTime) {
  if (!ytReady) return;
  yt.loadVideoById(videoId, startTime);
}

function restart() {
  if (!ytReady) return;
  yt.seekTo(playlist[current].start_time, true);
  yt.playVideo();
}

function back5(){
  if (!ytReady) return;
  const state = yt.getPlayerState();
  if (state === -1 || state === 5) {
      play(current);
      return;
    }
  const now = yt.getCurrentTime();
  const base = now > 0 ? now : playlist[current].start_time;
  yt.seekTo(Math.max(0, base - 5), true);
  yt.playVideo();
}

function pause() {
  if (!ytReady) return;
  const st = yt.getPlayerState()
  if (st === 1) {
    yt.pauseVideo();
  } else {
    yt.playVideo();
  }
}

let current = 0;
let sub = [];
const captionEl = document.getElementById("r_caption");

function play(i){
  if (i<0 || i>=playlist.length) return;
  current = i;
  const v = playlist[i];
  sub = transcripts[v.video_id] || []
  document.getElementById("hIndex").textContent = i + 1;
  loadVideo(v.video_id, v.start_time)
}

function showTranscript() {
  if (!ytReady || sub.length === 0) return;
  const t = yt.getCurrentTime();
  for (const c of sub) {
    if (t >= c.start_time && t < c.end_time) {
      if (captionEl.textContent !== c.text)
          captionEl.textContent = c.text;
      return;
    }
  }
}

function next() {play(current+1);}
function prev() {play(current-1);}

document.getElementById("imgPrev") .addEventListener("click", prev);
document.getElementById("imgRe")   .addEventListener("click", restart);
document.getElementById("imgNext") .addEventListener("click", next);
document.getElementById("imgBack5").addEventListener("click", back5);
document.getElementById("imgPlay") .addEventListener("click", pause);
setInterval(showTranscript, 250);
