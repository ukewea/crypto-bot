FROM registry.gitlab.com/bocchi-the-crypto/python-ta-lib/main:latest

LABEL maintainer="ukewea https://github.com/ukewea"

ARG BUILD_ID
LABEL build=$BUILD_ID

WORKDIR /usr/src/app

COPY * ./

RUN pip3 install --no-cache-dir -r requirements.txt

CMD [ "python3", "./trade_loop.py" ]
