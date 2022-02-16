# MAVLink UTM_GLOBAL_POSITION Simulator
Generate MAVLink [UTM_GLOBAL_POSITION](https://mavlink.io/en/messages/common.html#UTM_GLOBAL_POSITION) messages from a CSV with the corresponding data.


## Installation
Clone this repository and install the python dependencies with `pip3 install -r requirements.txt`.


## Usage
This utilit generates UTM_GLOBAL_POSITION by replaying a CSV file with the required data fields in a loop.

The output connection strings are according to the PyMavlink library, e.g.:
- `udpin:$ip:$port`: Listening for UDP packets on the specified IP (normally 0.0.0.0) and port
- `udpout:$ip:$port`: Sending UDP packets to the specified IP and port, will start with a heartbeat to "activate" the connection when using mavlink-router
- `tcp:$ip:$port`: Connecting to the specified IP and port

To fetch data form `/path/to/file.csv` and send it to `localhost:14550`, run:
```shell
python3 mavlink_utm_sim.py -i /path/to/file.csv -o udpout:localhost:14550
```

The CSV must contain these colums:
```csv
TODO
```

Data is in standard units (meters, degrees, m/s) and is converted to the fixed point version internally.
