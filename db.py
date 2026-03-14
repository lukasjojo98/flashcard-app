from os import path
from sqlite3 import Error
import sqlite3
import random
from typing import List


def get_card_or_default(
    user_id: int, deck_id: int, ignored_card_ids: List[any] = None
) -> any:
    try:
        ROOT = path.dirname(path.realpath(__file__))
        conn = sqlite3.connect(path.join(ROOT, "decks.db"))
        db = conn.cursor()
        db.execute(
            "SELECT * FROM cards WHERE user_id = (?) AND deck_id = (?)",
            [user_id, deck_id],
        )
        conn.commit()
        cards = db.fetchall()

    except Error as e:
        print(e)

    return random.choice(cards) if cards else None
