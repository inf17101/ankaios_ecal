import sys
import requests

import ecal.core.core as ecal_core
from ecal.core.subscriber import ProtoSubscriber
from ecal.core.publisher import ProtoPublisher
import threading, time

from queue import Queue

coordinates_queue = Queue() # synchronized queue

import lat_lon_pb2 as lat_lon
import sideseeing_info_pb2 as sideseeing_info

def fetch_sightseeing_info(lat, lon, radius_in_meter=5000):
    """
    Get sightseeing information for a given location (lat, lon) using Overpass API.
    """

    overpass_url = (
        f"http://overpass-api.de/api/interpreter"
        f"?data=[out:json];node(around:{radius_in_meter},{lat},{lon})"
        f"[tourism~\"attraction|museum|zoo|theme_park|viewpoint|park|historical|castle|monument|memorial\"];out;"
    )

    response = requests.get(overpass_url)
    response.raise_for_status()
    data = response.json()

    return data.get('elements', [])

def print_sideseeing_info(sightseeing_info):
    try:
        for place in sightseeing_info:
            name = place.get('tags', {}).get('name', None)
            if not name:
                continue
            tourism_type = place.get('tags', {}).get('tourism', 'N/A')
            print(f"Name: {name}")
            print(f"Type: {tourism_type}")
    except Exception as e:
        print(e)

def prepare_sideseeing_info(sightseeing_info):
    try:
        attraction = sideseeing_info.SideseeingInfo()
        name = sightseeing_info.get('tags', {}).get('name', None)

        if not name:
            return None
        
        attraction.name = name
        tags = sightseeing_info.get('tags', {})
        tourism_type = tags.get('tourism', None)
        if tourism_type:
            attraction.type = tourism_type

        wheelchair = tags.get('wheelchair', None)
        if wheelchair:
            attraction.wheelchair = wheelchair
        
        wheelchair_and_toilets = tags.get('toilets:wheelchair', None)
        if wheelchair_and_toilets:
            attraction.wheelchair_toilets = wheelchair_and_toilets

        fee = tags.get('fee', None)
        if fee:
            attraction.fee = fee
        
        phone = tags.get('phone', None)
        if phone:
            attraction.phone = phone

        website = tags.get('website', None)
        if website:
            attraction.website = website

        email = tags.get('email', None)
        if email:
            attraction.email = email

        opening_hours = tags.get('opening_hours', None)
        if opening_hours:
            attraction.opening_hours = opening_hours

        addr_street = tags.get('addr:street', None)
        if addr_street:
            attraction.addr_street = addr_street
        
        addr_housenumber = tags.get('addr:housenumber',None)
        if addr_housenumber:
            attraction.addr_housenumber = addr_housenumber

        addr_postcode = tags.get('addr:postcode', None)
        if addr_postcode:
            attraction.addr_postcode = addr_postcode
        
        addr_city = tags.get('addr:city', None)
        if addr_city:
            attraction.addr_city = addr_city

        wikipedia_article = tags.get('wikipedia', None)
        if wikipedia_article:
            attraction.wikipedia = wikipedia_article

        return attraction
    except Exception as e:
        print(e)
    return None

# Callback for receiving messages
def put_coordinate_into_queue(_topic_name, coordinate_msg, _time):
    print(f"Received coordinate:\n{coordinate_msg}")
    coordinates_queue.put(coordinate_msg)

def next_message_from_queue_blocking(queue_container):
    next_item = queue_container.get(block=True)
    queue_container.task_done()
    return next_item

if __name__ == "__main__":
    ecal_core.initialize(sys.argv, "Sideseeing Generator Lat Lon")
    sub = ProtoSubscriber("lat_lon_topic", lat_lon.Coordinates)
    pub = ProtoPublisher("sideseeing_info_topic", sideseeing_info.SideseeingInfo)

    # Set the Callback
    sub.set_callback(put_coordinate_into_queue)

    sideseeing_info_data = {}
    while ecal_core.ok():
        coordinate_msg = next_message_from_queue_blocking(coordinates_queue)
        print(f"Got coordinate from queue:\n{coordinate_msg}")
        # Get sightseeing information for the location
        try:
            sightseeing_infos = fetch_sightseeing_info(coordinate_msg.lat, coordinate_msg.lon)
            # print_sideseeing_info(sightseeing_infos)
            for place in sightseeing_infos:
                proto_sightseeing_msg = prepare_sideseeing_info(place)
                if proto_sightseeing_msg and proto_sightseeing_msg.name:
                    if sideseeing_info_data.get(proto_sightseeing_msg.name, None) is None:
                        sideseeing_info_data[proto_sightseeing_msg.name] = proto_sightseeing_msg
                        print(f"Publishing sideseeing info:\n{proto_sightseeing_msg}")
                        pub.send(proto_sightseeing_msg)
                        # put_sideseeing_proto_msg_to_queue(proto_sightseeing_msg)
        except Exception as e:
            print(f"Failed to fetch sightseeing information: {e}")
        time.sleep(0.3)
  
    # finalize eCAL API
    ecal_core.finalize()