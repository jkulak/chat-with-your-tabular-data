# smartplaylist/app
FROM python:3.10.7-alpine3.16

RUN apk update && apk upgrade
RUN apk add --no-cache htop ncdu \
    && rm -rf /var/cache/apk/*

WORKDIR /app
ADD ./src/ ./
RUN pip install --no-cache-dir pipenv==v2022.10.25 && \
    pipenv install
