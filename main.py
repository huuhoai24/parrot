from parrot.database import SubtitleStore
from parrot.sub_download import *

with open("dataset/url_video.jsonl", "r", encoding="utf-8") as f:
    video_ids = [json.loads(line) for line in f if line.strip()]
    print(len(video_ids))

with SubtitleStore() as store:
    saved, skipped = 0, 0
    for i, item in enumerate(video_ids, 1):
        video_id = item["video_id"]
        if store.has_video(video_id):
            print(f"Video id {video_id} has database")
            continue
        try:
            cues = fetch_segments(video_id)
            if cues is None:
                skipped += 1
                print(f"[{i}] skip {video_id}: no manual 'en' subs")
                continue
            n = store.save_cues(video_id, cues)
            print(f"saved {n} cues for {video_id}")
        except Exception as e:
            skipped += 1
            print(f"[{i}] can't save {video_id}: {type(e).__name__}: {e}")
    print(f"done: saved={saved}, skipped={skipped}")
