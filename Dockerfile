FROM alpine
RUN apk update && apk add docker py-pip
RUN pip install docker-compose
ADD . /weasyl-src
RUN pip install -e /weasyl-src/_wzl
VOLUME /weasyl-src
WORKDIR /weasyl-src
ENTRYPOINT ["python", "-mwzl"]
