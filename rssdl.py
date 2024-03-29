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

import logging
import os
import re
import shutil
import sys
import tempfile
from time import sleep

import configargparse

import feedparser

import libtorrent as lt

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(HERE, "rssdl.conf")
LOG_FILE = os.path.join(os.path.expanduser("~"), "rssdl.log")
LAST_FILE = os.path.join(os.path.expanduser("~"), ".rssdl")


class FullPaths(configargparse.Action):
    """Expand user- and relative-paths."""

    def __call__(self, parser, namespace, values, option_string=None):
        """Expand user- and relative-paths."""
        setattr(namespace, self.dest, os.path.abspath(os.path.expanduser(values)))


def is_writable_dir(dirname):
    """Check if a path is a writable directory."""
    if not os.path.isdir(dirname):
        msg = "{0} is not a directory".format(dirname)
        raise configargparse.ArgumentTypeError(msg)
    if not os.access(dirname, os.W_OK):
        msg = "{0} is not writable".format(dirname)
        raise configargparse.ArgumentTypeError(msg)
    else:
        return dirname


def magnet2torrent(magnet, output_path):
    """
    Convert magnet link to Torrent file.

    Code from Daniel Folkes: https://github.com/danfolkes/Magnet2Torrent

    Args:
        magnet(str): The magnet link.
        output_path(str): The absolute path to write the Torrent file.

    """
    global logger

    tempdir = tempfile.mkdtemp()
    session = lt.session()
    params = lt.parse_magnet_uri(magnet)
    params.save_path = tempdir
    handle = session.add_torrent(params)

    logger.debug("Downloading Metadata...")
    while not handle.status().has_metadata:
        try:
            sleep(1)
        except KeyboardInterrupt:
            logger.debug("Aborting...")
            session.pause()
            logger.debug("Cleanup dir %s", tempdir)
            shutil.rmtree(tempdir)
            sys.exit(0)
    session.pause()

    torinfo = handle.torrent_file()
    torfile = lt.create_torrent(torinfo)

    with open(output_path, "wb") as f:
        f.write(lt.bencode(torfile.generate()))
    logger.debug("Saved! Cleaning up dir: %s", tempdir)
    session.remove_torrent(handle)
    shutil.rmtree(tempdir)


def downloadtorrent(url, output_path):
    """
    Download Torrent file.

    Args:
        url(str): The Torrent's URL.
        output_path(str): The absolute path to write the Torrent file.

    """
    global logger

    # Set requests log level to WARNING
    logging.getLogger("requests").setLevel(logging.WARNING)

    r = requests.get(url)
    if r.status_code != requests.codes.ok:
        logger.error("Error %s while downloading %s. Exiting...", r.status_code, url)
        sys.exit(1)
    with open(output_path, "wb") as f:
        f.write(r.content)


def fetch_torrents(entries, skip_seasons=False):
    """
    Browse feed entries and fetch new torrents.

    Args:
        entries(list): The feed entries.
        skip_seasons(bool): Do not download full seasons.

    """
    global logger

    if os.path.isfile(LAST_FILE):
        with open(LAST_FILE, "r") as f:
            last_entry = f.read().strip("\n")
    else:
        logger.warning("File %s not found", LAST_FILE)
        last_entry = ""

    protocol_regex = re.compile("^(https?|magnet).*")
    season_regex = re.compile(r"^.*\.[sS][0-9]+\.(?![Ee][0-9]+).*")
    for entry in entries:
        if entry.id == last_entry:
            break
        protocol_match = protocol_regex.match(entry.link)
        if not protocol_match:
            logger.warning("Unknown protocol, skipping URL: %s", entry.link)
            continue
        filename = entry.title.replace(" ", ".") + ".torrent"
        season_match = season_regex.match(filename)
        if season_match and skip_seasons:
            logger.debug("Skipping full season: %s", filename)
            continue
        torrent_path = os.path.join(options.torrents_dir, filename)
        if protocol_match.group(1).startswith("http"):
            downloadtorrent(entry.link, torrent_path)
        else:
            magnet2torrent(entry.link, torrent_path)
        logger.info("Downloading: %s", filename)

    # Save last entry's ID
    if last_entry != entries[0].id:
        with open(LAST_FILE, "w") as f:
            f.write("{0}\n".format(entries[0].id))
        logger.debug("New last_entry ID: %s", entries[0].id)


def setup_logging():
    """Set up logging."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    logfileFormatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(module)s - %(message)s"
    )
    logfileHandler = logging.FileHandler(LOG_FILE)
    logfileHandler.setFormatter(logfileFormatter)
    logger.addHandler(logfileHandler)

    if sys.stdout.isatty():
        logconsoleFormatter = logging.Formatter("%(levelname)s: %(message)s")
        logconsoleHandler = logging.StreamHandler()
        logconsoleHandler.setFormatter(logconsoleFormatter)
        logger.addHandler(logconsoleHandler)
    return logger


def parse_arguments():
    """Parse command-line arguments."""
    parser = configargparse.ArgParser(default_config_files=[CONFIG_FILE])
    parser.add_argument(
        "-c", "--config-file", is_config_file=True, help="Config file path."
    )
    parser.add_argument(
        "-t",
        "--torrents-dir",
        action=FullPaths,
        required=True,
        type=is_writable_dir,
        help="Path to write Torrents files.",
    )
    parser.add_argument(
        "-f", "--feed-url", required=True, help="URL to your personal showRSS feed."
    )
    parser.add_argument(
        "-s",
        "--skip-seasons",
        action="store_true",
        default=False,
        help="Do not download full seasons.",
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Run in debug mode.")
    return parser.parse_args()


if __name__ == "__main__":
    logger = setup_logging()
    options = parse_arguments()

    if options.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Starting in debug mode...")

    feed_request = requests.get(options.feed_url, allow_redirects=True)
    if feed_request.status_code != 200:
        logger.error("Error downloading feed(%s)", feed_request.status_code)
        sys.exit(1)
    parsed_feed = feedparser.parse(feed_request.text)
    if parsed_feed.bozo == 1:
        try:
            logger.error(
                "Error parsing RSS feed: %s at line %s",
                parsed_feed.bozo_exception.getMessage(),
                parsed_feed.bozo_exception.getLineNumber(),
            )
        except AttributeError:
            logger.error("Error parsing RSS feed")
        sys.exit(1)

    fetch_torrents(parsed_feed.entries, options.skip_seasons)
    logger.debug("Job done, bye!")
