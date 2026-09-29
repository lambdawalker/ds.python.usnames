import gzip
import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import us_names


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.assets = self.root / 'releases' / 'dataset-v0.2.0'
        self.assets.mkdir(parents=True)
        db = self.root / 'input.sqlite'
        with sqlite3.connect(db) as c:
            c.executescript('PRAGMA user_version=2; CREATE TABLE metadata(key TEXT, value TEXT);')
        self.raw = db.read_bytes()
        self.asset(gzip.compress(self.raw))

    def asset(self, data, digest=None):
        (self.assets / 'names.sqlite.gz').write_bytes(data)
        (self.assets / 'SHA256SUMS').write_text(f'{digest or hashlib.sha256(data).hexdigest()}  names.sqlite.gz\n')

    def download(self, name='out.sqlite'):
        self.assertTrue(hasattr(us_names, 'download_dataset'), 'Library must expose release download API')
        with patch('us_names.download.RELEASE_BASE_URL', (self.root / 'releases').as_uri()):
            return us_names.download_dataset(self.root / name)

    def test_verified_download_opens_with_reader(self):
        target = self.download()
        self.assertEqual(target.read_bytes(), self.raw)
        with us_names.Dataset(target) as db:
            self.assertEqual(db.metadata(), {})

    def test_bad_checksum_leaves_no_database(self):
        self.asset(gzip.compress(self.raw), '0' * 64)
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.download()
        self.assertFalse((self.root / 'out.sqlite').exists())
        self.assertFalse(list(self.root.glob('.usnames-*')))

    def test_wrong_schema_leaves_no_database(self):
        db = self.root / 'wrong.sqlite'
        with sqlite3.connect(db) as c:
            c.execute('PRAGMA user_version=1')
        self.asset(gzip.compress(db.read_bytes()))
        with self.assertRaisesRegex(ValueError, 'schema'):
            self.download()
        self.assertFalse((self.root / 'out.sqlite').exists())

    def test_existing_database_is_not_overwritten(self):
        target = self.root / 'out.sqlite'
        target.write_bytes(b'existing')
        with self.assertRaises(FileExistsError):
            self.download()
        self.assertEqual(target.read_bytes(), b'existing')

    def test_reader_prevents_persistent_writes_but_allows_cohort_temp_tables(self):
        target = self.download()
        with us_names.Dataset(target) as db:
            with self.assertRaises(sqlite3.OperationalError):
                db.connection.execute('CREATE TABLE unexpected(id INTEGER)')
            db.connection.execute('CREATE TEMP TABLE cohort_test(id INTEGER)')
