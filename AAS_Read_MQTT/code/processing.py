
import threading
import time
import zmq
import logging
import zmq.asyncio
import multiprocessing
import base64
import zlib
import json

context = zmq.Context()
logger = logging.getLogger("main.pocessing")


class DataProcessing(multiprocessing.Process):
    def __init__(self, config, zmq_conf):
        super().__init__()
        self.process_running = False
        # declarations
        self.zmq_conf = zmq_conf
        self.zmq_in = None
        self.zmq_out = None
        self.multiple = False
        self.buffer = ""
        self.topic = config["factory"]["name"]

    def do_connect(self):
        self.zmq_in = context.socket(self.zmq_conf['in']['type'])
        if self.zmq_conf['in']["bind"]:
            self.zmq_in.bind(self.zmq_conf['in']["address"])
        else:
            self.zmq_in.connect(self.zmq_conf['in']["address"])

        self.zmq_out = context.socket(self.zmq_conf['out']['type'])
        if self.zmq_conf['out']["bind"]:
            self.zmq_out.bind(self.zmq_conf['out']["address"])
        else:
            self.zmq_out.connect(self.zmq_conf['out']["address"])
        print("connected processing")

    def decodeFullData(self, dataIn):
        try:
            dataDecode = base64.b64decode(dataIn)
            uncompressed = zlib.decompress(dataDecode)
            data = uncompressed.decode()
            res = json.loads(data)
            print(res)

            if res["idShort"]:
                name = "./data/" + res[0]["idShort"] + ".json"
            else:
                print("no id short")
                name = "./data/" + "output.json" 

            with open(name, "w") as outfile:
                outfile.write(data)
            print(data)
            self.forwardOnData(data)
        except Exception as e:
            print("Error in processing")
            print(e)
            logger.error(e)

    def forwardOnData(self, dataToSend):
        self.zmq_out.send_json({'topic': self.topic, 'payload': {"type": "AAS","id": dataToSend}})
        print("Sent on to next thread" )


    def checkForMultiple(self, dataIn):
        if dataIn == "AAS00001": # multiple if this is scanned with barcode
            if self.multiple == True:
                #ending scan of multiple 
                print("Multiple QR collected sending for processing ...")
                self.multiple = False
                self.decodeFullData(self.buffer)
            elif self.multiple == False: 
                # starting scan of multiple 
                print("Waiting for multiple QR")
                self.multiple = True
                self.buffer = ""  # clear buffer if not already
    
    def get_input_message(self):
        while self.zmq_in.poll(1000, zmq.POLLIN) == 0:  # blocks until a message arrives
            pass
        try:
            msg = self.zmq_in.recv(zmq.NOBLOCK)
            logger.debug(f"got {msg}")
            return json.loads(msg)
        except zmq.ZMQError:
            pass
        return {}

    def run(self):
        self.do_connect()

        run = True
        while run:
            msg = self.get_input_message()
                #msg = self.zmq_in.recv(zmq.NOBLOCK)
            try:
                barcode = msg['barcode']
            except KeyError:
                logger.warning(f"Message did not not have required keys: {msg}")
                continue
            datScanned= barcode
            print("barcode/qr code found")
            self.checkForMultiple(datScanned)
            if self.multiple == False:
                # only one to process 
                print("QR code scnaned and recieved")
                self.decodeFullData(datScanned)
            else:
                #multiple to collct 
                self.buffer = self.buffer + datScanned

                


                
