docker build -t registry.cn-beijing.aliyuncs.com/zhengsj/hongbao:loganalyzer .
docker push registry.cn-beijing.aliyuncs.com/zhengsj/hongbao:loganalyzer


docker pull registry.cn-beijing.aliyuncs.com/zhengsj/hongbao:loganalyzer

docker stop loganalyzer
docker rm loganalyzer
docker run -it --name loganalyzer \
   registry.cn-beijing.aliyuncs.com/zhengsj/hongbao:loganalyzer \
   python3 /hongbao-log/src/main.py \
   log-spb.json



docker pull registry.cn-beijing.aliyuncs.com/zhengsj/hongbao:loganalyzer
docker stop loganalyzer
docker rm loganalyzer
docker run -it --name loganalyzer \
   registry.cn-beijing.aliyuncs.com/zhengsj/hongbao:loganalyzer \
   python3 /hongbao-log/src/main.py \
   log-net.json

