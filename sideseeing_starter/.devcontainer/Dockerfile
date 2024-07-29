FROM docker.io/ubuntu:24.04 as dev

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install \
    curl \
    software-properties-common \
    python3 \
    python3-pip \
    protobuf-compiler \
    && \
    rm -rf /var/lib/apt/lists/* \
    && add-apt-repository ppa:ecal/ecal-latest \
    && apt-get install -y python3-ecal5

RUN PIP_BREAK_SYSTEM_PACKAGES=1 pip install \
    geopy \
    shapely

RUN mkdir -p /usr/local/lib/ankaios \
    && curl -sL https://github.com/eclipse-ankaios/ankaios/releases/download/v0.3.1/ankaios.proto -o /usr/local/lib/ankaios/ankaios.proto

RUN protoc --python_out=/usr/local/lib/ankaios/ --proto_path=/usr/local/lib/ankaios/ ankaios.proto \
    && touch /usr/local/lib/ankaios/__init__.py

FROM dev as prod

COPY proto_lat_lon /proto_lat_lon

RUN mkdir -p /usr/local/lib/lat_lon_coordinates \
    && protoc --python_out=/usr/local/lib/lat_lon_coordinates/ --proto_path=/proto_lat_lon/ lat_lon.proto \
    && protoc --python_out=/usr/local/lib/lat_lon_coordinates/ --proto_path=proto_lat_lon/ lat_lon_in_city.proto \
    && touch /usr/local/lib/lat_lon_coordinates/__init__.py

ENV PYTHONPATH="${PYTHONPATH}:/usr/local/lib/lat_lon_coordinates"
ENV PYTHONPATH="${PYTHONPATH}:/usr/local/lib/ankaios"
COPY --from=dev /usr/local/lib/ankaios /usr/local/lib/ankaios
COPY src /sideseeing_starter

ENTRYPOINT ["python3", "-u", "/sideseeing_starter/sideseeing_starter.py"]