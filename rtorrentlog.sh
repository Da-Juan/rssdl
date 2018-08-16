#!/bin/bash
LOG_FILE="${HOME}/rssdl.log"

echo "$(date "+%Y-%m-%d %H:%M:%S,%3N") - INFO - rtorrent - Finished downloading: ${@}" >> "$LOG_FILE"
