import multiprocessing
import zmq
import logging
import json
from enum import Enum, auto
import time
import os, json
import paho.mqtt.client as mqtt
import random 
from datetime import datetime

context = zmq.Context()
logger = logging.getLogger("main.message_printer")

class MQTT_forwarding_print(multiprocessing.Process):
    def __init__(self, config, zmq_conf):
        super().__init__()


        self.name = config["Factory"]["name"]
        self.config_lab = config["Factory"]

        mqtt_conf = config['internal_layer']['mqtt']
        self.url = mqtt_conf['broker']
        self.port = int(mqtt_conf['port'])
        self.topic = mqtt_conf["topic_print"]
        
        self.topic_base = mqtt_conf['base_topic_template']

        self.initial = mqtt_conf['reconnect']['initial']
        self.backoff = mqtt_conf['reconnect']['backoff']
        self.limit = mqtt_conf['reconnect']['limit']
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


    def mqtt_connect(self, client, first_time=False):
        timeout = self.initial
        exceptions = True
        while exceptions:
            try:
                if first_time:
                    client.connect(self.url, self.port, 60)
                else:
                    logger.error("Attempting to reconnect...")
                    client.reconnect()
                logger.info("Connected!")
                time.sleep(self.initial)  # to give things time to settle
                exceptions = False
            except Exception:
                logger.error(f"Unable to connect, retrying in {timeout} seconds")
                time.sleep(timeout)
                if timeout < self.limit:
                    timeout = timeout * self.backoff
                else:
                    timeout = self.limit

    def on_disconnect(self, client, _userdata, rc):
        if rc != 0:
            logger.error(f"Unexpected MQTT disconnection (rc:{rc}), reconnecting...")
            self.mqtt_connect(client)

    def run(self):
        logger.info("Starting")
        self.do_connect()
        client =mqtt.Client()
        client.on_disconnect = self.on_disconnect
        self.mqtt_connect(client, True)
        logger.info("ZMQ Connected")
        run = True
        while run:
            while self.zmq_in.poll(500, zmq.POLLIN):
                msg = self.zmq_in.recv()
                try: 
                    msg = msg.decode("utf-8")
                except:
                    msg =msg
                
                if type(msg)== str:
                    msg_json = json.loads(msg)
                else:
                    msg_json = msg
                print("MQTT_processing: mess recieved to process")
                print(type(msg_json))
                msg_send = self.messeage_for_label(msg_json, self.config_lab)
                topic = self.topic + self.name + "/"
                #data = [topic, msg_send]
                logger.info("AAS sending with topic: " + topic)
                out = json.dumps(msg_send)
                client.publish(topic, out)
                logger.info("Sent")
    
    def messeage_for_label(self, msg_in, config):
        #process the data for printer format
        payload = {}
        payload["timestamp"] = "2024-02-29T09:49:20+00:00"
        payload["id"] = "line_1"
        payload["labelItems"] = []
        name = self.findName(msg_in)
        labelItem2 = {}
        labelItem2["labelType"] = "text"
        labelItem2["labelKey"] = name
        labelItem2["labelValue"] = "Sustainability Data"
        payload["labelItems"].append(labelItem2)
        labelItem2 = {}
        labelItem2["labelType"] = "text"
        labelItem2["labelKey"] = "From: " + config["name"]
        labelItem2["labelValue"] = ""
        payload["labelItems"].append(labelItem2)
        labelItem2 = {}
        labelItem2["labelType"] = "QRAAS"
        labelItem2["labelKey"] = name
        labelItem2["labelValue"] = msg_in
        payload["labelItems"].append(labelItem2)

        return payload
    
    def findName(self, msg_in):
        if msg_in[0]["idShort"]:
            name = msg_in[0]["idShort"]
        elif msg_in[0]["submodelElements"][0]["value"][2]["value"]:
            name = msg_in[0]["submodelElements"][0]["value"][2]["value"]
        else:
            name = "AAS name not found"
        return name

    
                    
        