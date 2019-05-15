"""

db.py
~~~~~

Sqlite3 database wrapper for download history.

The database stores information on downloaded images to prevent
downloading images more than once.


"""

import logging
import os.path
import sqlite3

from utils import data_dir


logger = logging.getLogger(__name__)


class DownloadDatabase:
    """Configure and establish connection to tweet database.

    Note:
        This class acts as a context manager.

    Args:
        db_filename (`str`, optional): filename of database

    """

    def __init__(
        self, db_filename=os.path.join(data_dir(), 'wikiwall.db'), tablename='downloads'
    ):
        self.db_filename = db_filename
        self.tablename = tablename

    def __enter__(self):
        self._connect()
        self._create_table()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def _connect(self):
        """Connect to database. """
        try:
            self.conn = sqlite3.connect(self.db_filename)
        except sqlite3.Error:
            logger.exception('Failed to connect to database!')

    def _create_table(self):
        """Create a table for image data if it does not exist.

        Args:
            name (`str`, optional): name of table

        """
        query = '''
            CREATE TABLE IF NOT EXISTS {} (
                id integer PRIMARY KEY,
                url text NOT NULL UNIQUE)
            '''.format(
            self.tablename
        )

        self.conn.execute(query)

    def add(self, url):
        """Add image url to database.

        Args:
            url (str): image url

        Raises:
            sqlite3.IntegrityError: If data already exists in database.

        """
        record_sql = '''
            INSERT INTO {} (url)
            VALUES (?)
        '''.format(
            self.tablename
        )
        try:
            with self.conn:
                self.conn.execute(record_sql, (url,))
        except sqlite3.IntegrityError:
            logger.exception('Already tweeted %s!', url)

    def is_duplicate(self, url):
        """Check if `url` already exists in database.

        Args:
            url(`str`): url of image

        """
        dupl_check_sql = '''
            SELECT url FROM {} WHERE url=?
        '''.format(
            self.tablename
        )
        with self.conn:
            return self.conn.execute(dupl_check_sql, (url,)).fetchone()
