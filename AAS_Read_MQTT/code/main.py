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
from scanner_find import BarcodeScanner
from aas_save import AAS_save
from wrapper import MQTTServiceWrapper
from processing import DataProcessing


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

    scan_in = {"type": zmq.PUSH, "address": "tcp://127.0.0.1:4001", "bind": True}
    webIn = {"type": zmq.PULL, "address": "tcp://127.0.0.1:4001", "bind": False}
    webOut = {"type": zmq.PUSH, "address": "tcp://127.0.0.1:4000", "bind": True}
    save_in1 = {"type": zmq.PULL, "address": "tcp://127.0.0.1:4000", "bind": False}

    mqtt_in = {"type": zmq.PUSH, "address": "tcp://127.0.0.1:4002", "bind": True} 
    save_in2 = {"type": zmq.PULL, "address": "tcp://127.0.0.1:4002", "bind": False}
    if config["Factory"]["reciving_method"] == "Printing":
        bbs["scan"] = BarcodeScanner(config, {'out': scan_in})
        bbs["pro"] = DataProcessing(config, {'in': webIn, 'out': webOut})
        bbs["save1"] = AAS_save(config, {'in':save_in1})
    elif config["Factory"]["reciving_method"] == "MQTT":
        bbs["mqtt"] = MQTTServiceWrapper(config, {'out': mqtt_in})
        bbs["save2"] = AAS_save(config, {'in':save_in2})
    else:
        scan_in = {"type": zmq.PUB, "address": "tcp://127.0.0.1:4005", "bind": True}
        mqtt_in = {"type": zmq.PUB, "address": "tcp://127.0.0.1:4005", "bind": True} 
        save_in2 = {"type": zmq.SUB, "address": "tcp://127.0.0.1:4005", "bind": False}
        bbs["mqtt"] = MQTTServiceWrapper(config, {'out': mqtt_in})
        bbs["scan"] = BarcodeScanner(config, {'out': scan_in})
        bbs["save2"] = AAS_save(config, {'in1':save_in1})

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
