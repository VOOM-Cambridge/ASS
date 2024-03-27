import os
from flask import Flask, render_template, request, jsonify
import zmq
import json, time
import logging

context = zmq.Context()
app = Flask(__name__)
logger = logging.getLogger("UI")

class App:
    def __init__(self, config, zmq_conf):
        self.app = Flask(__name__)
        self.zmq_conf = zmq_conf
        main_direc = self.findCurrentStore()
        AAS_direc = "AAS_data/order/"
        self.files_folder = os.path.join(main_direc, AAS_direc)
        print(self.files_folder)
        self.findFiles()
        self.text =""


        
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
            self.connect()
            return render_template('index.html', files=self.newFiles, text = self.text)

        @self.app.route('/', methods=['POST'])
        def submit():
            self.findFiles()
            selected_file = request.form['file']
            self.send_file_mess(selected_file)
            self.text = "File sent: " + selected_file
            return render_template('index.html', files=self.newFiles, text = self.text)

        @self.app.route('/start', methods=['GET'])
        def start():
            self.zmq_out.send(b'start')
            return jsonify({'message': 'Start command sent'})

        @self.app.route('/stop', methods=['GET'])
        def stop():
            self.zmq_out.send(b'stop')
            return jsonify({'message': 'Stop command sent'})

    def start(self):
        self.app.run(debug=True,host="0.0.0.0",port=6050)
    
    def connect(self):
        self.zmq_out = context.socket(self.zmq_conf['out']['type'])
        if self.zmq_conf["out"]["bind"]:
            self.zmq_out.bind(self.zmq_conf["out"]["address"])
        else:
            self.zmq_out.connect(self.zmq_conf["out"]["address"])

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
        self.zmq_out.send_json(json_data)
        print("sent")
        logging.info("sent")
