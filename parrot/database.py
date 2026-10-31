import re
import sqlite3
from dataclasses import dataclass
from tkinter import SW


@dataclass(frozen=True, slots=True)
class Cue:
    video_id: str
    cue_id: int
    start_time: float
    end_time: float
    text: str


class SubtitleStore:
    def __init__(self) -> None:
        self.conn = sqlite3.connect("subtitles.db")
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS subtitles (
            video_id    TEXT     NOT NULL,
            cue_id      INT      NOT NULL,
            start_time  INT    NOT NULL,
            end_time    INT    NOT NULL,
            text        TEXT     NOT NULL,
            PRIMARY KEY (video_id, cue_id))"""
        )
        self.conn.execute(
            """CREATE VIRTUAL TABLE IF NOT EXISTS subtitles_fts using fts5(
            video_id    UNINDEXED,
            cue_id      UNINDEXED,
            start_time  UNINDEXED,
            end_time    UNINDEXED,
            text
            )"""
        )
        self.conn.row_factory = sqlite3.Row

    def save_cues(self, video_id: str, cues):
        rows = [
            (video_id, c["cue_id"], c["start_time"], c["end_time"], c["text"])
            for c in cues
        ]
        if not rows:
            return 0
        with self.conn:
            self.conn.execute("DELETE FROM subtitles WHERE video_id = ?", (video_id,))
            self.conn.execute(
                "DELETE FROM subtitles_fts WHERE video_id = ?", (video_id,)
            )
            self.conn.executemany("INSERT INTO subtitles VALUES(?,?,?,?,?)", rows)
            self.conn.executemany(
                "INSERT INTO subtitles_fts (video_id, cue_id, start_time, end_time, text) VALUES(?,?,?,?,?)",
                rows,
            )
        return len(rows)

    def has_video(self, video_id: str) -> bool:
        return (
            self.conn.execute(
                " SELECT 1 FROM subtitles WHERE video_id = ? LIMIT 1", (video_id,)
            ).fetchone()
            is not None
        )

    def get_videos(self, query: str):
        if not query.strip():
            return []
        fts = '"' + query.replace('"', '""') + '"'
        return self.conn.execute(
            """SELECT video_id, cue_id, start_time
                FROM subtitles_fts
                WHERE subtitles_fts MATCH ?
               ORDER BY rank """,
            (fts,),
        ).fetchall()

    def get_text(self, video_id: str):
        return self.conn.execute(
            "SELECT start_time, end_time, text FROM subtitles "
            "WHERE video_id = ? ORDER BY start_time",
            (video_id,),
        ).fetchall()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "SubtitleStore":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()


# for row in SubtitleStore().get_videos("you"):
#     print(
#         row["video_id"],
#         row["cue_id"],
#     )

# res = SubtitleStore().get_text("3cTt7G6MTsc")
# for r in res:
#     print(r["start_time"], r["end_time"], r["text"])
#     print(type(r["start_time"]))
#     print(type(r[0]))
