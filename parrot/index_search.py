import json
from collections import defaultdict
from pathlib import Path

subs = Path("Subtitles/clean")

query = ["how", "have", "you", "been"]
video_list = []

index = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

for path in subs.glob("*.json"):
    data = json.loads(path.read_text(encoding="utf-8"))
    video_id = Path(path).stem

    if video_id not in video_list:
        video_list.append(video_id)
    v_id = video_list.index(video_id)

    for cue in data:
        text = cue["text"]
        cue_id = cue["cue_id"]
        for pos, word in enumerate(text.split()):
            index[word][cue_id][v_id].append(pos)


result = []
for cue_id, videos in index[query[0]].items():
    for v_id, start_positions in videos.items():
        for start in start_positions:
            matched = True

            for i in range(1, len(query)):
                word = query[i]

                positions = index[word].get(cue_id, {}).get(v_id, [])

                if start + i not in positions:
                    matched = False
                    break

            if matched:
                path = subs / f"{video_list[v_id]}.json"
                data = json.loads(path.read_text(encoding="utf-8"))
                cue = next((block for block in data if block["cue_id"] == cue_id), None)
                if cue is not None:
                    start_time = cue["start_time"]
                    result.append(
                        {
                            "video_id": video_list[v_id],
                            "cue": cue_id,
                            "posittion": start,
                            "start_time": start_time,
                        }
                    )
                    print(
                        f"video_id: {video_list[v_id]}, cue: {cue_id}, posittion: {start}, start_time: {start_time}"
                    )
# print(result)
