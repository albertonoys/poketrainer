#!/usr/bin/env python
"""
pgoapi - Pokemon Go API
Copyright (c) 2016 tjado <https://github.com/tejado>
Modifications Copyright (c) 2016 j-e-k <https://github.com/j-e-k>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.

Author: tjado <https://github.com/tejado>
Modifications by: j-e-k <https://github.com/j-e-k>
"""

import os
import re
import json
import struct
import logging
import requests
import argparse
from time import sleep
from pgoapi import PGoApi
from pgoapi.utilities import f2i, h2f
from pgoapi.location import getNeighbors

from google.protobuf.internal import encoder
from geopy.geocoders import GoogleV3
from s2sphere import CellId, LatLng

log = logging.getLogger(__name__)
from threading import Thread
from Queue import Queue
from web import run_web
def get_pos_by_name(location_name):
    geolocator = GoogleV3()
    loc = geolocator.geocode(location_name)

    log.info('Your given location: %s', loc.address.encode('utf-8'))
    log.info('lat/long/alt: %s %s %s', loc.latitude, loc.longitude, loc.altitude)

    return (loc.latitude, loc.longitude, loc.altitude)

def init_configs():
    parser = argparse.ArgumentParser()
    config_file = "config.json"

    # If config file exists, load variables from json
    load = {}
    if os.path.isfile(config_file):
        with open(config_file) as data:
            load.update(json.load(data))

    # Read passed in Arguments
    parser.add_argument("-a", "--accounts", help="config_index", nargs='+', default=[0], type=int)
    # parser.add_argument("-d", "--debug", help="Debug Mode", action='store_true')
    # parser.set_defaults(DEBUG=False)
    config = parser.parse_args()
    loaded = [load['accounts'][i] for i in config.accounts]
    # Passed in arguments shoud trump
    return loaded


def main():
    # log settings
    # log format
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')
    # log level for http request class
    logging.getLogger("requests").setLevel(logging.WARNING)
    # log level for main pgoapi class
    logging.getLogger("pgoapi").setLevel(logging.INFO)
    # log level for internal pgoapi class
    logging.getLogger("rpc_api").setLevel(logging.INFO)

    # FIXME
    # if config.debug:
    #     logging.getLogger("requests").setLevel(logging.DEBUG)
    #     logging.getLogger("pgoapi").setLevel(logging.DEBUG)
    #     logging.getLogger("rpc_api").setLevel(logging.DEBUG)
    queues = {}
    for config in init_configs():
        queues[config["username"]] = Queue()
        position = get_pos_by_name(config['location'])
        # instantiate pgoapi
        pokemon_names = json.load(open("pokemon.en.json"))
        api = PGoApi(config, pokemon_names)

        # provide player position on the earth
        api.set_position(*position)
        if not api.login(config["auth_service"], config["username"], config["password"], config.get("cached",False)):
            return
        try:
            t = Thread(target=api.main_loop, args=[queues[config["username"]]])
            t.daemon = True
            t.start()
        except Exception as e:
            log.error('Error in main loop, restarting %s', e)
            # restart after sleep
            sleep(30)
            main()
    run_web(queues)
    t.join(1)
if __name__ == '__main__':
    main()
