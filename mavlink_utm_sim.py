#!/usr/bin/env python3
"""
D2X Demos - MAVLink UTM_GLOBAL_POSITION/ GLOBAL_POSITION_INT Simulator

Generate MAVLink UTM_GLOBAL_POSITION and/or GLOBAL_POSITION_INT messages from CSV file.

Author:    Jannik Beyerstedt <beyerstedt@consider-it.de>
Copyright: (c) consider it GmbH, 2022 - 2023
License:   MIT
"""

import argparse
import csv
import logging
import sys
import time
from pymavlink.dialects.v20 import common as mavlink
import pymavlink.mavutil as mavutil

OWN_SYSID = 1
OWN_COMPID = 0
UDP_CONNECT_TIMEOUT = 10

POS_INTERVAL_MS = 250
UTM_INTERVAL_MS = 1000  # must be a multiple of POS_INTERVAL_MS


if __name__ == "__main__":
    log_format = '%(asctime)s %(levelname)s:%(name)s: %(message)s'
    log_datefmt = '%Y-%m-%dT%H:%M:%S%z'
    logging.basicConfig(format=log_format, datefmt=log_datefmt, level=logging.INFO)
    logger = logging.getLogger()

    parser = argparse.ArgumentParser(description='MAVLink UTM_GLOBAL_POSITION/ GLOBAL_POSITION_INT Generator')
    parser.add_argument("-i", "--input", required=True,
                        help="CSV file path")
    parser.add_argument("-o", "--output", required=True,
                        help="output connection address, e.g. tcp:$ip:$port, udpout:$ip:$port")
    parser.add_argument("-s", "--sysID", type=int,
                        help="just use data from the specified system ID")
    parser.add_argument("--ardupilot", action='store_true',
                        help="Only send GLOBAL_POSITION_INT")
    parser.add_argument("-v", "--verbosity", action="count",
                        help="increase output and logging verbosity")
    args = parser.parse_args()

    if args.verbosity == 2:
        logger.setLevel(logging.DEBUG)
    elif args.verbosity == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    # SETUP
    input_data = []

    # read CSV file
    with open(args.input, newline='') as csvfile:
        csv.register_dialect('strip', skipinitialspace=True)
        reader = csv.DictReader(csvfile, dialect='strip')
        for row in reader:
            input_data.append(row)

     # open MAVLink output
    logger.info("Starting MAVLink connection to %s", args.output)
    try:
        mav_out = mavutil.mavlink_connection(
            args.output, source_system=OWN_SYSID, source_component=OWN_COMPID)
    except OSError:
        logger.error("MAVLink connection failed, exiting")
        sys.exit(-1)

    # RUN
    utm_flags = mavlink.UTM_DATA_AVAIL_FLAGS_TIME_VALID + \
        mavlink.UTM_DATA_AVAIL_FLAGS_UAS_ID_AVAILABLE + \
        mavlink.UTM_DATA_AVAIL_FLAGS_POSITION_AVAILABLE + \
        mavlink.UTM_DATA_AVAIL_FLAGS_ALTITUDE_AVAILABLE + \
        mavlink.UTM_DATA_AVAIL_FLAGS_RELATIVE_ALTITUDE_AVAILABLE + \
        mavlink.UTM_DATA_AVAIL_FLAGS_HORIZONTAL_VELO_AVAILABLE + \
        mavlink.UTM_DATA_AVAIL_FLAGS_VERTICAL_VELO_AVAILABLE

    utm_flight_state = mavlink.UTM_FLIGHT_STATE_AIRBORNE

    MSGS_OVERSAMPLING = int(UTM_INTERVAL_MS / POS_INTERVAL_MS)
    START_TIME = time.time()

    while True:
        for row in input_data:
            logger.debug("IN: %s N, %s E, %s m, %s rel_alt; %s, %s, %s m/s; %s h_acc, %s v_acc, %s vel_acc", row['lat'], row['lon'], row['alt'], row['relative_alt'], row['vx'],
                         row['vy'], row['vz'], row['h_acc'], row['v_acc'], row['vel_acc'])

            uas_id = bytes.fromhex(row['uas_id'])

            for _ in range(MSGS_OVERSAMPLING):
                pos_msg = mavlink.MAVLink_global_position_int_message(
                    int((time.time()-START_TIME)*1E3),      # Time since boot (uint32_t, ms)
                    int(float(row['lat'])*1E7),             # lat (int32_t, degE7)
                    int(float(row['lon'])*1E7),             # lon (int32_t, degE7)
                    int(float(row['alt'])*1000),            # alt (int32_t, mm)
                    int(float(row['relative_alt'])*1000),   # alt AGL (int32_t, mm)
                    int(float(row['vx'])*100),              # speed north (int16_t, cm/s)
                    int(float(row['vy'])*100),              # speed east (int16_t, cm/s)
                    int(float(row['vz'])*100),              # speed down (int16_t, cm/s)
                    int(65535)                              # heading (uint16_t, cdeg)
                )

                mav_out.mav.send(pos_msg)
                logger.info("OUT: %s", pos_msg)

                time.sleep(POS_INTERVAL_MS/1000)

            if not args.ardupilot:
                utm_msg = mavlink.MAVLink_utm_global_position_message(
                    int(time.time()*1E6),                   # Time unix epoch (uint64_t, us)
                    list(uas_id),                           # Unique UAS ID (uint8_t[18])
                    int(float(row['lat'])*1E7),             # lat (int32_t, degE7)
                    int(float(row['lon'])*1E7),             # lon (int32_t, degE7)
                    int(float(row['alt'])*1000),            # alt (int32_t, mm)
                    int(float(row['relative_alt'])*1000),   # alt AGL (int32_t, mm)
                    int(float(row['vx'])*100),              # speed north (int16_t, cm/s)
                    int(float(row['vy'])*100),              # speed east (int16_t, cm/s)
                    int(float(row['vz'])*100),              # speed down (int16_t, cm/s)
                    int(float(row['h_acc'])*1000),          # stddev horiz. (uint16_t, mm)
                    int(float(row['v_acc'])*1000),          # stddev alt (uint16_t, mm)
                    int(float(row['vel_acc'])*1000),        # stddev speed (uint16_t, cm/s)
                    0,                                      # Next waypoint lat (int32_t, degE7)
                    0,                                      # Next waypoint lon (int32_t, degE7)
                    0,                                      # Next waypoint alt (int32_t, mm)
                    0,                                      # Time until next update (uint16_t, cs)
                    utm_flight_state,                       # flight state (uint8_t, UTM_FLIGHT_STATE)
                    utm_flags                               # data available flags (uint8_t, UTM_DATA_AVAIL_FLAGS)
                )

                mav_out.mav.send(utm_msg)
                logger.info("OUT: %s", utm_msg)
