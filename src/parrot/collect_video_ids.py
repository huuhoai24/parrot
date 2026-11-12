import json
from pathlib import Path

import yt_dlp

BASE = Path(__file__).resolve().parents[2]
DATASET_DIR = BASE / "dataset"
DATASET_DIR.mkdir(parents=True, exist_ok=True)
CHANNELS_FILE = DATASET_DIR / "channels.txt"
URL_FILE = DATASET_DIR / "video_ids.jsonl"


def get_channel_urls(chanel_url: str):
    opts = {
        "extract_flat": True,
        "quiet": True,
        "ignoreerrors": True,
        "writesubtitles": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"{chanel_url}/videos", download=False)
        for item in info.get("entries"):
            if not item:
                continue
            video_id = item.get("id")
            if not video_id:
                continue
            yield {
                "video_id": video_id,
                # "url": f"https://www.youtube.com/watch?v={video_id}",
            }


def load_existing_ids():
    ids = set()

    if URL_FILE.exists():
        with URL_FILE.open(encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line)
                    ids.add(item["video_id"])
                except (json.JSONDecodeError, KeyError):
                    continue

    return ids


def collector():
    existing_ids = load_existing_ids()
    added = 0

    with CHANNELS_FILE.open(encoding="utf-8") as f:
        channels = [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]

    with URL_FILE.open("a", encoding="utf-8") as output:
        for channel in channels:
            print(f"Collecting: {channel}")

            try:
                for video in get_channel_urls(channel):
                    if video["video_id"] in existing_ids:
                        continue

                    output.write(json.dumps(video, ensure_ascii=False) + "\n")
                    output.flush()

                    existing_ids.add(video["video_id"])
                    added += 1

            except Exception as exc:
                print(f"Failed: {channel}: {exc}")

    print(f"Added {added} new videos")


collector()
