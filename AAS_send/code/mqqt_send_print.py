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
logger = logging.getLogger("main.message_rewriter")


class MQTT_forwarding(multiprocessing.Process):
    def __init__(self, config, zmq_conf):
        super().__init__()

        self.name = config["Factory"]["name"]
        self.mqqt_rec = config["printer_send"]

        # declarations
        self.zmq_conf = zmq_conf
        self.zmq_in = None

    def do_connect(self):
        self.zmq_in = context.socket(self.zmq_conf['in']['type'])
        if self.zmq_conf['in']["bind"]:
            self.zmq_in.bind(self.zmq_conf['in']["address"])
        else:
            self.zmq_in.connect(self.zmq_conf['in']["address"])


    def run(self):
        logger.info("Starting")
        self.do_connect()
        logger.info("ZMQ Connected")
        run = True
        while run:
            while self.zmq_in.poll(500, zmq.POLLIN):
                msg = self.zmq_in.recv()
                msg_json = json.loads(msg)
                print("MQTT_processing: mess recieved to process")
                msg_send = self.messeage_process(msg_json)
                for reciever in self.mqqt_rec:
                    topic = reciever["topic"] + self.name
                    self.message_send(reciever["url"], reciever["port"], topic, msg_send)
                
    def message_send(host, port, topic, msg):
        try:
            client =mqtt.Client("aas_test" +str(random.randrange(1,1000)))
            client.connect(host, port)
            out = json.dumps(msg)
            client.publish(topic,out)
        except Exception:
            print(Exception)
    
    def messeage_for_label(self, msg_in, config_label):
        # process the data for printer format
        payload = {}
        payload["timestamp"] = "2024-02-29T09:49:20+00:00"
        payload["id"] = "line_1"
        payload["labelItems"] = []
        name = self.findName(msg_in)
        labelItem2 = {}
        labelItem2["labelType"] = name
        labelItem2["labelKey"] = "Sustainability Data"
        labelItem2["labelValue"] = "Manual Assembly" 
        payload["labelItems"].append(labelItem2)
        labelItem2 = {}
        labelItem2["labelType"] = "QRAAS"
        labelItem2["labelKey"] = "12345"
        labelItem2["labelValue"] = msg_in
        payload["labelItems"].append(labelItem2)

        return payload
    
    def findName(self, msg_in):
        if msg_in["idShort"]:
            name = msg_in["idShort"]
        elif msg_in[0]["submodelElements"][0]["value"][2]["value"]:
            name = msg_in[0]["submodelElements"][0]["value"][2]["value"]
        else:
            name = "AAS name no found"
        return name

    
                    
        