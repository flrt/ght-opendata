FROM python:3.6
LABEL maintainer: "Frederic Laurent <frederic.laurent@gmail.com>"
LABEL description: "simple container with xml, http, pandas, xls capabilities"
LABEL version: "1.0"

RUN apt-get update
RUN apt-get -y install python3-lxml libxml2-utils
RUN pip install requests
RUN pip install lxml
RUN pip install pandas 
RUN pip install pyproj 
RUN pip install xlrd

WORKDIR /opt