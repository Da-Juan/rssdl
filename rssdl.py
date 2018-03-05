#!/usr/bin/env python3
'''
    RSSdl Automatic torrent downloader for http://showrss.info/ RSS feed

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
'''
import feedparser
import libtorrent as lt
import logging
from os import path
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
log_file = path.join(path.expanduser('~'), 'rssdl.log')
last_file = path.join(path.expanduser('~'), '.rssdl')

def is_true(string):
    if re.match('[Tt]rue', string):
        return True
    elif re.match('[Ff]alse', string):
        return False
    else:
        return None

def readconfig():
    global feed_url, torrents_dir, debug

    config_file = path.join(path.dirname(path.realpath(__file__)), 'rssdl.yml')
    if not path.isfile(config_file):
        print('ERROR: configuration file not found! ({0})'.format(config_file))
        sys.exit(1)
    else:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        try:
            config['feed_url']
        except KeyError:
            print('ERROR: feed_url is not set in configuration file.')
            sys.exit(1)
        else:
            feed_url = config['feed_url']

        try:
            config['torrents_dir']
        except KeyError:
            print('ERROR: torrents_dir is not set in configuration file.')
            sys.exit(1)
        else:
            if not path.isdir(config['torrents_dir']):
                print('ERROR: {0} is not a '
                        'directory.'.format(config['torrents_dir']))
                sys.exit(1)
            else:
                if config['torrents_dir'][:1] == '~':
                    torrents_dir = path.join(path.expanduser('~'), re.sub('^/',
                        '', config['torrents_dir'][2:]))
                else:
                    torrents_dir = config['torrents_dir']

        try:
            config['debug']
        except KeyError:
            pass
        else:
            debug = is_true(str(config['debug']))

def magnet2torrent(magnet, output_dir):
    '''
    Convert magnet link to torrent file and write it in output_dir
    Return the torrent filename

    Code from Daniel Folkes: https://github.com/danfolkes/Magnet2Torrent
    '''

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
            print("Aborting...")
            session.pause()
            print("Cleanup dir " + tempdir)
            shutil.rmtree(tempdir)
            sys.exit(0)
    session.pause()

    torinfo = handle.get_torrent_info()
    torfile = lt.create_torrent(torinfo)

    filename = torinfo.name() + ".torrent"
    output = path.join(output_dir, filename)
    torcontent = lt.bencode(torfile.generate())
    with open(output, "wb") as f:
        f.write(lt.bencode(torfile.generate()))
    logger.debug("Saved! Cleaning up dir: " + tempdir)
    session.remove_torrent(handle)
    shutil.rmtree(tempdir)

    return filename

def downloadtorrent(url, output_dir, filename):
    '''
    Download torrent file and save it in output_dir
    Return the torrent filename
    '''

    global logger

    # Set requests log level to WARNING
    logging.getLogger("requests").setLevel(logging.WARNING)

    r = requests.get(url)
    if r.status_code == requests.codes.ok:
        with open(path.join(output_dir, filename), 'wb') as f:
            f.write(r.content)

        return filename
    else:
        logger.error('Error {0} while downloading file {1}'
                'Exiting...'.format(r.status_code, url))
        sys.exit(1)

if __name__ == '__main__':
    logging.basicConfig(filename = log_file, format = '%(asctime)s - '
            '%(levelname)s - %(module)s - %(message)s', level = logging.INFO)
    logger = logging.getLogger(__name__)

    readconfig()

    if debug == True:
        logger.setLevel(logging.DEBUG)
        logger.debug('Starting in debug mode...')


    feed = feedparser.parse(feed_url)
    if feed.bozo == 1:
        logger.error('Error parsing RSS feed: {0} at line '
                '{1}'.format(feed.bozo_exception.getMessage(),
                    feed.bozo_exception.getLineNumber()))
        sys.exit(1)

    if path.isfile(last_file):
        with open(last_file, 'r') as f:
            last_entry = f.read().strip('\n')
    else:
        logger.warning('File {0} not found'.format(last_file))
        last_entry = ''
    i = 0
    while feed.entries[i].id != last_entry:
        if feed.entries[i].link.split(':',1)[:1][0] == 'magnet':
            logger.info('Downloading: '
                    '{0}'.format(magnet2torrent(feed.entries[i].link,
                        torrents_dir)))
        elif re.match('^https?.*\.torrent$', feed.entries[i].link):
            logger.info('Downloading: '
                    '{0}'.format(downloadtorrent(feed.entries[i].link,
                        torrents_dir, re.sub(' ', '.',
                            feed.entries[i].tv_raw_title) + '.torrent')))
        else:
            logger.warning('Skipping unknown URL: '
                    '{0}'.format(feed.entries[i].link))
        i += 1
        if i == len(feed.entries):
            break

    # Save last entry's ID
    if last_entry != feed.entries[0].id:
        with open(last_file, 'w') as f:
            f.write('{0}\n'.format(feed.entries[0].id))
        logger.debug('New last_entry ID: {0}'.format(feed.entries[0].id))
    sys.exit(0)
