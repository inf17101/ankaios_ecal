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
    requests

FROM dev as prod

COPY proto_lat_lon /proto_lat_lon
COPY proto_sideseeing_info /proto_sideseeing_info

RUN mkdir -p /usr/local/lib/lat_lon_coordinates \
    && protoc --python_out=/usr/local/lib/lat_lon_coordinates/ --proto_path=/proto_lat_lon/ lat_lon.proto \
    && touch /usr/local/lib/lat_lon_coordinates/__init__.py

RUN mkdir -p /usr/local/lib/sideseeing_info \
    && protoc --python_out=/usr/local/lib/sideseeing_info/ --proto_path=/proto_sideseeing_info/ sideseeing_info.proto \
    && touch /usr/local/lib/sideseeing_info/__init__.py

ENV PYTHONPATH="${PYTHONPATH}:/usr/local/lib/lat_lon_coordinates"
ENV PYTHONPATH="${PYTHONPATH}:/usr/local/lib/sideseeing_info"
COPY src /sideseeing_generator

ENTRYPOINT ["python3", "-u", "/sideseeing_generator/sideseeing_generator.py"]