FROM python:3.8-alpine


WORKDIR /
RUN apk update
RUN apk add git gcc musl-dev linux-headers

ARG hash_value=45e3efcd090f93e416504403fbf1474a753873db
RUN git clone https://github.com/gr0vity-dev/bnano-prom-exporter.git app

WORKDIR /app

RUN git fetch --all
RUN git checkout $hash_value
RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "-m", "nano_prom_exporter" ]