# RSSdl
Automatic torrent downloader for http://showrss.info/ RSS feed

## Foreword
I'm not a developer, I've written this program to learn about python and for the pleasure to build something myself.

So this code is probably far from perfect but if you want to comment it or improve it, feel free to do it and please explain me how and why :)

## Requirements
RSSdl requires python3 and a few libraries:
* ConfigArgParse
* feedparser
* python-libtorrent
* requests

## Installation

### Virtual environment

```
python3 -m virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
```

Libtorrent's python bindings are not available on PyPI so we need to install them system wide and do a little hack.

```
apt install python3-libtorrent
ln -s /usr/lib/python3/dist-packages/libtorrent*.so <path_to_virtualenv>/lib/python<version>/site-packages/
```

To run rssdl from the virtual environment without activating use:
```
<path_to_virtualenv>/venv/bin/python rssdl.py
```

### Simple install
Install these packages on Debian/Ubuntu:

```
apt install python3 python3-configargparse python3-libtorrent python3-requests python3-feedparser
```

## Usage

```
usage: rssdl.py [-h] [-c CONFIG_FILE] -t TORRENTS_DIR -f FEED_URL [-d]

Args that start with '--' (eg. -t) can also be set in a config file
(<path_to_rssdl>/rssdl.conf or specified via -c). Config file syntax allows:
key=value, flag=true, stuff=[a,b,c] (for details, see syntax at
https://goo.gl/R74nmi). If an arg is specified in more than one place, then
commandline values override config file values which override defaults.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        Config file path.
  -t TORRENTS_DIR, --torrents-dir TORRENTS_DIR
                        Path to write Torrents files.
  -f FEED_URL, --feed-url FEED_URL
                        URL to your personal showRSS feed.
  -d, --debug           Run in debug mode.
```

Copy rssdl.conf.example to rssdl.conf and configure your personal feed URL and the directory where you want the torrents to be saved.

To download the torrents you can use [rtorrent](https://github.com/rakshasa/rtorrent) and configure it to watch `torrents_dir`.

You can run rssdl.py automatically from a cron, it will write a log file, rssdl.log, in the home directory of the user who is running it.

### Bonus
If you want to see a list of the new downloaded files in you message of the day next time you log in, put **60-rssdl** in **/etc/update-motd.d/** and configure `FINISHED_DIR`.

## License
All code is licensed under the [GPL version 3](http://www.gnu.org/licenses/gpl.html)
