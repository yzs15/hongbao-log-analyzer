FROM python:3.9

ENV PYTHONPATH=/hongbao-log

RUN pip3 install websockets requests pyzmq

COPY ./ /hongbao-log

CMD ["python3", "/hongbao-log/src/main.py"]