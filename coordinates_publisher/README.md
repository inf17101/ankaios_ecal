# Coordinates Publisher

## Build

```shell
podman build -t coordinates_publisher:latest -f .devcontainer/Dockerfile .
```

## Run

```shell
podman run -it --rm -v ./assets/trk_files/route_nuernberg.csv:/trk_files/trk.csv --ipc=host --pid=host --network=host coordinates_publisher:latest /bin/bash
```

## Development

## Building the proto lib with protoc

```shell
mkdir -p /usr/local/lib/lat_lon_coordinates
protoc --python_out=/usr/local/lib/lat_lon_coordinates/ --proto_path=proto_lat_lon/ lat_lon.proto
touch /usr/local/lib/lat_lon_coordinates/__init__.py
```
## Run

The scripts expects the csv file containing latitude and longitude coordinates under `/trk_files/trk.csv`.

Prepare the execution with the following commands:

```shell`
mkdir -p /trk_files
cp assets/trk_files/route_nuernberg.csv /trk_files/trk.csv
export PYTHONPATH="${PYTHONPATH}:/usr/local/lib/lat_lon_coordinates"
```

Execute the coordinates publisher:

```shell
python3 src/coordinates_publisher.py
```