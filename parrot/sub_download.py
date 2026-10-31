import json
import re
import urllib.request
from urllib.parse import parse_qs, parse_qsl, urlencode, urlsplit, urlunsplit

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


def normalize(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\W]+", " ", text)
    text = text.lower()
    return text.strip()


def player_response(video_id: str) -> dict:
    req = urllib.request.Request(
        "https://www.youtube.com/youtubei/v1/player?prettyPrint=false",
        data=json.dumps({"context": CONTEXT, "videoId": video_id}).encode(),
        headers={
            "Content-Type": "application/json",
            "User-Agent": CONTEXT["client"]["userAgent"],
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def timedtext_json3(base_url: str) -> dict:
    parts = urlsplit(base_url)
    query = dict(parse_qsl(parts.query))
    query["fmt"] = "json3"
    url = urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )
    req = urllib.request.Request(
        url, headers={"User-Agent": CONTEXT["client"]["userAgent"]}
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def fetch_segments(video_id: str, lang: str = "en") -> list[dict]:
    pr = player_response(video_id)
    tracks = pr["captions"]["playerCaptionsTracklistRenderer"]["captionTracks"]

    track = next(
        (t for t in tracks if t["languageCode"] == lang and not t.get("kind")),
        None,
    )

    if track is None:
        return None

    data = timedtext_json3(track["baseUrl"])

    out = []
    # print(track)
    for i, event in enumerate(data.get("events", []), 1):
        text = "".join(seg.get("utf8", "") for seg in event.get("segs", []))
        if not text.strip():
            continue
        start = event.get("tStartMs", 0) / 1000
        out.append(
            {
                "video_id": video_id,
                "cue_id": i,
                "start_time": int(start),
                "end_time": int(start + event.get("dDurationMs", 0) / 1000),
                "text": normalize(text),
            }
        )
    return out


def extract_video_id(url: str):
    result = urlsplit(url)
    if result.netloc == "youtu.be":
        return result.path[1:]
    elif "youtube.com" in result.netloc:
        query = parse_qs(result.query)
        return query.get("v", None)[0]
