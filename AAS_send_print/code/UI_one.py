import os
from flask import Flask, redirect, url_for, render_template, request, jsonify
import zmq
import json, time
import logging
import multiprocessing
from enum import Enum, auto
import time
import paho.mqtt.client as mqtt
import random 
from datetime import datetime

context = zmq.Context()
app = Flask(__name__)
logger = logging.getLogger("UI_single")

class App:
    def __init__(self, config, zmq_conf, typeIn):
        self.app = Flask(__name__)
        self.zmq_conf = zmq_conf
        main_direc = self.findCurrentStore()
        AAS_direc = "AAS_data/order/"
        self.files_folder = os.path.join(main_direc, AAS_direc)
        print(self.files_folder)
        self.findFiles()
        self.text = ""
        self.textOut = ""
        self.typeIn = typeIn
        
        if self.typeIn == "mqtt" or self.typeIn == "MQTT":
            self.config_mqtt = config['external_layer']['mqtt']
        elif self.typeIn == "Printing":
            self.config_mqtt = config['internal_layer']['mqtt']

        self.name = config["Factory"]["name"]
        self.config_lab = config["Factory"]
        
        self.url = self.config_mqtt['broker']
        self.port = int(self.config_mqtt['port'])
        self.topic = self.config_mqtt["topic"]
        self.client = mqtt.Client()
        self.topic_base = self.config_mqtt['base_topic_template']
        self.initial = self.config_mqtt['reconnect']['initial']
        self.backoff = self.config_mqtt['reconnect']['backoff']
        self.limit = self.config_mqtt['reconnect']['limit']
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_publish
        self.portIn = self.config_mqtt['portIn']
        #self.client_Ex.on_connect = self.onConnectEx
        self.connected_flag= False
        self.mqtt_connect(True)
        #self.client_ex.connect(self.url, self.port)

        self.setup_routes()

    def findFiles(self):
        files = os.listdir(self.files_folder)
        new_files =[]
        for file in files:
            new_files.append(file[:-5])
        self.newFiles = new_files
        
    def setup_routes(self):
        @self.app.route('/')
        def index():
            self.findFiles()
            #self.connect()
            return render_template('indexOne.html', files=self.newFiles, text = self.text,  typeIn= self.typeIn)

        @self.app.route('/submit', methods=['POST'])
        def submit():
            self.findFiles()
            selected_file = request.form['file']
            self.send_file_mess(selected_file)
            self.text = selected_file
            return redirect(url_for('index'))

        @self.app.route('/check_connection', methods=['GET'])
        def check_connection():
            connected = self.connected_flag
            print(connected)
            if not connected:
                self.mqtt_connect()
            return jsonify({'connected': connected})


    def start(self):
        logger.info("Starting")
        self.app.run(debug=True,host="0.0.0.0",port=self.portIn)
    

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
        folder_path = os.path.join(directory, folder_name)
        # Check if the folder exists
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            return True
        else:
            return False
        
    def on_publish(self, client, userdata, mid, reason_code, properties):
        
        print("Published")
        logger.info("Published")
        
    def file_exists(self, directory, filename):
        filepath = os.path.join(directory, filename)
        return os.path.exists(filepath)
    
    def send_file_mess(self, fileName):
        fileName = fileName + ".json"
        file_path = os.path.join(self.files_folder, fileName)
        # Print the new file
        print("New AAS detected:", fileName)
        logging.info("New AAS detected:")
        # send files on to next
        with open(file_path, encoding="utf-8") as json_file:
            json_data = json.load(json_file)
            logging.info(json_file)
        #msg_payload = json.dumps(json_data)
        #self.zmq_out.send_json(json_data)
        if self.typeIn == "mqtt" or self.typeIn == "MQTT":
            self.send_mqtt(json_data)
        elif self.typeIn == "Printing":
            self.send_mqtt_print(json_data)
        logging.info("sent")
        

    def mqtt_connect(self, first_time=False):
        timeout = self.initial
        name = "Internal"
        try:
            if first_time:
                self.client.connect(self.url, self.port, 60)
                self.connected_flag = True
            else:
                logger.error("Attempting to reconnect to broker")
                self.client.reconnect()
                self.connected_flag = True  # Set flag if reconnection succeeds
            logger.info("Connected to broker !")
            time.sleep(self.initial)  # to give things time to settle
        except Exception:
            logger.error(f"Unable to connect to {name}, retrying in {timeout} seconds")
            time.sleep(timeout)
            if timeout < self.limit:
                timeout = timeout * self.backoff
            else:
                timeout = self.limit

    def on_disconnect(self, client, _userdata, rc):
        self.connected_flag=False
        if rc != 0:
            logger.error(f"Unexpected MQTT disconnection (rc:{rc}), reconnecting...")
            self.mqtt_connect()

    def send_mqtt_print(self, msg_json):
        logger.info("MQTT_processing: mess recieved to process")
        msg_send = self.messeage_for_label(msg_json, self.config_lab)
        topic = self.topic + self.name + "/"
        #data = [topic, msg_send]
        logger.info("AAS sending with topic: " + topic)
        out = json.dumps(msg_send)
        if not self.connected_flag:
            self.mqtt_connect
        self.client.publish(topic, out, 1)
        logger.info("Sent to printer")
    
    def send_mqtt(self, msg_json):
        logger.info("MQTT_processing: mess recieved to process")
        topic = self.topic + self.name + "/"
        #data = [topic, msg_send]
        logger.info("AAS sending with topic: " + topic)
        out = json.dumps(msg_json)
        if not self.connected_flag:
            self.mqtt_connect
        self.client.publish(topic, out, 1)
        logger.info("Sent MQTT")

    
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
            name = self.checkX(msg_in[0]["idShort"])
        elif msg_in[0]["submodelElements"][0]["value"][2]["value"]:
            name = msg_in[0]["submodelElements"][0]["value"][2]["value"]
        else:
            name = "AAS name not found"
        return name
    
    def checkX(self, name):
        if name[0] == "x" or name[0] == "X":
            name = name[1:]
        return name

