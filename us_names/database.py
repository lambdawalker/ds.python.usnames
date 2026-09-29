"""Normalized version-2 SQLite storage."""
import json
import sqlite3
from pathlib import Path

SCHEMA_VERSION = 2

class Dataset:
    def __init__(self, path):
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError(f'{path}: download data with python -m us_names download first')
        self.connection = sqlite3.connect(self.path.resolve().as_uri() + '?mode=ro', uri=True)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute('PRAGMA foreign_keys=ON')
        if self.connection.execute('PRAGMA user_version').fetchone()[0] != SCHEMA_VERSION:
            self.close()
            raise ValueError('Dataset schema is incompatible; download a compatible release (schema 2)')

    def record(self, ident):
        r=dict(self.connection.execute('SELECT * FROM names WHERE id=?',(ident,)).fetchone())
        return {'id':r['id'],'source_text':r['name'],'role':r['role'],'national_count':r['total'],
            'source':r['source_id'],
            'group_counts':dict(self.connection.execute('SELECT group_id,count FROM name_group_counts WHERE name_id=?',(ident,))),
            'sex_counts':{x['sex']:{'count':x['count'],'share':x['share'],'source':x['source_id']} for x in self.connection.execute('SELECT * FROM name_sex_counts WHERE name_id=?',(ident,))},
            'origins':[dict(x) for x in self.connection.execute('SELECT label,evidence,source_id FROM name_origin_associations WHERE name_id=?',(ident,))]}

    def metadata(self):
        return {r[0]:json.loads(r[1]) for r in self.connection.execute('SELECT * FROM metadata')}
    def close(self):self.connection.close()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
