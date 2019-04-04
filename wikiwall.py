'''
    wikiwall.py
    ~~~~~~~~~~~

    Downloads a random image from Wikiart's Hi-Res page
    and sets it as the desktop background in macOS.

'''

import click
import logging
from logging.handlers import RotatingFileHandler
import os
import os.path
import random
import requests
import subprocess
import sys
import time
from tqdm import tqdm


logger = logging.getLogger(__name__)


# Source of Hi-Res images
SRC_URL = 'https://www.wikiart.org/?json=2&layout=new&param=high_resolution'


def config_logger(debug, path=None):
    ''' Configure module logger.'''

    if path is not None:
        logfile = os.path.join(path, __name__ + '.log')
    else:
        logfile = os.path.join(os.getcwd(), __name__ + '.log')

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '''
        %(asctime)s %(name)-12s %(levelname)-8s %(message)s
    '''
    )

    # Push logs to stdout.
    if debug:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    # Add logfile with 10MB limit
    rh = RotatingFileHandler(filename=logfile, maxBytes=10485760, backupCount=10)
    rh.setLevel(logging.WARNING)
    rh.setFormatter(formatter)
    logger.addHandler(rh)


def data_dir():
    '''Return path to data directory.'''

    xdg_data_home = os.environ.get(
        'XDG_DATA_HOME', os.path.join(os.path.expanduser('~'), '.local/share')
    )
    path = os.path.join(xdg_data_home, 'wikiwall')

    if not os.path.exists(path):
        os.makedirs(path)

    return path


def get_random(iterator, k=1):
    '''Get random sample of items in iterator.

    Args:
        iterator: any iterator you want random samples from.
        k: number of samples to return.

    Note:
        Warning log if `k` is less than size of the iterator. Not
        an issue inside this function because max num of iterations
        will be number of items in `iterator`, not `k`, but could be
        one if you expect size of `results` to always equal to `k`.

    Returns:
        results: List of random items from iterator. Number of items
        is `k` or number of items in `iterator` if `k` is larger than
        the total number of items.

    '''
    results = []

    for i, item in enumerate(iterator):
        if i < k:
            results.append(item)
        else:
            s = int(random.random() * i)
            if s < k:
                results[s] = item

    if len(results) < k:
        logger.warning('Size of iterator (%s) is less than k (%s)', len(results), k)

    return results


def scrape_urls(src_url):
    '''Scrape jpg urls.

    Args:
        src_url: URL to scrape.

    Raises:
        Any typical Requests exceptions.

    Yields:
        Parsed url results in string format.

    '''
    # Exceptions raised here if connection issue arises
    r = requests.get(src_url)
    r.raise_for_status()

    data = r.json().get('Paintings')

    if data is not None:
        for obj in data:
            yield obj.get('image', '')
    else:
        yield ''


def download_img(url, dest=None):
    '''Download img from url.

    Args:
        url: url of image file.
        dest: where to download file. Default is current directory.

    Raises:
        TypeError: if url or dest aren't strings.

    Returns:
        path: local path to downloaded file.

    '''
    if not isinstance(url, str):
        raise TypeError(f'url must be type str, not {type(url)}')
    if dest and not isinstance(dest, str):
        raise TypeError(f'dest must be type str, not {type(dest)}')

    if not dest:
        dest = os.getcwd()
    if not os.path.exists(dest) or not os.path.isdir(dest):
        os.makedirs(dest)

    filename = url.split('/')[-1]
    path = os.path.join(dest, filename)

    # download the sucker
    with requests.get(url, stream=True) as r, open(path, 'wb') as f:
        file_sz = int(r.headers['content-length'])
        chunk_sz = 1024
        print(f'Downloading {filename}...')
        for chunk in tqdm(
            iterable=r.iter_content(chunk_sz),
            total=int(file_sz / chunk_sz),
            unit_scale=True,
            unit='KB',
        ):
            f.write(chunk)

    logger.info('%s downloaded to %s', filename, dest)

    return path


def _clean_dls(limit, path=None):
    ''' Check that number of images saved so far is no more than `limit`.

    Args:
        limit: maximum number of downloads allowed in download directory.
        path: path to saved images. Default to current working directory.

    Raises:
        ValueError: if `limit` is not an positive integer.

    '''
    if not isinstance(limit, int) or limit < 0:
        raise ValueError('`limit` must be a positive integer.')

    if path is None:
        path = os.getcwd()

    # collect jpg file paths
    jpegs = []
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)):
            if f.lower().endswith('.jpg'):
                jpegs.append(os.path.join(path, f))

    # check if limit exceeded
    if len(jpegs) > limit:

        logger.info('%s jpeg files in %s', len(jpegs), path)
        logger.info('Cleaning...')

        # sort by modification time, oldest to newest
        jpegs.sort(key=os.path.getmtime)

        while len(jpegs) > limit:
            f = jpegs.pop(0)
            os.remove(f)
            logger.info('%s removed.', f)


def _run_appscript(script):
    '''Execute Applescript. '''

    try:
        subprocess.run(
            ['/usr/bin/osascript', '-'],
            input=script.encode(),
            stderr=subprocess.PIPE,
            check=True,
        )

    except subprocess.CalledProcessError as err:
        raise ValueError(err.stderr.decode())


@click.group(invoke_without_command=True)
@click.option('--dest', help='Download images to specified destination.')
@click.option(
    '--limit',
    default=10,
    help='''
        Number of files to keep in download directory. Set to -1 for no limit. Default is 10.
    ''',
)
@click.option('--debug', is_flag=True, help='Show debugging messages.')
@click.pass_context
def cli(ctx, dest, limit, debug):
    '''Set desktop background in macOS to random WikiArt image.'''

    DATA_DIR = data_dir()

    config_logger(debug, path=DATA_DIR)

    if debug:
        print('Debug mode is on.')
    if dest is None:
        dest = DATA_DIR
    logger.info('Destination set to %s', dest)

    # Setup context passed to subcommands.
    ctx.ensure_object(dict)
    ctx.obj['DEST'] = dest

    # Skip below if subcommand `show` invoked.
    if ctx.invoked_subcommand == 'show':
        return

    try:
        # Retrieve random hi-res image.
        print('Searching for image...')
        url = get_random(scrape_urls(SRC_URL))[0]
        saved_img = download_img(url, dest)

        # Clean out DL directory if limit reached.
        if limit != -1:
            logger.info('Download limit set to %s.', limit)
            _clean_dls(limit, path=dest)
        else:
            logger.info('No download limit set. Skipping cleaning.')

        # Set image as desktop background.
        setwall_script = f'''
            tell application "System Events"
                tell every desktop
                    set picture to "{saved_img}"
                end tell
            end tell
        '''

        print('Setting background... ', end='')
        _run_appscript(setwall_script)

        sys.stdout.flush()
        time.sleep(1)
        print('done.')
        time.sleep(0.2)

    except Exception:
        logger.exception('Something went wrong.')
        print('Something went wrong. Check the logs.')
        sys.exit(1)


@cli.command()
@click.pass_context
def show(ctx):
    '''Show previous downloads in Finder.'''

    open_script = f'''
    tell application "Finder"
        open POSIX file "{ctx.obj['DEST']}"
    end tell
    '''
    _run_appscript(open_script)


if __name__ == '__main__':
    try:
        cli(obj={})
    except KeyboardInterrupt:
        print('\nSee you!')
