# Coordinates Publisher

# Build

```shell
podman build -t sideseeing_starter:latest -f .devcontainer/Dockerfile .
```

## Run

```shell
podman run -it --rm --ipc=host --pid=host --network=host sideseeing_starter:latest /bin/bash
```

## Development

## Building the proto lib with protoc

```shell
mkdir -p /usr/local/lib/lat_lon_coordinates
protoc --python_out=/usr/local/lib/lat_lon_coordinates/ --proto_path=proto_lat_lon/ lat_lon.proto
protoc --python_out=/usr/local/lib/lat_lon_coordinates/ --proto_path=proto_lat_lon/ lat_lon_in_city.proto
touch /usr/local/lib/lat_lon_coordinates/__init__.py
```

## Run

```shell
export PYTHONPATH="${PYTHONPATH}:/usr/local/lib/lat_lon_coordinates"
export PYTHONPATH="${PYTHONPATH}:/usr/local/lib/ankaios"
python3 src/sideseeing_starter.py
```