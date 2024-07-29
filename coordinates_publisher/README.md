# Coordinates Publisher

## Build

```shell
podman build -t coordinates_publisher:latest -f .devcontainer/Dockerfile .
```

## Run

```shell
podman run -it --rm -v ./assets/trk_files/test_trk.trk:/trk_files/trk.trk --ipc=host --pid=host --network=host coordinates_publisher:latest /bin/bash
```

## Development

## Building the proto lib with protoc

```shell
mkdir -p /usr/local/lib/lat_lon_coordinates
protoc --python_out=/usr/local/lib/lat_lon_coordinates/ --proto_path=proto_lat_lon/ lat_lon.proto
touch /usr/local/lib/lat_lon_coordinates/__init__.py
```
## Run

```shell
mkdir /trk_files
cp assets/trk_files/test_trk.trk /trk_files/trk.trk
export PYTHONPATH="${PYTHONPATH}:/usr/local/lib/lat_lon_coordinates"
python3 src/coordinates_publisher.py assets/trk_files/test_trk.trk
```