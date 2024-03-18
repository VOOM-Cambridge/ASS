import json
import os
import paho.mqtt.client as mqtt
from datetime import datetime
# MQTT broker settings
MQTT_host = "localhost"
MQTT_Port = 1883
MQTT_Topic = "AAS/in/#"

# Directory to save JSON files
SAVE_DIR = os.path.join(os.getcwd(), "..", "AAS_data/in/")

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(MQTT_Topic)

def on_message(client, userdata, msg):
    print("mess recieved")
    
    payload = msg.payload.decode("utf-8")
    print(payload)
    print("********")
    aas = payload["ass"]
    print(aas)
    
    try:
        # Decode the message payload
        payload = msg.payload.decode("utf-8")

        AAS = payload["ass"]
        print(AAS)
        # Create directory if it doesn't exist
        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)
        try:
            name = msg["submodelElements"][0]["value"][2]["value"]
        except:
            nam = "unkown" + datetime.now()
            name = nam.strftime("%Y-%m-%d_%H-%M-%S.json")
        
        # Save the message as a JSON file
        filename = name + ".json"
        filepath = os.path.join(SAVE_DIR, filename)
        with open(filepath, 'w') as file:
            json.dump(AAS, file, indent=4)
        print(f"Message saved to {filepath}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_host, MQTT_Port, 60)
    
    client.loop_forever()
