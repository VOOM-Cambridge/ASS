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
logger = logging.getLogger("UI")

class App:
    def __init__(self, config, zmq_conf, typeIn):
        self.app = Flask(__name__)
        self.zmq_conf = zmq_conf
        main_direc = self.findCurrentStore()
        AAS_direc = "AAS_data/order/"
        self.files_folder = os.path.join(main_direc, AAS_direc)
        print(self.files_folder)
        self.findFiles()
        self.textOut =""
        self.textIn = ""
        self.typeIn = typeIn
        
        if typeIn == "mqtt" or typeIn == "MQTT":
            self.config_mqtt = config['external_layer']['mqtt']
            self.multiple = False
        elif typeIn == "Printing":
            self.config_mqtt = config['internal_layer']['mqtt']
            self.multiple = False
        else: #typeIn == "Both"
            self.multiple = True


        self.name = config["Factory"]["name"]
        self.config_lab = config["Factory"]

        self.config_mqtt_out = config['external_layer']['mqtt']
        self.url_Ex = self.config_mqtt_out['broker']
        self.port_Ex = int(self.config_mqtt_out['port'])
        self.topic_Ex = self.config_mqtt_out["topic"]
        self.client_Ex = mqtt.Client()
        self.topic_base = self.config_mqtt_out['base_topic_template']
        self.initial = self.config_mqtt_out['reconnect']['initial']
        self.backoff = self.config_mqtt_out['reconnect']['backoff']
        self.limit = self.config_mqtt_out['reconnect']['limit']
        self.client_Ex.on_disconnect = self.on_disconnectIn
        self.client_Ex.on_publish = self.on_publish
        #self.client_Ex.on_connect = self.onConnectEx
        self.connected_flag_Ex= False
        self.mqtt_connectOut( True)
        #self.client_ex.connect(self.url, self.port)
        self.config_mqtt_int = config['internal_layer']['mqtt']
        self.url_Int = self.config_mqtt_int['broker']
        self.port_Int = int(self.config_mqtt_int['port'])
        self.topic_Int = self.config_mqtt_int["topic"]
        self.client_Int = mqtt.Client()
        self.client_Int.on_disconnect = self.on_disconnectOut
        self.client_Int.on_publish = self.on_publish
        #self.client_Int.on_connect = self.onConnectInt
        self.connected_flag_Int = False
        self.mqtt_connectIn(True)
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
            return render_template('index.html', files=self.newFiles, textOut = self.textOut, textIn = self.textIn, typeIn= self.typeIn)

        @self.app.route('/submit_mqtt', methods=['POST'])
        def submit_mqtt():
            self.findFiles()
            selected_file = request.form['file']
            self.send_file_mess(selected_file, "mqtt")
            self.textOut = "File sent: " + selected_file
            return redirect(url_for('index'))
            #return render_template('index.html', files=self.newFiles, textOut = self.textOut, textIn = self.textIn, typeIn= self.typeIn)

        @self.app.route('/submit_printing', methods=['POST'])
        def submi_print():
            self.findFiles()
            selected_file = request.form['file']
            self.send_file_mess(selected_file, "Printing")
            self.textIn = "File sent: " + selected_file
            return redirect(url_for('index'))
            #return render_template('index.html', files=self.newFiles, textOut = self.textOut, textIn = self.textIn, typeIn= self.typeIn)

        @self.app.route('/check_connection_ex', methods=['GET'])
        def check_connection_EX():
            connected = self.connected_flag_Ex
            print(connected)
            if not connected:
                self.mqtt_connectOut()
            return jsonify({'connected': connected})
        
        @self.app.route('/check_connection_int', methods=['GET'])
        def check_connection_Int():
            connected = self.connected_flag_Int
            print(connected)
            if not connected:
                self.mqtt_connectIn()
            return jsonify({'connected': connected})


    def start(self):
        logger.info("Starting")
        self.app.run(debug=True,host="0.0.0.0",port=6050)
    

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
        
    def on_publish(self, client,userdata,result): 
        logger.info("Published")
        
    def file_exists(self, directory, filename):
        filepath = os.path.join(directory, filename)
        return os.path.exists(filepath)
    
    def send_file_mess(self, fileName, typeSend):
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
            
        if typeSend == "mqtt" or typeSend == "MQTT":
            self.send_mqtt(json_data)
        elif typeSend == "Printing":
            self.send_mqtt_print(json_data)
        logging.info("sent")

    def mqtt_connectOut(self, first_time=False):
        timeout = self.initial
        name = "External"
        while not self.connected_flag_Ex:
            try:
                if first_time:
                    self.client_Ex.connect(self.url_Ex, self.port_Ex, 60)
                    self.connected_flag_Ex = True
                else:
                    logger.error("Attempting to reconnect to " + name)
                    self.client_Ex.reconnect()
                    self.connected_flag_Ex = True  # Set flag if reconnection succeeds
                logger.info("Connected to " + name + "!")
                time.sleep(self.initial)  # to give things time to settle
            except Exception:
                logger.error(f"Unable to connect to {name}, retrying in {timeout} seconds")
                time.sleep(timeout)
                if timeout < self.limit:
                    timeout = timeout * self.backoff
                else:
                    timeout = self.limit

    def mqtt_connectIn(self, first_time=False):
        timeout = self.initial
        name = "Internal"
        while not self.connected_flag_Int:
            try:
                if first_time:
                    self.client_Int.connect(self.url_Int, self.port_Int, 60)
                    self.connected_flag_Int = True
                else:
                    logger.error("Attempting to reconnect to " + name)
                    self.client_Int.reconnect()
                    self.connected_flag_Int = True  # Set flag if reconnection succeeds
                logger.info("Connected to " + name + "!")
                time.sleep(self.initial)  # to give things time to settle
            except Exception:
                logger.error(f"Unable to connect to {name}, retrying in {timeout} seconds")
                time.sleep(timeout)
                if timeout < self.limit:
                    timeout = timeout * self.backoff
                else:
                    timeout = self.limit

    def on_disconnectIn(self, client, _userdata, rc):
        self.connected_flag_Int=False
        if rc != 0:
            logger.error(f"Unexpected MQTT disconnection (rc:{rc}), reconnecting...")
            self.mqtt_connectIn()

    def on_disconnectOut(self, client, _userdata, rc):
        self.connected_flag_Ex=False
        if rc != 0:
            logger.error(f"Unexpected MQTT disconnection (rc:{rc}), reconnecting...")
            self.mqtt_connectOut()

    def send_mqtt_print(self, msg_json):
        logger.info("MQTT_processing: mess recieved to process")
        msg_send = self.messeage_for_label(msg_json, self.config_lab)
        topic = self.topic_Int + self.name + "/"
        #data = [topic, msg_send]
        logger.info("AAS sending with topic: " + topic)
        out = json.dumps(msg_send)
        if not self.connected_flag_Int:
            self.mqtt_connectIn
        self.client_Int.publish(topic, out, 1)
        logger.info("Sent to printer")
    
    def send_mqtt(self, msg_json):
        logger.info("MQTT_processing: mess recieved to process")
        topic = self.topic_Ex + self.name + "/"
        #data = [topic, msg_send]
        logger.info("AAS sending with topic: " + topic)
        out = json.dumps(msg_json)
        if not self.connected_flag_Ex:
            self.mqtt_connectOut
        self.client_Ex.publish(topic, out, 1)
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

