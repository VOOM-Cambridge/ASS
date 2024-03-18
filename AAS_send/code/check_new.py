
import multiprocessing
import logging
import zmq
import json
from datetime import datetime
import os, time

context = zmq.Context()

class Check_for_new(multiprocessing.Process):
    def __init__(self, config, zmq_conf):
        super().__init__()#
        
        self.directory = config["Factory"]["file_directory"]
        self.sent_files_file = "./sent_files.txt"
        self.printed_files = set()

        # declarations
        self.zmq_conf = zmq_conf
        self.zmq_out = None
        self.zmq_out_intenral =None

    def do_connect(self):
        self.zmq_out = context.socket(self.zmq_conf["out"]['type'])
        if self.zmq_conf["out"]["bind"]:
            self.zmq_out.bind(self.zmq_conf["out"]["address"])
        else:
            self.zmq_out.connect(self.zmq_conf["out"]["address"])
        
    def checkDirectory(self, directory_to_watch):
        files = os.listdir(directory_to_watch)
        for file_name in files:
            # Check if file is not already printed
            file_path = os.path.join(directory_to_watch, file_name)
            if file not in self.printed_files and file_name.endswith('.json'):
                # Print the new file
                print("New AAS detected:", file)
                # send files on to next
                with open(file_path, 'r') as json_file:
                    json_data = json.load(json_file)
                #msg_payload = json.dumps(json_data)
                self.zmq_out.send_json(json_data)
                # Add the file to the set of printed files
                self.printed_files.add(file)
                # Append the file name to the sent_files_file
                with open(self.sent_files_file, 'a') as file:
                    file.write(file + '\n')
        
    def run(self):
        self.do_connect()
        print("ZMQ Connected")
        run = True
        if not os.path.exists(self.sent_files_file):
            open(self.sent_files_file, 'a').close()
        with open(self.sent_files_file, 'r') as file:
            for line in file:
                self.printed_files.add(line.strip())
        while run:
            self.checkDirectory(self.directory)
            time.sleep(2)