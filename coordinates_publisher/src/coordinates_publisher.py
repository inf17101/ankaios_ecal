import sys, time
import ecal.core.core as ecal_core
from ecal.core.publisher import ProtoPublisher

# proto message lib
import lat_lon_pb2 as lat_lon

# setup logging
import os, logging
def setup_logger():
    log_level = os.getenv("LOG_LEVEL", "INFO")

    if log_level not in ("TRACE", "INFO", "DEBUG", "WARN", "ERROR"):
        print(f"Invalid log level: '{log_level}'. Use one of TRACE, INFO, DEBUG, WARN, ERROR", file=sys.stderr)
        exit(1)
    logging.basicConfig(level=log_level, format='[%(asctime)s %(levelname)s] %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    return logging.getLogger(__name__)

TRK_FILE_PATH = "/trk_files/trk.trk"
LON_POSITION = 0
LAT_POSITION = 1
logger = setup_logger()

class CoordinatesPublisher:
    def __init__(self):
        # initialize eCAL API
        ecal_core.initialize(sys.argv, "Coordinates Publisher")
        self.__publisher = ProtoPublisher("lat_lon_topic", lat_lon.Coordinates)

    def send(self, message):
        self.__publisher.send(message)

    def ok(self):
        return ecal_core.ok()

    def __del__(self):
        # finalize eCAL API
        ecal_core.finalize()

def create_lat_lon_proto_message(latitude, longitude):
    message = lat_lon.Coordinates()
    message.lat = latitude
    message.lon = longitude
    return message

def extract_latitude_longitude(line):
    splitted_line = line.strip().split(',')
    try:
        lon = float(splitted_line[LON_POSITION])
        lat = float(splitted_line[LAT_POSITION])
    except ValueError:
        return None, None
    return lat, lon

def read_lat_lon_from_file_and_publish():
    try:
        with open(TRK_FILE_PATH) as trk_file:
            next_line = trk_file.readline()
            coordinates_publisher = CoordinatesPublisher()
            while coordinates_publisher.ok() and next_line:
                lat, lon = extract_latitude_longitude(next_line)

                if lat is None or lon is None:
                    logger.error(f"Failed to extract lat/lon. Invalid line: '{next_line}'. Continue to next line.")
                else:
                    proto_msg = create_lat_lon_proto_message(lat, lon)

                    logger.info(f"Publishing proto message: \n{proto_msg}")
                    coordinates_publisher.send(proto_msg)
                
                next_line = trk_file.readline()
                time.sleep(1) # publish a lat/lon message approx. every second
        
        logger.info("End of file reached. Done.")
    except FileNotFoundError:
        logger.error(f"File '{TRK_FILE_PATH}' not found")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    read_lat_lon_from_file_and_publish()