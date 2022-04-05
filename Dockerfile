FROM python:3.10-alpine

RUN apk add --update py-pip
RUN apk add py3-setuptools
RUN apk add --no-cache git util-linux bash openssl curl
RUN apk add --no-cache --virtual .build_deps build-base libffi-dev
RUN pip3 install --extra-index-url https://test.pypi.org/simple/ prismacloud-cli==0.1.1
RUN apk del .build_deps
