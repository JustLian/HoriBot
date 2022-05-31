from hori import db

d = db._connect_db()
c = d.cursor()
c.execute('''ALTER TABLE servers ADD COLUMN language TEXT DEFAULT "EN"''')
