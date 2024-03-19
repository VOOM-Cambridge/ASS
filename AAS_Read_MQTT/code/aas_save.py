import multiprocessing
import zmq
import logging
import json
from enum import Enum, auto
import time
import os, json
import paho.mqtt.client as mqtt
import random 

context = zmq.Context()
logger = logging.getLogger("aas_save")


class AAS_save(multiprocessing.Process):
    def __init__(self, config, zmq_conf):
        super().__init__()

        self.name = config["Factory"]["name"]
        self.directory = "" 
        self.constants = []
        # declarations
        self.zmq_conf = zmq_conf
        self.zmq_in = None

    def do_connect(self):
        self.zmq_in = context.socket(self.zmq_conf['in']['type'])
        if self.zmq_conf['in']["bind"]:
            self.zmq_in.bind(self.zmq_conf['in']["address"])
        else:
            self.zmq_in.connect(self.zmq_conf['in']["address"])

    def findCurrentStore(self):
        path = os.getcwd()
        if not self.folder_exists(path, "AAS_data"):
            parent = os.path.abspath(os.path.join(path, os.pardir))
            if not self.folder_exists(parent, "AAS_data"):
                script_dir = os.path.abspath(os.path.join(parent, os.pardir))
            else:
                script_dir = parent
        else:
            script_dir = path
        return script_dir

    def folder_exists(self, directory, folder_name):
        # Get the current working directory
        # Construct the path to the folder
        folder_path = os.path.join(directory, folder_name)
        # Check if the folder exists
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            return True
        else:
            return False
        
    def file_exists(self, directory, filename):
        filepath = os.path.join(directory, filename)
        return os.path.exists(filepath)

    def save(self, fileData):
        logger.info("start saving")
        AAS = fileData
        logging.info(type(AAS))
        
        try:
            # Decode the message payload
            AAS = json.loads(AAS["AAS data"])
            logging.info(type(AAS))

            name = "unkown"
            try:
                name = AAS[0]["idShort"]
            except:
                name = "unkown"
            logging.info(name)
            i = 1
            while self.file_exists(self.directory, name + ".json"):
                print("Directory  exisits")
                name = name + str(i)
                i = i +1

            filename = name + ".json"
            filepath = os.path.join(self.directory, filename)
            
            with open(filepath, 'w') as file:
                json.dump(AAS, file, indent=4)
            print(f"Message saved to {filepath}")
            logger.info("Messaege saved")
        except Exception as e:
            print("Error:", e)

    def run(self):
        logger.info("Starting")
        self.do_connect()
        dir = self.findCurrentStore()
        self.directory = os.path.join(dir, "AAS_data/in/")
        logger.info("ZMQ Connected")
        run = True
        while run:
            while self.zmq_in.poll(500, zmq.POLLIN):
                msg = self.zmq_in.recv()
                msg_json = json.loads(msg)
                logging.info(type(msg_json))
                print("MQTT_saving: mess recieved to save")
                try:
                    self.save(json.loads(msg_json))
                except:
                    self.save(msg_json)
                 
        