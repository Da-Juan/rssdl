#!/usr/bin/env python3
"""
RSSdl Automatic torrent downloader for http://showrss.info/ RSS feed.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""
import feedparser
import libtorrent as lt
import logging
import os
import re
import requests
import shutil
import sys
import tempfile
from time import sleep
import yaml

feed_url = ''
torrents_dir = ''
debug = False
log_file = os.path.join(os.path.expanduser('~'), 'rssdl.log')
last_file = os.path.join(os.path.expanduser('~'), '.rssdl')


def readconfig():
    """Read configuration file and set global variables."""
    global feed_url, torrents_dir, debug

    config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'rssdl.yml')
    if not os.path.isfile(config_file):
        logger.error('Configuration file not found! (%s)', config_file)
        sys.exit(1)

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    feed_url = config.get('feed_url', '')
    if not feed_url:
        logger.error('feed_url is empty or not set in configuration file.')
        sys.exit(1)

    torrents_dir = os.path.expanduser(config.get('torrents_dir', ''))
    if not torrents_dir:
        logger.error('torrents_dir is empty or not set in configuration file.')
        sys.exit(1)
    if not os.path.exists(torrents_dir):
        try:
            os.mkdir(torrents_dir)
        except PermissionError:
            logger.error('Torrents directory does not exist (%s).', torrents_dir)
            sys.exit(1)
    elif not os.path.isdir(torrents_dir):
        logger.error('Torrents directory (%s) is not a directory.', torrents_dir)
        sys.exit(1)

    debug = config.get('debug', False)
    if not isinstance(debug, bool):
        debug = False


def magnet2torrent(magnet, output_dir):
    """
    Convert magnet link to Torrent file.

    Code from Daniel Folkes: https://github.com/danfolkes/Magnet2Torrent

    Args:
        magnet(str): The magnet link.
        output_dir(str): The path to write the Torrent file.

    Returns:
        str: The downloaded Torrent's filename.

    """
    global logger

    tempdir = tempfile.mkdtemp()
    session = lt.session()
    params = {
        'save_path': tempdir,
        'storage_mode': lt.storage_mode_t(2),
        'paused': False,
        'auto_managed': True,
        'duplicate_is_error': True
    }
    handle = lt.add_magnet_uri(session, magnet, params)

    logger.debug("Downloading Metadata...")
    while (not handle.has_metadata()):
        try:
            sleep(1)
        except KeyboardInterrupt:
            logger.debug('Aborting...')
            session.pause()
            logger.debug('Cleanup dir %s', tempdir)
            shutil.rmtree(tempdir)
            sys.exit(0)
    session.pause()

    torinfo = handle.get_torrent_info()
    torfile = lt.create_torrent(torinfo)

    filename = torinfo.name() + ".torrent"
    output = os.path.join(output_dir, filename)
    with open(output, "wb") as f:
        f.write(lt.bencode(torfile.generate()))
    logger.debug('Saved! Cleaning up dir: %s', tempdir)
    session.remove_torrent(handle)
    shutil.rmtree(tempdir)

    return filename


def downloadtorrent(url, output_dir, filename):
    """
    Download Torrent file.

    Args:
        url(str): The Torrent's URL.
        output_dir(str): The path to write the Torrent file.
        filename(str): The Torrent's filename.

    Returns:
        str: The downloaded Torrent's filename.

    """
    global logger

    # Set requests log level to WARNING
    logging.getLogger("requests").setLevel(logging.WARNING)

    r = requests.get(url)
    if r.status_code != requests.codes.ok:
        logger.error('Error %s while downloading %s. Exiting...', r.status_code, url)
        sys.exit(1)
    with open(os.path.join(output_dir, filename), 'wb') as f:
        f.write(r.content)

    return filename


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    logfileFormatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    logfileHandler = logging.FileHandler(log_file)
    logfileHandler.setFormatter(logfileFormatter)
    logger.addHandler(logfileHandler)

    if sys.stdout.isatty():
        logconsoleFormatter = logging.Formatter('%(levelname)s: %(message)s')
        logconsoleHandler = logging.StreamHandler()
        logconsoleHandler.setFormatter(logconsoleFormatter)
        logger.addHandler(logconsoleHandler)

    readconfig()

    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug('Starting in debug mode...')

    feed = feedparser.parse(feed_url)
    if feed.bozo == 1:
        logger.error(
            'Error parsing RSS feed: %s at line %s',
            feed.bozo_exception.getMessage(),
            feed.bozo_exception.getLineNumber()
        )
        sys.exit(1)

    if os.path.isfile(last_file):
        with open(last_file, 'r') as f:
            last_entry = f.read().strip('\n')
    else:
        logger.warning('File %s not found', last_file)
        last_entry = ''

    protocol_regex = re.compile('^(https?|magnet).*')
    for entry in feed.entries:
        if entry.id == last_entry:
            break
        match = protocol_regex.match(entry.link)
        if not match:
            logger.warning('Unknown protocol, skipping URL: %s', entry.link)
            continue
        if match.group(1).startswith('http'):
            torrent = downloadtorrent(entry.link, torrents_dir, re.sub(' ', '.', entry.tv_raw_title) + '.torrent')
        else:
            torrent = magnet2torrent(entry.link, torrents_dir)
        logger.info('Downloading: %s', torrent)

    # Save last entry's ID
    if last_entry != feed.entries[0].id:
        with open(last_file, 'w') as f:
            f.write('{0}\n'.format(feed.entries[0].id))
        logger.debug('New last_entry ID: %s', feed.entries[0].id)
    sys.exit(0)
