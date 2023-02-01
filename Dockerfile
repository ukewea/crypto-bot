FROM registry.gitlab.com/bocchi-the-crypto/python-ta-lib/main:latest

LABEL maintainer="ukewea https://github.com/ukewea"

ARG BUILD_ID
LABEL build=$BUILD_ID

# some PyPI packages needs compilation when building arm64 arch image
ENV APT_PKG_TEMPORARY="build-essential autoconf automake autotools-dev libopenblas-dev python3-dev"
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /usr/src/app

COPY * ./

RUN apt-get update && \
    apt-get install -y ${APT_PKG_TEMPORARY} && \
    pip3 install --no-cache-dir -r requirements.txt && \
    apt-get autoremove -y ${APT_PKG_TEMPORARY} && \
    rm -rf /var/lib/apt/lists/*

CMD [ "python3", "./trade_loop.py" ]
