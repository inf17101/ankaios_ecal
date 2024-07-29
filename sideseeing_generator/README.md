# Coordinates Publisher

## Build

```shell
podman build -t sideseeing_generator:latest -f .devcontainer/Dockerfile .
```

## Run

```shell
podman run -it --rm --ipc=host --pid=host --network=host sideseeing_generator:latest /bin/bash
```

## Development

## Building the proto lib with protoc

```shell
mkdir -p /usr/local/lib/lat_lon_coordinates
protoc --python_out=/usr/local/lib/lat_lon_coordinates/ --proto_path=proto_lat_lon/ lat_lon.proto
touch /usr/local/lib/lat_lon_coordinates/__init__.py

mkdir -p /usr/local/lib/sideseeing_info
protoc --python_out=/usr/local/lib/sideseeing_info/ --proto_path=/proto_sideseeing_info/ sideseeing_info.proto
touch /usr/local/lib/sideseeing_info/__init__.py
```
## Run

```shell
export PYTHONPATH="${PYTHONPATH}:/usr/local/lib/lat_lon_coordinates"
export PYTHONPATH="${PYTHONPATH}:/usr/local/lib/sideseeing_info"
python3 src/sideseeing_generator.py
```
