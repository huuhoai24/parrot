import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs, parse_qsl, urlencode, urlsplit, urlunsplit

import requests

_local = threading.local()
CONTEXT = {
    "client": {
        "clientName": "ANDROID",
        "clientVersion": "21.26.364",
        "androidSdkVersion": 30,
        "userAgent": "com.google.android.youtube/21.26.364 (Linux; U; Android 11) gzip",
        "osName": "Android",
        "osVersion": "11",
        "hl": "en",
    }
}
UA = CONTEXT["client"]["userAgent"]
_NON_WORD = re.compile(r"\W+")
PLAYER_URL = (
    "https://www.youtube.com/youtubei/v1/player"
    "?prettyPrint=false&fields=captions,playabilityStatus"
)


def normalize(text):
    return _NON_WORD.sub(" ", text).lower().strip()


def extract_video_id(url: str):
    u = urlsplit(url)
    if u.hostname == "youtu.be":
        return u.path[1:] or None
    if u.hostname and u.hostname.endswith("youtube.com"):
        return (parse_qs(u.query).get("v") or [None])[0]


def session():
    if not hasattr(_local, "s"):
        s = requests.Session()
        s.headers["User-Agent"] = UA
        s.mount(
            "https://",
            requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=4),
        )
        _local.s = s
    return _local.s


def player_response(video_id):
    r = session().post(
        PLAYER_URL,
        json={"context": CONTEXT, "videoId": video_id},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def timedtext_json3(base_url):
    parts = urlsplit(base_url)
    query = dict(parse_qsl(parts.query))
    query["fmt"] = "json3"
    url = urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )
    r = session().get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def fetch_segments(video_id: str, lang: str = "en") -> list[dict]:
    pr = player_response(video_id)
    tracks = (
        pr.get("captions", {})
        .get("playerCaptionsTracklistRenderer", {})
        .get("captionTracks", [])
    )
    track = next(
        (
            t
            for t in tracks
            if t["languageCode"].split("-")[0] == lang and not t.get("kind")
        ),
        None,
    )
    if track is None:
        print("skip: no manual subs", video_id)
        return None
    data = timedtext_json3(track["baseUrl"])
    out = []
    # print(track)
    for i, event in enumerate(data.get("events", []), 1):
        text = "".join(seg.get("utf8", "") for seg in event.get("segs", []))
        norm_text = normalize(text)
        if not norm_text:
            continue
        start_ms = event.get("tStartMs", 0)
        end_ms = start_ms + event.get("dDurationMs", 0)
        out.append(
            {
                "video_id": video_id,
                "cue_id": i,
                "start_time": start_ms // 1000,
                "end_time": end_ms // 1000,
                "text": norm_text,
            }
        )
    return out


def safe_fetch(video_id):
    try:
        return video_id, fetch_segments(video_id)
    except Exception as e:
        logging.exception("Failed video ID: ", video_id)
        return video_id, None


def fetch_many(video_ids, workers=6):
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return dict(ex.map(safe_fetch, video_ids))
