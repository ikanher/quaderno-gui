"""
Zotero integration functions for QuadernoGUI.
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path


DEFAULT_STORAGE_DIR = Path.home() / 'Zotero' / 'storage'
DEFAULT_DB_PATH = Path.home() / 'Zotero' / 'zotero.sqlite'


def resolve_zotero_paths(storage_path=None, db_path=None):
    """Resolve Zotero storage and database paths using GUI-provided overrides."""
    storage_candidate = Path(storage_path).expanduser() if storage_path else DEFAULT_STORAGE_DIR
    db_candidate = Path(db_path).expanduser() if db_path else DEFAULT_DB_PATH

    if storage_candidate.is_dir() and storage_candidate.name != 'storage':
        nested_storage = storage_candidate / 'storage'

        if nested_storage.is_dir():
            storage_candidate = nested_storage

    db_candidate = db_candidate if db_candidate.suffix else db_candidate

    if db_candidate.is_dir():
        nested_db = db_candidate / 'zotero.sqlite'

        if nested_db.is_file():
            db_candidate = nested_db

    return storage_candidate, db_candidate

def get_full_collection_path(collection_id, collections):
    """
    Recursively build the full path for a collection given its id.
    """
    coll = collections.get(collection_id)

    if not coll:
        return ''

    parent = coll.get('parentCollectionID')

    if parent:
        parent_path = get_full_collection_path(parent, collections)

        if parent_path:
            return os.path.join(parent_path, coll['collectionName'])

    return coll['collectionName']

def build_zotero_file_mapping(storage_folder=None, db_path=None):
    """
    Build a mapping of remote file paths to local file details from Zotero.
    """
    storage_folder, db_path = resolve_zotero_paths(storage_folder, db_path)

    if not storage_folder.is_dir():
        nested_candidate = storage_folder / 'storage'

        if nested_candidate.is_dir():
            storage_folder = nested_candidate

    if not storage_folder.is_dir():
        raise FileNotFoundError(f'Zotero storage folder not found: {storage_folder}')

    if db_path.is_dir():
        possible_db = db_path / 'zotero.sqlite'

        if possible_db.is_file():
            db_path = possible_db

    if not db_path.is_file():
        raise FileNotFoundError(f'Zotero database not found: {db_path}')

    mapping = {}
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Get deleted collections.
    deleted_collections = set()
    try:
        cursor.execute('SELECT collectionID FROM deletedCollections')

        for row in cursor.fetchall():
            deleted_collections.add(row[0])
    except sqlite3.OperationalError:
        pass

    # Load collections (excluding deleted ones).
    cursor.execute('SELECT collectionID, collectionName, parentCollectionID FROM collections')
    collections = {}

    for row in cursor.fetchall():
        collectionID, collectionName, parentCollectionID = row

        if collectionID in deleted_collections:
            continue

        collections[collectionID] = {'collectionName': collectionName, 'parentCollectionID': parentCollectionID}

    # Query attachments (only PDFs and valid items).
    query = '''
        SELECT
          COALESCE(
            (SELECT MIN(ci.collectionID) FROM collectionItems ci WHERE ci.itemID = i.itemID),
            (SELECT MIN(ci2.collectionID) FROM collectionItems ci2 WHERE ci2.itemID = ia.parentItemID)
          ) as collectionID,
          i.itemID, i.key, i.dateModified, ia.contentType
        FROM items i
        JOIN itemAttachments ia ON i.itemID = ia.itemID
        WHERE i.itemTypeID = 3
          AND NOT EXISTS (
              SELECT 1 FROM deletedItems di
              WHERE di.itemID IN (i.itemID, ia.parentItemID)
          )
          AND ia.contentType LIKE 'application/pdf'
    '''
    cursor.execute(query)
    rows = cursor.fetchall()

    for row in rows:
        collectionID, itemID, key, dateModified, contentType = row

        if collectionID is None or collectionID not in collections:
            folder = 'Uncategorized'
        else:
            folder = get_full_collection_path(collectionID, collections)
            if not folder:
                folder = 'Uncategorized'

        source_dir = storage_folder / key

        if not source_dir.exists():
            continue

        pdf_files = [entry for entry in source_dir.iterdir() if entry.suffix.lower() == '.pdf']
        if not pdf_files:
            continue

        pdf_file = pdf_files[0]
        abs_path = pdf_file

        try:
            mod_time = datetime.strptime(dateModified, '%Y-%m-%d %H:%M:%S').timestamp()
        except Exception:
            mod_time = pdf_file.stat().st_mtime

        base = pdf_file.stem
        ext = pdf_file.suffix
        unique_filename = f'{base} (itemID {itemID}){ext}'
        remote_rel = (Path(folder.replace(os.sep, '/')) / unique_filename).as_posix()
        mapping[remote_rel] = {'abs_path': str(abs_path), 'mod_time': mod_time}

    conn.close()

    return mapping

def build_zotero_folder_set(db_path=None):
    """
    Build a set of folder paths from Zotero collections.
    """
    _, db_path = resolve_zotero_paths(db_path=db_path)

    if db_path.is_dir():
        possible_db = db_path / 'zotero.sqlite'

        if possible_db.is_file():
            db_path = possible_db

    if not db_path.is_file():
        raise FileNotFoundError(f'Zotero database not found: {db_path}')

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    deleted_collections = set()

    try:
        cursor.execute('SELECT collectionID FROM deletedCollections')
        for row in cursor.fetchall():
            deleted_collections.add(row[0])
    except sqlite3.OperationalError:
        pass

    cursor.execute('SELECT collectionID, collectionName, parentCollectionID FROM collections')
    folder_set = set()
    collections = {}

    for row in cursor.fetchall():
        collectionID, collectionName, parentCollectionID = row
        if collectionID in deleted_collections:
            continue
        collections[collectionID] = {'collectionName': collectionName, 'parentCollectionID': parentCollectionID}

    for collectionID in collections:
        folder = get_full_collection_path(collectionID, collections)
        if folder:
            folder_set.add(folder.replace(os.sep, '/'))

    conn.close()

    return folder_set
