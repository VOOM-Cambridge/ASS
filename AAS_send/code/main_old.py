# This code example demonstartes how to generate a QR code from Text.
# Initialize the BarcodeGenerator
from aspose.barcode import generation
import os, json
import paho.mqtt.client as mqtt
import QRPrint
import time

client =mqtt.Client("aas_test")
client.connect("129.169.48.174", port=1883)
# Specify Encode type
generator = generation.BarcodeGenerator(generation.EncodeTypes.QR)
script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
rel_path = "/Submodel_CS1.json"
abs_file_path = script_dir + rel_path
with open(abs_file_path) as json_file:
    data_example = json.load(json_file)

# Define the data to be encoded in the QR code
data = json.dumps(data_example)

def sendMess():
    out = json.dumps(payload)
    client.publish("AAS/print/",out)
    print("sent")

def createQRAAS(ID, output_path):
    qrclass = QRPrint.QRPrint()
    qrclass.makeLabelAAS(ID, output_path + ".png")

client.subscribe("AAS/print/")
def on_message(client, userdata, message):
    payload_dict = json.loads(message)
    labelItems = payload_dict['labelItems']
    # for item in labelItems:
    #         print (item)
    #         createQRAAS(item['labelValue'], "new")
client.on_message = on_message

sendMess()

directory_to_watch = "/path/to/your/directory"

# Set to keep track of files that have been printed
printed_files = set()

while True:
    # Get list of files in the directory
    files = os.listdir(directory_to_watch)
    
    # Iterate over the files
    for file in files:
        # Check if file is not already printed
        if file not in printed_files:
            # Print the new file
            print("New file detected:", file)
            # Add the file to the set of printed files
            printed_files.add(file)
    
    # Sleep for a while before checking again (e.g., every 5 seconds)
    time.sleep(5)



