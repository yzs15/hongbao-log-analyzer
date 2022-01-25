#!/bin/bash
cd $(dirname "$0")
cd ..

if [ $# -lt 1 ]; then
  echo "usage: down-logs.sh SERVER"
  exit 1
fi

PRO_DIR='$HOME/projects/hongbao-log'

rsync -azP $1:$PRO_DIR/logs ./