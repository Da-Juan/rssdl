# RSSdl
Automatic torrent downloader for http://showrss.info/ RSS feed

## Foreword
I'm not a developer, I've written this program to learn about python and for the pleasure to build something myself.

So this code is probably far from perfect but if you want to comment it or improve it, feel free to do it and please explain me how and why :)

## Requirements
RSSdl requires python3 and a few libraries:
* feedparser
* python-libtorrent
* PyYAML
* requests

To install these libraries on Debian/Ubuntu:
```
apt-get install python3 python3-yaml python3-libtorrent python3-requests python3-feedparser
```

## Usage
Edit rssdl.yml and configure your personal feed URL and the directory where you want the torrents to be saved.

To download the torrents you can use [rtorrent](https://github.com/rakshasa/rtorrent) and configure it to watch `torrents_dir`.

You can run rssdl.py automatically from a cron, it will write a log file, rssdl.log, in the home directory of the user who is running it.

### Bonus
If you want to see a list of the new downloaded files in you message of the day next time you log in, put **60-rssdl** in **/etc/update-motd.d/** and configure `FINISHED_DIR`.

## License
All code is licensed under the [GPL version 3](http://www.gnu.org/licenses/gpl.html)
