FROM python:3.9
  
ADD protorank /protorank
RUN pip install configargparse
