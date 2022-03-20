#!/bin/bash
cd $(dirname "$0")
cd ..

if [ $# -lt 1 ]; then
  echo "usage: docker-run.sh SERVER"
  exit 1
fi

SERVER=$1

SESSION_NAME=logana
PRO_DIR='$HOME/projects/hongbao-log'

ssh $SERVER "mkdir -p $PRO_DIR"
rsync -a ./* $SERVER:$PRO_DIR/ --exclude-from=.gitignore

ssh $SERVER "
tmux send-keys -t $SESSION_NAME:0.0 C-c C-m ;
sleep 1 ;
tmux send-keys -t $SESSION_NAME:0.0 'bash $PRO_DIR/scripts/docker-run.sh net configs/bjnj/log-net.json' C-m ;
"

ssh $SERVER "
tmux send-keys -t $SESSION_NAME:0.1 C-c C-m ;
sleep 1 ;
tmux send-keys -t $SESSION_NAME:0.1 'bash $PRO_DIR/scripts/docker-run.sh spb configs/bjnj/log-spb.json' C-m ;
"
