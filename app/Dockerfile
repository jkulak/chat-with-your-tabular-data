# smartplaylist/app
FROM python:3.11.6-alpine3.18

RUN apk update && apk upgrade
RUN apk add --no-cache htop ncdu git gcc g++ musl-dev python3-dev openblas-dev \
    && rm -rf /var/cache/apk/*

WORKDIR /app
ADD ./src/ ./
RUN pip install --no-cache-dir pipenv==2023.10.3 && \
    pipenv install
