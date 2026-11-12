import json

from parrot.database import SubtitleStore
from parrot.fetch_subtitles import fetch_many


def read_file_ids(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)["video_id"]


def process_batch(store, batch):
    results = fetch_many(batch, workers=6)
    saved, skipped = 0, 0

    for video_id, cues in results.items():
        if cues is None:
            skipped += 1
            continue
        try:
            store.save_cues(video_id, cues)
            saved += 1
        except Exception as e:
            skipped += 1
            print(f"can't save {video_id}: {type(e).__name__}: {e}")
    print(f"batch done: saved={saved}, skipped={skipped}")
    return saved, skipped


path = "dataset/video_ids.jsonl"
BATCH = 200
saved = skipped = 0
with SubtitleStore() as store:
    batch = []
    for vid in read_file_ids(path):
        if store.has_video(vid):
            continue
        batch.append(vid)
        if len(batch) >= BATCH:
            s, k = process_batch(store, batch)
            saved += s
            skipped += k
            batch = []
    if batch:
        s, k = process_batch(store, batch)
        saved += s
        skipped += k
print(f"done: saved={saved}, skipped={skipped}")
