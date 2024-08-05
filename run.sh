#!/bin/bash
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ANKAIOS_SERVER_SOCKET="0.0.0.0:25551"
ANKAIOS_SERVER_URL="http://${ANKAIOS_SERVER_SOCKET}"
ANKAIOS_MANIFEST_PATH="config/startConfig.yaml"

print_usage() {
  echo "Usage: $0 [coordinates_csv_file]"
  echo "coordinates_csv_file: path to the csv trk file containing the lat/lon coordinates, e.g. coordinates_publisher/assets/trk_files/route_nuernberg.csv"
}

if [ -z "$1" ]; then
  print_usage
  exit 1
fi

SRC_COORDINATES_FILE_PATH="$1"

  if [ ! -f "$SRC_COORDINATES_FILE_PATH" ]; then
    echo "Error: File not found: $SRC_COORDINATES_FILE_PATH"
    print_usage
    exit 2
  fi

DEST_COORDINATES_FILE_PATH="/tmp/trk.csv"

echo "Building coordinates_publisher:latest"
(
  cd coordinates_publisher \
    && podman build -t coordinates_publisher:latest -f .devcontainer/Dockerfile .
)

echo "Building sideseeing_starter:latest"
(
  cd sideseeing_starter/ \
    && podman build -t sideseeing_starter:latest -f .devcontainer/Dockerfile .
)

echo "Building sideseeing_generator:latest"
(
  cd sideseeing_generator/ \
    && podman build -t sideseeing_generator:latest -f .devcontainer/Dockerfile .
)

echo "Building web_ivi:latest"
(
  cd web_ivi/ \
    && podman build -t web_ivi:latest -f .devcontainer/Dockerfile .
)

echo "Build done."

echo "Starting Eclipse Ankaios with Ankaios manifest ${ANKAIOS_MANIFEST_PATH}"

trap 'cleanup_routine' EXIT SIGTERM SIGQUIT SIGKILL

cleanup_routine() {
    $SCRIPT_DIR/shutdown.sh
}

run_ankaios() {

  if [[ -z "$ANK_BIN_DIR" ]]; then
      ANK_BIN_DIR="/usr/local/bin"
      echo Use default executable directory: $ANK_BIN_DIR
  fi

  ANKAIOS_LOG_DIR="/tmp"

  cp ${SRC_COORDINATES_FILE_PATH} ${DEST_COORDINATES_FILE_PATH}

  # Start the Ankaios server
  echo "Starting Ankaios server"
  ${ANK_BIN_DIR}/ank-server --startup-config ${SCRIPT_DIR}/${ANKAIOS_MANIFEST_PATH} --address ${ANKAIOS_SERVER_SOCKET} > ${ANKAIOS_LOG_DIR}/ankaios-server.log 2>&1 &

  sleep 2
  # Start an Ankaios agent
  echo "Starting Ankaios agent agent_A"
  ${ANK_BIN_DIR}/ank-agent --name agent_A --server-url ${ANKAIOS_SERVER_URL} > ${ANKAIOS_LOG_DIR}/ankaios-agent_A.log 2>&1 &

  echo "For graceful shutdown press Ctrl+C. Never exit just the terminal. Otherwise execute 'shutdown.sh' manually."

  # Wait for any process to exit
  wait -n

  # Exit with status of process that exited first
  exit $?
}

run_ankaios
