FROM ghcr.io/ukewea/python-talib:ubuntu24.04-python3.12-20250515

LABEL maintainer="ukewea https://github.com/ukewea"
LABEL org.opencontainers.image.source="https://github.com/ukewea/crypto-bot"

ARG BUILD_ID
LABEL build=$BUILD_ID

# some PyPI packages needs compilation when building arm64 arch image
ENV APT_PKG_TEMPORARY="build-essential autoconf automake autotools-dev libopenblas-dev python3-dev"
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /usr/src/app

# Copy requirements first for better layer caching
COPY requirements.txt ./

RUN apt-get update && \
    apt-get install -y ${APT_PKG_TEMPORARY} && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt && \
    apt-get autoremove -y ${APT_PKG_TEMPORARY} && \
    rm -rf /var/lib/apt/lists/*

COPY . ./

RUN mkdir -p user-config asset-positions logs && \
    chmod 755 user-config asset-positions logs

CMD [ "/venv/bin/python", "./trade_loop.py" ]
