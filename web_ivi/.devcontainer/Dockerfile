FROM docker.io/ubuntu:24.04 as dev

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install \
    software-properties-common \
    python3 \
    python3-pip \
    protobuf-compiler \
    && \
    rm -rf /var/lib/apt/lists/* \
    && add-apt-repository ppa:ecal/ecal-latest \
    && apt-get install -y python3-ecal5

RUN PIP_BREAK_SYSTEM_PACKAGES=1 pip install \
    fastapi \
    uvicorn

FROM dev as prod

COPY proto_sideseeing_info /proto_sideseeing_info
COPY src /web_ivi/src
COPY static /web_ivi/static

RUN mkdir -p /usr/local/lib/sideseeing_info \
    && protoc --python_out=/usr/local/lib/sideseeing_info/ --proto_path=/proto_sideseeing_info/ sideseeing_info.proto \
    && protoc --python_out=/usr/local/lib/sideseeing_info/ --proto_path=/proto_sideseeing_info/ lat_lon_in_city.proto \
    && touch /usr/local/lib/sideseeing_info/__init__.py

ENV PYTHONPATH="${PYTHONPATH}:/usr/local/lib/sideseeing_info"
WORKDIR /web_ivi

ENTRYPOINT ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "5500"]