from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from uvicorn import run
import json, time, sys
from asyncio import sleep
from queue import Queue
import threading
import logging
from contextlib import asynccontextmanager

import sideseeing_info_pb2 as sideseeing_info
import lat_lon_in_city_pb2 as lat_lon_in_city
import ecal.core.core as ecal_core
from ecal.core.subscriber import ProtoSubscriber
from google.protobuf.json_format import MessageToDict

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)

sideseeing_info_queue = Queue()

in_citiy_lock = threading.Lock()
vehicle_within_city = False

KEEP_ALIVE_INTERVAL = 20 # seconds

def receive_sideseeing_info(stop_event):
    logger.info("Starting Sideseeing Info Receiver")
    ecal_core.initialize(sys.argv, "WebIVI SideSeeingInfo")
    sub = ProtoSubscriber("sideseeing_info_topic", sideseeing_info.SideseeingInfo)
    
    # Set the Callback
    sub.set_callback(put_sideseeing_info_into_queue)

    while ecal_core.ok() and not stop_event.is_set():
        logger.debug("Waiting for Sideseeing Info")
        time.sleep(0.5)
        continue

    # finalize eCAL API
    ecal_core.finalize()

def receive_lat_lon_in_city_info(stop_event):
    logger.info("Starting Lat Lon in City Receiver")
    ecal_core.initialize(sys.argv, "WebIVI LatLonInCity")
    sub = ProtoSubscriber("lat_lon_in_city_topic", lat_lon_in_city.LatLonInCity)
    
    # Set the Callback
    sub.set_callback(set_lat_lon_in_city_flag)

    while ecal_core.ok() and not stop_event.is_set():
        logger.debug("Waiting for Sideseeing Info")
        time.sleep(0.5)

    # finalize eCAL API
    ecal_core.finalize()

def put_sideseeing_info_into_queue(_topic_name, proto_sideeeing_info, _time):
    logger.info("Received Sideseeing Info")
    sideseeing_info_queue.put(proto_sideeeing_info)

def set_lat_lon_in_city_flag(_topic_name, proto_lat_lon_in_city, _time):
    logger.info(f"Received lat_lon_in_city: {proto_lat_lon_in_city}")
    with in_citiy_lock:
        global vehicle_within_city
        vehicle_within_city = proto_lat_lon_in_city.lat_lon_in_city

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run at startup
    stop_event_sideseeing_receiver = threading.Event()
    sideseeing_receiver_thread = threading.Thread(target=receive_sideseeing_info, args=(stop_event_sideseeing_receiver,))
    sideseeing_receiver_thread.start()

    stop_event_lat_lon_in_city_receiver = threading.Event()
    lat_lon_in_city_thread = threading.Thread(target=receive_lat_lon_in_city_info, args=(stop_event_lat_lon_in_city_receiver,))
    lat_lon_in_city_thread.start()
    yield
    # Run on shutdown
    stop_event_sideseeing_receiver.set()
    stop_event_lat_lon_in_city_receiver.set()
    sideseeing_receiver_thread.join()
    lat_lon_in_city_thread.join()
    logger.info('Shutting down...')

# create a route that delivers the statc/index.html file
app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def home():
    return FileResponse("static/index.html")

@app.get("/sideseeings")
async def sideseeings():
    async def sideseeing_generator():
        last_keep_alive_time = time.time()
        previous_is_within_city = None
        while True:
            current_time = time.time()
            elapsed_time = current_time - last_keep_alive_time

            if elapsed_time >= KEEP_ALIVE_INTERVAL:
                yield ":\n\n" # Send keep alive
                last_keep_alive_time = current_time

            is_within_city = is_vehicle_within_city()

            if is_within_city and not sideseeing_info_queue.empty():
                proto_sideeeing_info = sideseeing_info_queue.get()
                sideseeing_info_queue.task_done()
                payload = MessageToDict(proto_sideeeing_info)
                json_out = json.dumps(payload)
                event_out = f"event: sideseeings\ndata: {json_out}\n\n"
                logger.info(f"yield {event_out}")
                yield event_out

            # push only on changed state
            if is_within_city != previous_is_within_city or previous_is_within_city is None:
                payload = {"is_within_city": is_within_city}
                logger.info(f"vehicle_within_city: {is_within_city}")
                json_out = json.dumps(payload)
                event_out = f"event: vehicle_within_city\ndata: {json_out}\n\n"
                logger.info(f"yield {event_out}")
                yield event_out
            previous_is_within_city = is_within_city
            await sleep(0.5)
    return StreamingResponse(sideseeing_generator(), media_type="text/event-stream")

def is_vehicle_within_city():
    is_within_city = False
    with in_citiy_lock:
        global vehicle_within_city
        is_within_city = vehicle_within_city
    return is_within_city

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=5500)

