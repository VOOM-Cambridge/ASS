import json
import os
import paho.mqtt.client as mqtt
from datetime import datetime
import tomli
# MQTT broker settings
script_dir_con = os.path.dirname(__file__) #<-- absolute dir the script is in
rel_path = "config/config.toml"
abs_file_path = os.path.join(script_dir_con, rel_path)

with open(abs_file_path, mode="rb") as fp:
    config = tomli.load(fp)

MQTT_host = config["mqtt"]["url"]
MQTT_Port = int(config["mqtt"]["port"])
MQTT_Topic = config["mqtt"]["topic_in"]
MQTT_Topic_out = config["mqtt"]["topic_out"]

def findCurrentStore():
    path = os.getcwd()
    if not folder_exists(path, "AAS_data"):
        parent = os.path.abspath(os.path.join(path, os.pardir))
        if not folder_exists(parent, "AAS_data"):
            script_dir = os.path.abspath(os.path.join(parent, os.pardir))
        else:
            script_dir = parent
    else:
        script_dir = path
    return script_dir

def folder_exists(directory, folder_name):
    # Get the current working directory
    # Construct the path to the folder
    folder_path = os.path.join(directory, folder_name)
    # Check if the folder exists
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        return True
    else:
        return False

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(MQTT_Topic)

def file_exists(directory, filename):
    filepath = os.path.join(directory, filename)
    return os.path.exists(filepath)

def on_message(client, userdata, msg):
    print("mess recieved")
    payload = msg.payload.decode("utf-8")
    print(payload)
    print("********")
    payload = json.loads(payload)

    try:
        # Decode the message payload
        AAS = json.loads(payload["AAS data"])
        print(AAS)
        print(type(AAS[0]))
        name = "unkown"
        try:
            name = AAS[0]["idShort"]
        except:
            name = "unkown"
        
        # Save the message as a JSON file
        
        i = 1
        while file_exists(SAVE_DIR, name + ".json"):
            print("Directory  exisits")
            name = name + str(i)
            i = i +1

        filename = name + ".json"
        filepath = os.path.join(SAVE_DIR, filename)
        
        with open(filepath, 'w') as file:
            json.dump(AAS, file, indent=4)
        print(f"Message saved to {filepath}")
    except Exception as e:
        print("Error:", e)

SAVE_DIR = os.path.join(findCurrentStore(), "AAS_data/in/")

if __name__ == "__main__":
    # Directory to save JSON files
    SAVE_DIR = os.path.join(findCurrentStore(), "AAS_data/in/")
    print(SAVE_DIR)
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    print(MQTT_host)
    print(MQTT_Port)
    client.connect(MQTT_host, MQTT_Port)
    
    client.loop_forever()
