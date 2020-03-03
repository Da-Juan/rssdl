#!/bin/bash
CONFIG="/root/rssdl.conf"

export TORRENTS_DIR="/Torrents"

if [[ ! -f "$CONFIG" && "$FEED_URL" == "feed_me" ]]; then
	echo "Please provide a feed URL using FEED_URL environment variable."
	exit 1
fi
if [[ ! -f "$CONFIG" ]]; then
	RSSDL_ARGS=( "-w" "$CONFIG" )
else
	unset FEED_URL
	RSSDL_ARGS=( "-c" "$CONFIG" )
fi

python3 -W ignore rssdl.py "${RSSDL_ARGS[@]}"
