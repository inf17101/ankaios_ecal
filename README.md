#  Blueprint Eclipse Ankaios and Eclipse eCAL

The repository contains a blueprint for implementing a sample scenario using [Eclipse Ankaios](https://eclipse-ankaios.github.io/ankaios/0.3/) and [Eclipse eCAL](https://eclipse-ecal.github.io/ecal/).

The sample scenario is to generate sideseeing information when the vehicle enters a city. The sideseeing information is displayed in the user's virtual cockpit (IVI), which in this case is a demo Web IVI running as a workload and accessible through the user's browser. When the vehicle leaves the city, no sideseeing information is visible in the IVI.

To realize this use case, the software orchestrator Eclipse Ankaios and the pub/sub middleware Eclipse eCAL, both optimized for automotive use, are used. Eclipse Ankaios acts as a software orchestrator and deploys all applications (called workloads in the following) of the scenario as containers on the podman runtime. A software orchestrator allows workloads to be dynamically launched. The workload that generates the sideseeing information and publishes the data only needs to run when the vehicle is in a city. The 'sideseeing starter' workload starts the 'sideseeing generator' workload when the vehicle enters a city and deletes it when the vehicle leaves the city. It uses the Ankaios [control interface](https://eclipse-ankaios.github.io/ankaios/0.3/reference/control-interface/) to dynamically start and stop the workload. Eclipse eCAL is used to exchange information about the sideseeing and lat/lon positions of the vehicle between interested subscriber workloads. To do this, eCAL is configured to use shared memory on the localhost.

The following visualization shows the architecture of the example scenario, including all workloads and information flow.

![Sample scenario sideseeings](scenario.drawio.svg)

## Run

Adjust the mount path of `coordinates_publisher` to use an absolute path to the coordinates file inside the [Ankaios manifest](config/startConfig.yaml). Replace the path `/path/to/ankaios_ecal/coordinates_publisher/assets/trk_files/route_nuernberg.csv` through the absolute path.

The examples can be run by executing the following script, which builds all the workloads with the podman runtime and starts Ankaios with a predefined [Ankaios manifest](config/startConfig.yaml) containing all the built workloads:

```shell
./run.sh
```

Afterwards, open your web browser (Google Chrome) and go to [http://localhost:5500](http://localhost:5500).

In addition, open a new terminal window and execute the `ank get workloads` command every 1 second to follow the `sideseeing_generator` workload started by the `sideseeing_starter` workload after a few seconds (approx. 20 sec). When the workload is up and running the sideseeings shall be visible on the web ivi.

```shell
watch -n 1 ank get workloads
```

## Shutdown

Press Ctr + C in the terminal window where the `run.sh` script is running. Do not just exit the terminal window, it is not guaranteed that the Ankaios server and Ankaios agent with all the workloads on the podman runtime are canceled properly. If you have accidentially exited the terminal window, just run `shutdown.sh` script manually in a new terminal window. It cleans up everything again.

## Change the route of the vehicle

A simple csv file is provided containing latitude and longitude coordinates.

```shell
# coordinates_publisher/assets/trk_files/route_nuernberg.csv
latitude,longitude
49.43814,11.117565
49.438233,11.117296
49.438346,11.116884
...
```

You can generate a new route and put the coordinates in the same csv file structure into another a file inside `coordinates_publisher/assets/trk_files` and adjust the Ankaios manifest to instruct the `coordinates_publisher` to use that new route file.

Adjust this line and replace `<new_trk_file>.csv` with the new file name:

```yaml
# line 14
coordinates_publisher:
...
  runtimeConfig:
    ...
    commandOptions: ["--ipc=host", "--pid=host", "--network=host", "-v", "/path/to/coordinates_publisher/assets/trk_files/<new_trk_file>.csv:/trk_files/trk.csv", "--name", "coordinates_publisher"]
...
```

To generate a new route the open osm.router-project.org API is used. Go to google maps or your favourite maps API and select some source and destination longitude/latitude coordinates and execute the following script inside the tools folder after entering the `coordintates_publisher` devcontainer:

```shell
python3 tools/generate_route.py --output assets/trk_files/new_route_file.csv 49.44215 11.111729 49.443540 11.110035
```

The first the latitude/longitude pair represents the source and the second latitude/longitude pair is the destination (use -h of the python script to display the argument information). The script uses the osm.router-project API to generate a route between the source and destination and writes the output to a csv file containing the latitude and longitude coordinates of the whole route.

Recommendation: Keep the route short otherwise you have a long runtime because the coordinates_publisher publishes lat/lon coordinates every 1 sec.

Adjust the path like mentioned above inside the Ankaios manifest to point to your new csv file containing the coordinates of the new generated route.

## Extend the previous challenge

If you search for some challenge, then develop a new workload that publishes the speed value of the current lat/lon coordinate with Eclipse eCAL. The `web_ivi` can then subscribe on the speed values and can adjust the speed inside the speedometer according to the received speed value.

A good starting point to receive speed values for a lat/lon coordinate is to use the following code snippet using the overpass-api:

```python
# Function to query Overpass API for speed limits
def query_speed_limits(lat, lon):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    way(around:50,{lat},{lon})["maxspeed"];
    out body;
    """
    response = requests.post(overpass_url, data={'data': overpass_query})
    data = response.json()
    speed_limits = []
    for element in data['elements']:
        if 'maxspeed' in element['tags']:
            speed_limits.append(element['tags']['maxspeed'])
    return speed_limits
```

Feel free to create own challenges or modifications.