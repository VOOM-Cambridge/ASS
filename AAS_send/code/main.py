# Check config file is valid
# create BBs
# plumb BBs together
# start BBs
# monitor tasks

# packages
import tomli
import time
import logging
import zmq
# local

from mqqt_send import MQTT_forwarding
from mqqt_send_print import MQTT_forwarding_print
from check_new import Check_for_new
from userInterface import App
logger = logging.getLogger("main")
logging.basicConfig(level=logging.DEBUG)  # move to log config file using python functionality

def get_config():
    with open("./config/config.toml", "rb") as f:
        toml_conf = tomli.load(f)
    logger.info(f"config:{toml_conf}")
    return toml_conf


def config_valid(config):
    return True


def create_building_blocks(config):
    bbs = {}

    interface = {"type": zmq.PUSH, "address": "tcp://127.0.0.1:4051", "bind": True}
    print_pair = {"type": zmq.PULL, "address": "tcp://127.0.0.1:4051", "bind": False}
    
    check_Out = {"type": zmq.PUSH, "address": "tcp://127.0.0.1:4000", "bind": True}
    print_in = {"type": zmq.PULL, "address": "tcp://127.0.0.1:4000", "bind": False}
    mqtt_in = {"type": zmq.PULL, "address": "tcp://127.0.0.1:4000", "bind": False}
    
    #bbs["check"] = Check_for_new(config, {"out":check_Out})
    
    if config["Factory"]["sending_method"] == "Printing":
        bbs["out"] = MQTT_forwarding_print(config, {"in": print_in})
    elif config["Factory"]["sending_method"] == "MQTT":
        bbs["out"] = MQTT_forwarding(config, {"in": mqtt_in})

    bbs["ui"] = App(config, {"out": interface})
    return bbs


def start_building_blocks(bbs):
    for key in bbs:
        p = bbs[key].start()


def monitor_building_blocks(bbs):
    while True:
        time.sleep(1)
        for key in bbs:
            # logger.debug(f"{bbs[key].exitcode}, {bbs[key].is_alive()}")
            # todo actually monitor
            pass

if __name__ == "__main__":
    conf = get_config()
    # todo set logging level from config file
    if config_valid(conf):
        bbs = create_building_blocks(conf)
        start_building_blocks(bbs)
        monitor_building_blocks(bbs)
    else:
        raise Exception("bad config")
