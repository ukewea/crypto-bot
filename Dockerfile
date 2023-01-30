FROM python:3.11-alpine

MAINTAINER ukewea <https://github.com/ukewea>

ARG BUILD_ID
LABEL build=$BUILD_ID

WORKDIR /usr/src/app

COPY * ./

# Install NumPy, TA-Lib
RUN apk update && \
  apk add musl-dev wget git build-base openblas-dev linux-headers py3-scipy && \
  ln -s /usr/include/locale.h /usr/include/xlocale.h && \
  \
  wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
  tar -xvzf ta-lib-0.4.0-src.tar.gz && \
  cd ta-lib/ && \
  ARCH=`uname -m` && \
  if [ "$ARCH" == "aarch64" ]; then \
    ./configure --prefix=/usr --build=arm-linux; \
  else \
    ./configure --prefix=/usr; \
  fi && \
  make && \
  make install && \
  cd .. && \
  rm -rf ta-lib ta-lib-0.4.0-src.tar.gz && \
  \
  pip install --no-cache-dir cython numpy TA-Lib && \
  pip install --no-cache-dir -r requirements.txt && \
  apk del musl-dev wget git build-base linux-headers openblas-dev


CMD [ "python", "./trade_loop.py" ]
