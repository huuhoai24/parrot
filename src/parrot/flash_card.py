data = {
    "prompt": "how to say when long time meet someone",
    "response": "How have you been",
    "video_id": "fdsh13",
    "start_time": 12,
    "end_time": 14,
    "created_at": "2026-11-10 03:50:55",
}

# from parrot.database import CardStore
#
# with CardStore() as store:
#     card_id = store.add_card(
#         front=data["prompt"],
#         back=data["response"],
#         video_id=data["video_id"],
#         start_time=data["start_time"],
#         end_time=data["end_time"],
#     )
#     print("Đã lưu card id:", card_id)


from datetime import datetime, timedelta

RATINGS = ("again", "hard", "good", "easy")
MIN_EASE = 1.3


def schedule(interval: float, ease: float, reps: int, rating: str) -> dict:
    """SM-2: nhận trạng thái cũ của thẻ + đánh giá, trả về trạng thái mới."""
    if rating == "again":
        reps = 0
        interval = 0
        ease = max(ease - 0.20, MIN_EASE)
    elif rating == "hard":
        interval = interval * 1.2
        ease = max(ease - 0.15, MIN_EASE)
        reps += 1
    elif rating == "easy":
        interval = max(interval, 1) * ease * 1.3
        ease += 0.15
        reps += 1
    else:  # "good"
        if reps == 0:
            interval = 1  # lần đầu: 1 ngày
        elif reps == 1:
            interval = 6  # lần hai: 6 ngày
        else:
            interval = interval * ease
        reps += 1

    due = datetime.now() + timedelta(days=interval)
    return {
        "interval": interval,
        "ease": round(ease, 4),
        "reps": reps,
        "due_date": due.strftime("%Y-%m-%d %H:%M:%S"),
    }
