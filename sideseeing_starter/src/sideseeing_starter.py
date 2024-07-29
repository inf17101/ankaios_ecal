import sys
import time

import ecal.core.core as ecal_core
from ecal.core.subscriber import ProtoSubscriber
from ecal.core.publisher import ProtoPublisher

import lat_lon_pb2 as lat_lon
import lat_lon_in_city_pb2 as lat_lon_in_city
import ankaios_pb2 as ank

from google.protobuf.internal.encoder import _VarintBytes
from google.protobuf.internal.decoder import _DecodeVarint
import time
import threading
from geopy.geocoders import Nominatim
from geopy.exc import GeopyError

from queue import Queue # this is a synchronized queue

# setup logging
import os, logging
def setup_logger():
    log_level = os.getenv("LOG_LEVEL", "INFO")

    if log_level not in ("TRACE", "INFO", "DEBUG", "WARN", "ERROR"):
        print(f"Invalid log level: '{log_level}'. Use one of TRACE, INFO, DEBUG, WARN, ERROR", file=sys.stderr)
        exit(1)
    logging.basicConfig(level=log_level, format='[%(asctime)s %(levelname)s] %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    return logging.getLogger(__name__)

REQUEST_ID = "sideseeing_starter@ankaios_control_interface"
API_VERSION = "v0.1"
ANKAIOS_CONTROL_INTERFACE_BASE_PATH = "/run/ankaios/control_interface"
coordinates_queue = Queue()
logger = setup_logger()

def is_point_in_city(latitude, longitude):
    """
    Check if the provided latitude and longitude is within a city containing roads with buildings.

    Args:
        latitude (float): Latitude of the point.
        longitude (float): Longitude of the point.

    Returns:
        bool: True if the point is within a city and buildings are available, False otherwise.
    """
    geolocator = Nominatim(user_agent="sideseeing-starter")

    try:
        # Reverse geocode to find the location details
        location = geolocator.reverse((latitude, longitude), exactly_one=True, timeout=10)
        
        if location is None:
            return False
        
        address = location.raw['address']
        logger.debug(location.raw)
        
        # Check if the location type is 'city' or 'town' or equivalent
        if 'city' in address:
            city_name = address['city']
        elif 'town' in address:
            city_name = address['town']
        elif 'village' in address:
            city_name = address['village']
        elif 'hamlet' in address:
            city_name = address['hamlet']
        elif 'municipality' in address:
            city_name = address['municipality']
        else:
            return False
        
        location_class = location.raw['class']
        if location_class == 'highway' or location_class == 'junction':
            return False

        logger.info(f"Found city name: {city_name}")
        return True
    
    except GeopyError as e:
        logger.error(f"Unexpected error: {e}")
        return False

def create_request_for_new_sideseeing_generator_workload():
    """Create the Request containing an UpdateStateRequest
    that contains the details for adding the new workload sideseeing_generator
    and the update mask to add only the new workload.
    """

    return ank.ToServer(
        request=ank.Request(
            requestId=REQUEST_ID,
            updateStateRequest=ank.UpdateStateRequest(
                newState=ank.CompleteState(
                    desiredState=ank.State(
                        apiVersion=API_VERSION,
                        workloads={
                            "sideseeing_generator": ank.Workload(
                                agent="agent_A",
                                runtime="podman",
                                restartPolicy=ank.NEVER,
                                runtimeConfig="image: sideseeing_generator:latest\ncommandOptions: [\"--ipc=host\", \"--pid=host\", \"--network=host\", \"--name\", \"sideseeing_generator\"]",
                            )
                        }
                    )
                ),
                updateMask=["desiredState.workloads.sideseeing_generator"]
            )
        )
    )

def create_request_to_delete_sideseeing_generator_workload():
    """Create the Request containing an UpdateStateRequest
    that contains the details for deleting the workload sideseeing_generator
    and the update mask to delete only the workload.
    """

    return ank.ToServer(
        request=ank.Request(
            requestId=REQUEST_ID,
            updateStateRequest=ank.UpdateStateRequest(
                newState=ank.CompleteState(
                    desiredState=ank.State(
                        apiVersion=API_VERSION,
                        workloads={}
                    )
                ),
                updateMask=["desiredState.workloads.sideseeing_generator"]
            )
        )
    )

def write_to_control_interface(proto_msg):
    """Writes a Request into the control interface output fifo
    """

    with open(f"{ANKAIOS_CONTROL_INTERFACE_BASE_PATH}/output", "ab") as f:
        proto_msg_byte_len = proto_msg.ByteSize() # Length of the msg
        proto_serialized_msg = proto_msg.SerializeToString() # Serialized proto msg

        logger.info(f'Writing proto message into fifo file: ToServer {{\n{proto_msg}}}\n')
        f.write(_VarintBytes(proto_msg_byte_len)) # Send the byte length of the proto msg
        f.write(proto_serialized_msg) # Send the proto msg itself
        f.flush()

def read_from_control_interface():
    """Reads from the control interface input fifo and logs the response"""

    with open(f"{ANKAIOS_CONTROL_INTERFACE_BASE_PATH}/input", "rb") as f:

        while True:
            varint_buffer = b'' # Buffer for reading in the byte size of the proto msg
            while True:
                next_byte = f.read(1) # Consume byte for byte
                if not next_byte:
                    break
                varint_buffer += next_byte
                if next_byte[0] & 0b10000000 == 0: # Stop if the most significant bit is 0 (indicating the last byte of the varint)
                    break
            msg_len, _ = _DecodeVarint(varint_buffer, 0) # Decode the varint and receive the proto msg length

            msg_buf = b'' # Buffer for the proto msg itself
            for _ in range(msg_len):
                next_byte = f.read(1) # Read exact amount of byte according to the calculated proto msg length
                if not next_byte:
                    break
                msg_buf += next_byte

            from_server = ank.FromServer()
            try:
                from_server.ParseFromString(msg_buf) # Deserialize the received proto msg
            except Exception as e:
                logger.error(f"Invalid response, parsing error: '{e}'")
                continue

            request_id = from_server.response.requestId
            if from_server.response.requestId == REQUEST_ID:
                logger.info(f"Receiving Response containing the workload states of the current state:\nFromServer {{\n{from_server}}}\n")
            else:
                logger.warn(f"RequestId does not match. Skipping messages from requestId: {request_id}")

# Callback for receiving messages
def put_coordinate_into_queue(_topic_name, coordinate_msg, _time):
    coordinates_queue.put(coordinate_msg)

def create_sideseeing_generator_workload():
    logger.debug(f"Creating the sideseeing_generator workload.")
    new_workload_request = create_request_for_new_sideseeing_generator_workload()
    write_to_control_interface(new_workload_request)

def delete_sideseeing_generator_workload():
    logger.debug(f"Deleting the sideseeing_generator workload.")
    delete_workload_request = create_request_to_delete_sideseeing_generator_workload()
    write_to_control_interface(delete_workload_request)

def next_message_from_queue_blocking():
    next_coordinate = coordinates_queue.get(block=True)
    coordinates_queue.task_done()
    return next_coordinate

def is_transition_of_city_boundaries(previous_is_within_city, is_city):
    return previous_is_within_city != is_city

if __name__ == "__main__":
    read_thread = threading.Thread(target=read_from_control_interface, daemon=True)
    read_thread.start()

    ecal_core.initialize(sys.argv, "Sideseeing Starter")
    sub = ProtoSubscriber("lat_lon_topic", lat_lon.Coordinates)
    pub = ProtoPublisher("lat_lon_in_city_topic", lat_lon_in_city.LatLonInCity)

    # Set the Callback
    sub.set_callback(put_coordinate_into_queue)
  
    sideseeing_generator_running = False
    previous_is_within_city = False
    
    while ecal_core.ok():
        coordinate_msg = next_message_from_queue_blocking()

        is_city = is_point_in_city(coordinate_msg.lat, coordinate_msg.lon)

        if is_transition_of_city_boundaries(previous_is_within_city, is_city):
            proto_in_city = lat_lon_in_city.LatLonInCity()
            proto_in_city.lat_lon_in_city = is_city
            pub.send(proto_in_city)
        
        previous_is_within_city = is_city

        if is_city:
            logger.info(f"Point {coordinate_msg} is within a city.")

            if not sideseeing_generator_running:
                create_sideseeing_generator_workload()
                sideseeing_generator_running = True
        else:
            logger.info(f"Point {coordinate_msg} is not within a city.")

            if sideseeing_generator_running:
                delete_sideseeing_generator_workload()
                sideseeing_generator_running = False
  
    # finalize eCAL API
    ecal_core.finalize()
    read_thread.join()
