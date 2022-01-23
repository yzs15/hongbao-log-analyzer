#!/bin/bash
cd $(dirname "$0")
cd ..

if [ $# -lt 2 ]; then
  echo "usage: docker-run.sh ENV CONFIG"
  exit 1
fi

ENV=$1
CONFIG=$2

docker pull registry.cn-beijing.aliyuncs.com/zhengsj/hongbao:loganalyzer
docker stop loganalyzer-$ENV
docker rm loganalyzer-$ENV
docker run -it --name loganalyzer-$ENV \
   -v $HOME/projects/hongbao-log:/hongbao-log \
   registry.cn-beijing.aliyuncs.com/zhengsj/hongbao:loganalyzer \
   python3 /hongbao-log/src/main.py \
   $CONFIG