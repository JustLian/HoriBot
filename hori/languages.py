import nextcord
from hori import db
from json import load
import os


langs = {}
for tf in filter(lambda x: x.endswith('.json'), os.listdir('./assets/languages')):
    with open(f'./assets/languages/{tf}', 'r') as f:
        tr = load(f)
        langs[tr['ID']] = tr
        print(f'Loaded {tr["ID"]} translation')


def tr(obj, key: str) -> str:
    if isinstance(obj, nextcord.Guild):
        id = obj.id
    elif isinstance(obj, nextcord.Interaction):
        id = obj.guild.id
    elif isinstance(obj, int):
        id = obj
    else:
        return 'UNKNOWN_OBJECT_TYPE'

    lang = db.get_server(id)['language']
    if lang not in langs:
        return 'UNKNOWN_LANGUAGE'

    return langs[lang].get(key, key)
