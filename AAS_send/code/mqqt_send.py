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
        self.mqqt_rec = config["mqqt_send"]

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
    
    def messeage_process(self, msg_in):
        # reverse of above function
        newMess = msg_in
        return newMess
    
                    
        