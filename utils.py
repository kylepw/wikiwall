"""

    config.py
    ~~~~~~~~~

    Functions and values that all modules share.

"""

import os


# Source of Hi-Res images
SRC_URL = 'https://www.wikiart.org/?json=2&layout=new&param=high_resolution&layout=new&page={}'

# If only duplicate images returned, wait before trying next page of json data.
DUPLICATE_TIMEOUT = 3


def data_dir():
    """Return path to data directory. """

    xdg_data_home = os.environ.get(
        'XDG_DATA_HOME', os.path.join(os.path.expanduser('~'), '.local/share')
    )
    path = os.path.join(xdg_data_home, 'wikiwall')

    if not os.path.exists(path):
        os.makedirs(path)

    return path
