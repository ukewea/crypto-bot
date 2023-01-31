FROM registry.gitlab.com/bocchi-the-crypto/python-ta-lib/main:latest

LABEL maintainer="ukewea https://github.com/ukewea"

ARG BUILD_ID
LABEL build=$BUILD_ID

ENV APK_PKG_TEMPORARY="musl-dev wget git build-base linux-headers openblas-dev"

WORKDIR /usr/src/app

COPY * ./

RUN apk update && \
  apk add ${APK_PKG_TEMPORARY} && \
  ln -s /usr/include/locale.h /usr/include/xlocale.h && \
  pip install --no-cache-dir -r requirements.txt && \
  apk del ${APK_PKG_TEMPORARY}

CMD [ "python", "./trade_loop.py" ]
