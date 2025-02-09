"""
Zotero integration functions for QuadernoGUI.
"""

import os
import sqlite3
from datetime import datetime

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

def build_zotero_file_mapping():
    """
    Build a mapping of remote file paths to local file details from Zotero.
    """
    storage_folder = os.path.expanduser('~/Zotero/storage')
    db_path = os.path.expanduser('~/Zotero/zotero.sqlite')
    mapping = {}
    conn = sqlite3.connect(db_path)
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

        source_dir = os.path.join(storage_folder, key)

        if not os.path.exists(source_dir):
            continue

        pdf_files = [f for f in os.listdir(source_dir) if f.lower().endswith('.pdf')]
        if not pdf_files:
            continue

        pdf_file = pdf_files[0]
        abs_path = os.path.join(source_dir, pdf_file)

        try:
            mod_time = datetime.strptime(dateModified, '%Y-%m-%d %H:%M:%S').timestamp()
        except Exception:
            mod_time = os.path.getmtime(abs_path)

        base, ext = os.path.splitext(pdf_file)
        unique_filename = f'{base} (itemID {itemID}){ext}'
        remote_rel = os.path.join(folder, unique_filename).replace(os.sep, '/')
        mapping[remote_rel] = {'abs_path': abs_path, 'mod_time': mod_time}

    conn.close()

    return mapping

def build_zotero_folder_set():
    """
    Build a set of folder paths from Zotero collections.
    """
    db_path = os.path.expanduser('~/Zotero/zotero.sqlite')
    conn = sqlite3.connect(db_path)
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
