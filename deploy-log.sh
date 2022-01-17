docker build -t registry.cn-beijing.aliyuncs.com/zhengsj/hongbao:loganalyzer .

docker pull registry.cn-beijing.aliyuncs.com/zhengsj/hongbao:loganalyzer

docker stop loganalyzer
docker rm loganalyzer
docker run -it --name loganalyzer \
   registry.cn-beijing.aliyuncs.com/zhengsj/hongbao:loganalyzer \
   python3 /hongbao-log/src/main.py \
   192.168.143.3:8082 \
   tcp://192.168.143.3:8081



docker stop loganalyzer
docker rm loganalyzer
docker run -it --name loganalyzer \
   registry.cn-beijing.aliyuncs.com/zhengsj/hongbao:loganalyzer \
   python3 /hongbao-log/src/main.py \
   172.16.32.14:8082 \
   tcp://172.16.32.14:8081

