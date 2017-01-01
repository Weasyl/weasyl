FROM alpine:3.5
RUN apk --no-cache --update add docker py2-pip
RUN pip install docker-compose
RUN mkdir /weasyl-src
ADD _wzl /weasyl-src/_wzl
RUN pip install -e /weasyl-src/_wzl
VOLUME /weasyl-src
WORKDIR /weasyl-src
ENTRYPOINT ["python", "-mwzl"]
