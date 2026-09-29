"""Download a versioned database release; generation itself never uses the network."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import os
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
import urllib.request
from .database import Dataset

DEFAULT_RELEASE = 'dataset-v0.2.0'
RELEASE_BASE_URL = 'https://github.com/lambdawalker/ds.source.usnames/releases/download'


def _download(url, path):
    request = urllib.request.Request(url, headers={'User-Agent': 'us-synthetic-names/0.3.0'})
    with urllib.request.urlopen(request, timeout=120) as response, path.open('wb') as target:
        shutil.copyfileobj(response, target)


def download_dataset(output='data/names.sqlite', *, release=DEFAULT_RELEASE):
    """Verify, decompress and install a schema-2 release. Refuses existing output.

    Returns a Path. Pin ``release`` for reproducibility; no implicit latest lookup.
    SHA-256 is checked against the checksum asset served by the same release.
    A failed download, checksum or database check leaves no destination file.
    """
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', release):
        raise ValueError('Invalid release tag')
    output = Path(output)
    if output.exists():
        raise FileExistsError(f'{output} already exists; reuse it or choose a new output path')
    output.parent.mkdir(parents=True, exist_ok=True)
    base = f'{RELEASE_BASE_URL}/{release}'
    with tempfile.TemporaryDirectory(prefix='.usnames-', dir=output.parent) as tmp:
        tmp = Path(tmp)
        checksums = tmp / 'SHA256SUMS'
        archive = tmp / 'names.sqlite.gz'
        staged = tmp / 'names.sqlite'
        _download(f'{base}/SHA256SUMS', checksums)
        expected = []
        for line in checksums.read_text().splitlines():
            fields = line.split()
            if len(fields) == 2 and fields[1].lstrip('*') == archive.name:
                expected.append(fields[0].lower())
        if len(expected) != 1 or not re.fullmatch('[0-9a-f]{64}', expected[0]):
            raise ValueError('Release checksum for names.sqlite.gz is missing or invalid')
        _download(f'{base}/{archive.name}', archive)
        digest = hashlib.sha256()
        with archive.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        if digest.hexdigest() != expected[0]:
            raise ValueError('Database release checksum mismatch')
        with gzip.open(archive, 'rb') as stream, staged.open('wb') as target:
            shutil.copyfileobj(stream, target)
        try:
            with Dataset(staged) as db:
                if db.connection.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                    raise ValueError('Downloaded database failed integrity check')
                db.metadata()
        except sqlite3.DatabaseError as error:
            raise ValueError('Downloaded release is not a valid names database') from error
        # Same filesystem: atomic, and never replaces an existing destination.
        os.link(staged, output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='data/names.sqlite')
    parser.add_argument('--release', default=DEFAULT_RELEASE)
    args = parser.parse_args()
    try:
        print(download_dataset(args.output, release=args.release))
    except (OSError, ValueError) as error:
        parser.exit(2, f'Error: {error}\n')


if __name__ == '__main__':
    main()
