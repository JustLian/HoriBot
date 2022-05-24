import sqlite3
import json


def _connect_db() -> sqlite3.Connection:
    return sqlite3.connect('./hori/data.sqlite')


db = _connect_db()
cur = db.cursor()
cur.execute(f'''CREATE TABLE IF NOT EXISTS users (
    uId INT,
    osuId INT
)''')
cur.execute(f'''CREATE TABLE IF NOT EXISTS servers (
    id INT,
    music_channel INT,
    radio_enabled INT,
    shuffle INT,
    playlist_urls TEXT
)''')


def create_server(id) -> None:
    db = _connect_db()
    cur = db.cursor()

    cur.execute(f'''SELECT * FROM servers WHERE id = {id}''')
    data = cur.fetchone()
    if data is None:
        cur.execute(
            f'''INSERT INTO servers VALUES({id}, 0, 0, 0, "[]")''')
        db.commit()
    cur.close()
    db.close()


def delete_server(id) -> None:
    db = _connect_db()
    cur = db.cursor()

    cur.execute(f'''SELECT * FROM servers WHERE id = {id}''')
    data = cur.fetchone()
    if data is not None:
        cur.execute(
            f'''DELETE FROM servers WHERE id = {id}''')
        db.commit()
    cur.close()
    db.close()


def get_server(id) -> dict:
    db = _connect_db()
    cur = db.cursor()
    cur.execute(f'''SELECT * FROM servers WHERE id = {id}''')
    d = cur.fetchone()
    cur.close()
    db.close()
    return {'id': d[0], 'music_channel': d[1], 'radio_enabled': d[2], 'shuffle': d[3], 'playlist_urls': json.loads(d[4])}


def get_servers() -> list[int]:
    db = _connect_db()
    cur = db.cursor()
    cur.execute(f'''SELECT id FROM servers''')
    d = cur.fetchall()
    cur.close()
    db.close()
    return list(map(lambda x: x[0], d))


def update_server(id, *args) -> None:
    db = _connect_db()
    cur = db.cursor()
    for st in args:
        if type(st[1]) == int:
            val = st[1]
        elif type(st[1]) in [dict, list]:
            val = f"'{json.dumps(st[1])}'"
        elif type(st[1]) == str:
            val = f'"{st[1]}"'
        else:
            continue
        cur.execute(
            f'''UPDATE servers SET {st[0]} = {val} WHERE id = {id}''')
    db.commit()
    cur.close()
    db.close()
