# Coordinates Publisher

## Build

```shell
podman build -t web_ivi:latest -f .devcontainer/Dockerfile .
```

## Run

```shell
podman run -it --rm --ipc=host --pid=host --network=host web_ivi:latest
```

## Development

### Run

```shell
mkdir -p /usr/local/lib/sideseeing_info
protoc --python_out=/usr/local/lib/sideseeing_info/ --proto_path=proto_sideseeing_info/ sideseeing_info.proto
protoc --python_out=/usr/local/lib/sideseeing_info/ --proto_path=proto_sideseeing_info/ lat_lon_in_city.proto
touch /usr/local/lib/sideseeing_info/__init__.py
```

```shell
export PYTHONPATH="${PYTHONPATH}:/usr/local/lib/sideseeing_info"
uvicorn src.main:app --reload
```