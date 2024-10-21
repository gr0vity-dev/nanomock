FROM python:3.8-alpine


WORKDIR /
RUN apk update
RUN apk add git gcc musl-dev linux-headers

ARG hash_value=853a6c2f0934c99fe5a388994ddf2f3176139716
RUN git clone https://github.com/gr0vity-dev/bnano-prom-exporter.git app

WORKDIR /app

RUN git fetch --all
RUN git checkout $hash_value
RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "-m", "nano_prom_exporter" ]