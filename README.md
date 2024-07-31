#  Blueprint Eclipse Ankaios and Eclipse eCAL

The repository contains a blueprint to achieve a sample scenario using Eclipse Ankaios and Eclipse eCAL.

The sample scenario is about generating sideseeing information whenever the vehicle enters a city. The sideseeing information is displayed to the user's virtual cockpit (IVI) which is in this case a demo Web IVI running as workload and accessible through the user's browser. When the vehilce leaves the city, then no sideseeing information is visible in the IVI.

To accomplish this use case the software orchestrator Eclipse Ankaios and the pub/sub middleware Eclipse eCAL, both optimized for automotive usage, are used. Eclipse Ankaios acts as software orchestrator and deploys all applications (called workloads in the following) of the scenario as containers on the podman runtime. A software orchestrator enables dynamic starts of workloads. The workload that generates the sideseeing info and publishes the data must only run when the vehicle is within a city. The workload `sideseeing starter` starts the `sideseeing generator` workload when the vehilce enters a city and deletes it when the vehicle leaves the city. It uses the Control Interface of Ankaios to start and stop the workload dynamically. Eclipse eCAL is used to deliver information about the sideseeing and lat/lon positions of the vehicle between the interested subscriber workloads. For this, eCAL is configured to use shared memory on the localhost.

The following visualization shows the architecture of the sample scenario including all workloads and the information flow.

![Sample scenario sideseeings](scenario.drawio.svg)

## Run

Adjust the mount path of `coordinates_publisher` to use an absolute path to the coordinates file inside the [Ankaios manifest](config/startConfig.yaml). Replace the path `/path/to/ankaios_ecal/coordinates_publisher/assets/trk_files/de_erlangen_sideseeing.trk` through the absolute path.

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

A simple csv file is provided containing longitude and latitude coordinates.

```shell
# coordinates_publisher/assets/trk_files/de_erlangen_sideseeing.trk
10.993287735851851,49.588964964568945
10.99349643047723,49.58904967255495
...
```

You can generate a new route and put the coordinates in the same csv file structure into another a file inside `coordinates_publisher/assets/trk_files` and adjust the Ankaios manifest to instruct the `coordinates_publisher` to use that new route file.

Adjust this line and replace `<new_trk_file>.trk` with the new file name:

```yaml
# line 14
coordinates_publisher:
...
  runtimeConfig:
    ...
    commandOptions: ["--ipc=host", "--pid=host", "--network=host", "-v", "/path/to/coordinates_publisher/assets/trk_files/<new_trk_file>.trk:/trk_files/trk.trk", "--name", "coordinates_publisher"]
...
```