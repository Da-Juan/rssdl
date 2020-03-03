FROM debian:10

ENV DEBUG 0
ENV FEED_URL feed_me
ENV SKIP_SEASONS 0

VOLUME /root
VOLUME /Torrents

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install --no-install-recommends --no-install-suggests -y \
        python3 python3-pip python3-libtorrent python3-setuptools python3-wheel \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY rssdl.py .
COPY docker_cmd.sh .

CMD ./docker_cmd.sh
