import sys
import requests

import ecal.core.core as ecal_core
from ecal.core.subscriber import ProtoSubscriber

# queue protected by a lock
from queue import Queue
from threading import Lock

coordinates_queue = Queue()
lock = Lock()

import lat_lon_pb2 as lat_lon

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
          print(f"Latitude: {place['lat']}, Longitude: {place['lon']}\n")
    except Exception as e:
      print(e)

def prepare_sideseeing_info(sightseeing_info):
    data = []
    try:
      for place in sightseeing_info:
          attraction = {}
          name = place.get('tags', {}).get('name', None)
          if not name:
            continue

          attraction["name"] = name
          tags = place.get('tags', {})
          tourism_type = tags.get('tourism', None)
          if tourism_type:
            attraction["type"] = tourism_type

          wheelchair = tags.get('wheelchair', None)
          if wheelchair:
            attraction["wheelchair"] = wheelchair
          
          wheelchair_and_toilets = tags.get('toilets:wheelchair', None)
          if wheelchair_and_toilets:
            attraction["wheelchair_and_toilets"] = wheelchair_and_toilets

          fee = tags.get('fee', None)
          if fee:
            attraction["fee"] = fee
          
          phone = tags.get('phone', None)
          if phone:
            attraction["phone"] = phone

          website = tags.get('website', None)
          if website:
            attraction["website"] = website

          email = tags.get('email', None)
          if email:
            attraction["email"] = email

          opening_hours = tags.get('opening_hours', None)
          if opening_hours:
            attraction["opening_hours"] = opening_hours

          addr_street = tags.get('addr:street', None)
          if addr_street:
            attraction["addr_street"] = addr_street
          
          addr_housenumber = tags.get('addr:housenumber',None)
          if addr_housenumber:
            attraction["addr_housenumber"] = addr_housenumber

          addr_postcode = tags.get('addr:postcode', None)
          if addr_postcode:
            attraction["addr_postcode"] = addr_postcode
          
          addr_city = tags.get('addr:city', None)
          if addr_city:
            attraction["addr_city"] = addr_city

          data.append(attraction)
      return data
    except Exception as e:
      print(e)
      return []

# Callback for receiving messages
def put_coordinate_into_queue(_topic_name, coordinate_msg, _time):
    # put the received message into the queue with a lock
    print(f"Received coordinate:\n{coordinate_msg}")
    with lock:
        coordinates_queue.put(coordinate_msg)

if __name__ == "__main__":
    ecal_core.initialize(sys.argv, "Sideseeing Generator Lat Lon")
    sub = ProtoSubscriber("lat_lon_topic", lat_lon.Coordinates)

    # Set the Callback
    sub.set_callback(put_coordinate_into_queue)
  
    while ecal_core.ok():
      # Check if there is a message in the queue
      with lock:
        if not coordinates_queue.empty():
          # Get the message from the queue
          coordinate_msg = coordinates_queue.get()
          print(f"Got coordinate from queue:\n{coordinate_msg}")
          # Get sightseeing information for the location
          try:
            sightseeing_info = fetch_sightseeing_info(coordinate_msg.lat, coordinate_msg.lon)
            print(f"Got sightseeing information: {sightseeing_info}")
            print_sideseeing_info(sightseeing_info)
          except Exception as e:
            print(f"Failed to fetch sightseeing information: {e}")
  
    # finalize eCAL API
    ecal_core.finalize()