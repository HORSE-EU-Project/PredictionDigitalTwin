FROM ubuntu

RUN apt-get update && apt-get -y upgrade 
RUN apt install -y build-essential
RUN apt install -y python3
RUN apt install -y python3-pip
RUN apt install -y iputils-ping
RUN apt install -y net-tools
RUN apt install -y autoconf
RUN apt install -y bash bash-completion
RUN apt install -y iproute2 iperf3

RUN apt install -y stress-ng curl tcpdump netcat-openbsd
RUN apt-get update && apt-get upgrade -y

# install required software
# * TWAMP
COPY ./twamp/twamp.py /home/twamp.py
# * iperf
RUN pip install iperf3
COPY ./iperf3/client.py /home/iperf-client.py
COPY ./iperf3/server.py /home/iperf-server.py

# * Webserver
COPY ./webserver/webserver.py /home/webserver.py
COPY ./webserver/mywebpage.html /home/mywebpage.html
RUN mkdir /home/data

ENV HOME /home
WORKDIR /home
EXPOSE 80
EXPOSE 861
EXPOSE 862
EXPOSE 20000
EXPOSE 20001
EXPOSE 20002

# Define default command.
CMD ["bash"]
