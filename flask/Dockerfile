FROM ubuntu:20.04
RUN apt-get update
RUN apt-get install -y python3 python3-pip
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN mkdir /app
RUN mkdir -p /app/data
COPY service.py /app/service.py
ADD data /app/data
EXPOSE 5000
WORKDIR /app
ENTRYPOINT [ "python3", "-u", "service.py"]
