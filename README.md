# In-vehicle sideseeing generator demo

The repository contains a blueprint for implementing a sample scenario using [Eclipse Ankaios](https://eclipse-ankaios.github.io/ankaios/0.3/) and [Eclipse eCAL](https://eclipse-ecal.github.io/ecal/).

The sample scenario is to generate sideseeing information when the vehicle is within a city. The sideseeing information is displayed in the user's virtual cockpit (IVI), which is in this case a web-based demo IVI and accessible through the user's browser. When the vehicle leaves the city, no sideseeing information is displayed anymore.

This means that an application (sideseeing generator) is required which, depending on the current location of the vehicle, downloads information about sideseeings from the internet and publishes it so that the sideseeing data can be displayed in the demo IVI. Thus, to save resources in the vehicle, the sideseeing generator only needs to run when the vehicle is within a city, otherwise not. A software orchestrator such as [Eclipse Ankaios](https://eclipse-ankaios.github.io/ankaios/0.3/), which is optimized for these types of tasks in the automotive sector, facilitates the dynamic launch of applications with all their dependencies.

In addition, a modern software-defined vehicle (SDV) benefits from fast updates of individual applications and many new features that are loaded into the vehicle on-the-fly. The challenges arise in managing and maintaining the increasing number of dependencies and third-party libaries that an application has today. Containerized applications meet these challenges, because they encapsulate software and its dependencies into lightweight, consistent units that can run seamlessly across various computing environments. They are portable and implicitly support simple versioning and visibility of all dependencies at a glance. Containerized applications are therefore used for the sideseeing example scenario.

Another challenge is the ever-increasing flow of information in modern vehicles. Even for this sideseeing scenario certain applications need the information about vehicle position (latitude/longitude), a field indicating whether the vehicle is within the city and the sideseeing data itself. And in some scenarios multiple subscribers on the same data are required. Thus, fast middleware is needed that forwards the information to the interested applications. [Eclipse eCAL](https://eclipse-ecal.github.io/ecal/) is such a middleware, optimized for use in the vehicle. It follows the publish/subscribe approach with an easy-to-use API and manages inter-process data exchange, as well as inter-host communication. 

The following visualization shows the architecture of the sideseeing sample scenario, including all applications and information flow. In the following, a containerized application are referred to as a workload, as an application that is managed by [Eclipse Ankaios](https://eclipse-ankaios.github.io/ankaios/0.3/) is designated as such.

![Workload Architecture Sideseeings](assets/scenario_light_mode.drawio.svg#gh-light-mode-only)
![Workload Architecture Sideseeings](assets/scenario_dark_mode.drawio.svg#gh-dark-mode-only)

The Ankaios server is started with an initial Ankaios manifest containing configuration of all grey colored workloads. These workloads are assigned to an Ankaios agent and are started initially. The `Coordinates Publisher` reads latitude/longitude coordinates from a csv file and publishes those coordinates each second using the [Eclipse eCAL](https://eclipse-ecal.github.io/ecal/) middleware. The `Sideseeing Starter` workload subscribes on the coordinates and checks for each coordinate via the [Nominatim API](https://nominatim.org/release-docs/develop/) if the vehicle is within a city or not. Once the vehicle is detected as within a city it starts the `Sideseeing Generator` workloads dynamically by instructing Eclipse Ankaios to create the new workload. To send requests to Eclipse Ankaios the workload uses the so-called [Control Interface](https://eclipse-ankaios.github.io/ankaios/0.3/reference/control-interface/) of Ankaios. The `Sideseeing Starter` instructs Ankaios to delete the `Sideseeing Generator` workload when it detects that the current coordinate is not within a city (e.g. on a highway). The `Sideseeing Generator` uses the open source [Overpass API](https://dev.overpass-api.de/overpass-doc/en/preface/preface.html) (copy of OpenStreetMap) to fetch sideseeing information around 5km of the current lat/lon coordinate of the vehicle. Since the demo `Web IVI` needs to know the information when to display the sideseeing data or not, it subscirbes on a topic about a boolean field indicating if the vehicle is within a city or not. For simplicitly the `Sideseeing Starter` publishes this boolean field since it already has this information. The `Web IVI` subscribes on the sideseeing data and displays it in the web browser of the user. It uses server-side events to send the received sideseeing data to the ivi running inside user's web browser.

**Please note:** Eclipse Ankaios supports multi-node setups within its [architecture](https://eclipse-ankaios.github.io/ankaios/0.3/architecture/) including one Ankaios server and multiple Ankaios agents. For simplicitly only one agent on the same host of the server (all localhost) is used. Feel free to change the scenario to use a multi-node setup by adding more Ankaios agents similar like done in this [Ankaios base tutorial](https://eclipse-ankaios.github.io/ankaios/0.3/usage/tutorial-vehicle-signals/).

**Please note:** The [Overpass API](https://dev.overpass-api.de/overpass-doc/en/preface/preface.html) is used for simplicitly because it is free and no API key is needed. In addition, the [Nominatim API](https://nominatim.org/release-docs/develop/) provides a Python lib already. Keep in mind that the meta data of the [Nominatim API](https://nominatim.org/release-docs/develop/) contains not the exact information whether a vehicle is within a city or not, the code tries to use as strict checks as possible to determine it. But an outcome might not be as expected. Feel free to improve the code or introduce a different API.

## Prerequisites

- Linux as operating system or WSL2 on Windows (tested on Ubuntu-22.04)
- Eclipse Ankaios [v0.3.1](https://eclipse-ankaios.github.io/ankaios/0.3/usage/installation/)
- [Podman](https://podman.io/docs/installation) v4.6 or newer as the container runtime used by [Eclipse Ankaios](https://eclipse-ankaios.github.io/ankaios/0.3/)

Please note that all workloads are setup to use the host's network IPC and PID namespace for simplicitly and that Eclipse eCAL uses the fast shared memory approach to send and receive data.

## Run

Adjust the mount path of the `coordinates_publisher` workload inside the [Ankaios manifest](config/startConfig.yaml) to use an absolute path to the coordinates file. Replace the path `/path/to/ankaios_ecal/coordinates_publisher/assets/trk_files/route_nuernberg.csv` with the absolute path.

The examples can be run by executing the following script, which builds all the workloads with the podman runtime and starts [Eclipse Ankaios](https://eclipse-ankaios.github.io/ankaios/0.3/) with all workloads part of the predefined [Ankaios manifest](config/startConfig.yaml).

```shell
./run.sh
```

Afterwards, open your web browser (Google Chrome) and go to [http://localhost:5500](http://localhost:5500).

In addition, open a new terminal window and execute the `ank get workloads` command every 1 second to follow the `sideseeing_generator` workload started by the `sideseeing_starter` workload after a few seconds. When the workload is up and running the sideseeings shall be visible on the web ivi.

```shell
watch -n 1 ank get workloads
```

## Shutdown

Press Ctr + C in the terminal window where the `run.sh` script is running. Do not just exit the terminal window, it is not guaranteed that the Ankaios server and Ankaios agent with all the workloads on the podman runtime are canceled properly. If you have accidentially exited the terminal window, just run `shutdown.sh` script manually in a new terminal window. It cleans up everything again.

## Application logs

In addition or for debugging reasons you can display logs of several applications by using the podman logs command in a separate terminal window.

Example:

```shell
podman logs -f web_ivi
```

Get the names of each workload by executing `podman ps -a` or `ank get workloads` when the scenario runs.

## Eclipse Ankaios logs

For debugging reasons, display the logs of the Software Orchestrator Eclipse Ankaios itself.

For displaying the Ankaios server logs, run the following command in a separate terminal window:

```shell
tail -f /tmp/ankaios-server.log
```

Or for the Ankaios agent:

```shell
tail -f /tmp/ankaios-agent_A.log
```

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

You can generate a new route csv file containing latitude and longitude coordinates that the `coordinates_publisher` will use.

To generate a new route the open osm.router-project.org API is used. Go to google maps or your favourite maps API and select some source and destination longitude/latitude coordinates and execute the following script inside the tools folder after entering the `coordintates_publisher` devcontainer:

```shell
python3 tools/generate_route.py --output assets/trk_files/new_route_file.csv 49.44215 11.111729 49.443540 11.110035
```

The first the latitude/longitude pair represents the source and the second latitude/longitude pair is the destination (use -h of the python script to display the argument information). The script uses the osm.router-project API to generate a route between the source and destination and writes the output to a csv file containing the latitude and longitude coordinates of the whole route.

Recommendation: Keep the route short otherwise you have a long runtime because the `coordinates_publisher` publishes lat/lon coordinates every 1 sec.

Adjust the [Ankaios manifest](config/startConfig.yaml) to point to your new generated csv route file:

```yaml
# line 14
coordinates_publisher:
...
  runtimeConfig:
    ...
    commandOptions: ["--ipc=host", "--pid=host", "--network=host", "-v", "/path/to/coordinates_publisher/assets/trk_files/<new_trk_file>.csv:/trk_files/trk.csv", "--name", "coordinates_publisher"]
...
```
