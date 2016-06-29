#!/bin/bash
LOG_FILE="rssdl.log"

echo "$(date "+%Y-%m-%d %H:%M:%S,%3N") - INFO - rtorrent - Finished downloading: ${1}" >> $LOG_FILE
