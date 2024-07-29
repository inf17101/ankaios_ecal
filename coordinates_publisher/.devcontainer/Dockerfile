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

FROM dev as prod

COPY proto_lat_lon /proto_lat_lon

RUN mkdir -p /usr/local/lib/lat_lon_coordinates \
    && protoc --python_out=/usr/local/lib/lat_lon_coordinates/ --proto_path=/proto_lat_lon/ lat_lon.proto \
    && touch /usr/local/lib/lat_lon_coordinates/__init__.py

ENV PYTHONPATH="${PYTHONPATH}:/usr/local/lib/lat_lon_coordinates"
COPY src /coordinates_publisher

ENTRYPOINT ["python3", "-u", "/coordinates_publisher/coordinates_publisher.py"]