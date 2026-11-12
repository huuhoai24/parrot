import sqlite3
from pathlib import Path

from parrot.flash_card import schedule

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "subtitles.db"


class SubtitleStore:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(DB_PATH)
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
            """CREATE VIRTUAL TABLE IF NOT EXISTS subtitles_fts using fts5(text, content='subtitles',content_rowid='rowid'
            )"""
        )
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS subtitles_ai AFTER INSERT ON subtitles BEGIN
              INSERT INTO subtitles_fts(rowid, text) VALUES (new.rowid, new.text);
            END;
            """)
        self.conn.row_factory = sqlite3.Row

    def save_cues(self, video_id: str, cues):
        rows = [
            (video_id, c["cue_id"], c["start_time"], c["end_time"], c["text"])
            for c in cues
        ]
        if not rows:
            return 0
        with self.conn:
            # self.conn.execute("DELETE FROM subtitles WHERE video_id = ?", (video_id,))
            # self.conn.execute(
            #     "DELETE FROM subtitles_fts WHERE video_id = ?", (video_id,)
            # )
            self.conn.executemany("INSERT INTO subtitles VALUES(?,?,?,?,?)", rows)
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
        rows = self.conn.execute(
            """SELECT s.video_id, s.start_time
                FROM subtitles_fts f JOIN subtitles s ON s.rowid = f.rowid
                WHERE subtitles_fts MATCH ?
               ORDER BY rank
               LIMIT 100""",
            (fts,),
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "SubtitleStore":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def get_text(self, video_id: str):
        rows = self.conn.execute(
            "SELECT start_time, end_time, text FROM subtitles "
            "WHERE video_id = ? ORDER BY start_time",
            (video_id,),
        ).fetchall()
        return [dict(r) for r in rows]


class CardStore:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                front      TEXT,
                back       TEXT NOT NULL,
                video_id   TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS card_review (
                card_id  INTEGER PRIMARY KEY REFERENCES cards(id),
                due_date TEXT NOT NULL,
                interval REAL DEFAULT 0,
                ease     REAL DEFAULT 2.5,
                reps     INT  DEFAULT 0
            )
        """)

    def add_card(
        self, front: str, back: str, video_id: str, start_time: int, end_time: int
    ) -> int:
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO cards (front, back, video_id, start_time, end_time) "
                "VALUES (?, ?, ?, ?, ?)",
                (front, back, video_id, start_time, end_time),
            )
            self.conn.execute(
                "INSERT INTO card_review (card_id, due_date) VALUES (?, datetime('now'))",
                (cur.lastrowid,),
            )
        return cur.lastrowid

    def get_due(self, limit: int = 20):
        rows = self.conn.execute(
            """SELECT c.id, c.front, c.back, c.video_id, c.start_time, c.end_time
                    FROM cards c JOIN card_review r ON r.card_id = c.id
                WHERE r.due_date <= datetime('now')
                ORDER BY r.due_date
                LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def apply_review(self, card_id: int, rating: str):
        row = self.conn.execute(
            "SELECT interval, ease, reps FROM card_review WHERE card_id = ?",
            (card_id,),
        ).fetchone()
        next_state = schedule(row["interval"], row["ease"], row["reps"], rating)
        with self.conn:
            self.conn.execute(
                """UPDATE card_review
                        SET interval = ?, ease = ?, reps = ?, due_date = ?
                    WHERE card_id = ?""",
                (
                    next_state["interval"],
                    next_state["ease"],
                    next_state["reps"],
                    next_state["due_date"],
                    card_id,
                ),
            )
        return next_state

    def reset_all(self) -> int:
        """Đưa mọi thẻ về trạng thái đầu: đến hạn ngay, interval/ease/reps về mặc định."""
        with self.conn:
            cur = self.conn.execute("""
                UPDATE card_review
                    SET due_date = datetime('now'), interval = 0,
                        ease = 2.5, reps = 0
            """)
        return cur.rowcount

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "CardStore":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()


#
# for row in SubtitleStore().get_videos("are you ok"):
#     print(
#         # print(row)
#         row["video_id"],
#     )
#
# res = SubtitleStore().get_text("iFkCMeEhs0Y")
# for r in res:
#     print(r["start_time"], r["end_time"], r["text"])
#     print(type(res))
