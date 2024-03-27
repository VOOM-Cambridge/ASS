import tkinter as tk
import threading
import time
import os
from aas.adapter import aasx
import json
from aas import model
import aas.adapter.json
import aas.adapter.xml
from aas.adapter import aasx
from tkinter import ttk

# #inputs
filename = "gearboxJSON"  # file name of the AAS V0 file in JSON format
directory = 'AAS gearbox/submodels/New template' #directory of the folder where the submodels are stored
aas_identifier = 'urn:cam.ac.uk:ifm:aas:1:1:gearbox' #unique identifier of the AAS v0

class BackgroundUpdater:
    def __init__(self, root):
        self.root = root
        self.root.title("Submodel Importer")
        root.geometry("300x100")

        # Flag to control the background operation
        self.running = False
##############################################################
        # # Label and entry for the filename
        # self.label1 = tk.Label(self.root, text="Name of the AAS file:")
        # self.label1.pack(pady=(10, 0))
        # self.param1 = tk.Entry(self.root)
        # self.param1.pack(pady=5)
        #
        # # Label and entry for the second parameter
        # self.label2 = tk.Label(self.root, text="Directory where the submodels are stored:")
        # self.label2.pack(pady=(10, 0))
        # self.param2 = tk.Entry(self.root)
        # self.param2.pack(pady=5)
        #
        # # Label and entry for the third parameter
        # self.label3 = tk.Label(self.root, text="The unique identifier of the AAS:")
        # self.label3.pack(pady=(10, 0))
        # self.param3 = tk.Entry(self.root)
        # self.param3.pack(pady=5)
############################################################

        # Setup the start button
        self.start_button = tk.Button(self.root, text="Start Importing", command=self.start_updating)
        self.start_button.pack(padx=20, pady=10)

        # Setup the stop button
        self.stop_button = tk.Button(self.root, text="Stop Importing", command=self.stop_updating, state=tk.DISABLED)
        self.stop_button.pack(padx=20, pady=10)


        frame = ttk.Frame(root, padding="20")
        frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.label_folder_path = ttk.Label(frame, text="Folder Path:")
        self.label_folder_path.grid(column=0, row=0, sticky=tk.W)

        self.entry_folder_path = ttk.Entry(frame, width=50)
        self.entry_folder_path.grid(column=1, row=0, sticky=(tk.W, tk.E))

        self.button_populate = ttk.Button(frame, text="Populate Dropdown", command=self.populate_dropdown)
        self.button_populate.grid(column=0, row=1, columnspan=2, pady=10)

        self.dropdown = ttk.Combobox(frame, width=50, state="readonly")
        self.dropdown.grid(column=0, row=2, columnspan=2, pady=10)
        self.dropdown.set("Select a file")

    def populate_dropdown(self):
        folder_path = os.getcwd()
        if os.path.isdir(folder_path):
            files = os.listdir(folder_path)
            self.dropdown['values'] = files
        else:
            self.dropdown.set('Invalid folder path')

    def update_file(self):
#################################################################
        # filename = self.param1.get()
        # directory = self.param2.get()
        # aas_identifier = self.param3.get()
#########################################################################
        while self.running:
            ###################################################################################
            # step 1: extracting the AAS data into python and populating the part ids of the submodels to be imported
            bom_partid = []
            with open(f'AAS gearbox/{filename}.json', 'r') as f:
                aas_data = json.load(f)
            bom = aas_data['submodels'][2]['submodelElements']

            for i in range(len(bom)):
                p = bom[i]['value'][0]['value']
                bom_partid.append(p)

            print(f'The submodels to be imported are the ones with the following part id: {bom_partid}')

            ###################################################################################
            # step 2: Assign  the directory in which the imported submodels are present

            subPath = []
            # iterate over files in that directory
            for filename1 in os.listdir(directory):
                f = os.path.join(directory, filename1)
                # checking if it is a file
                if os.path.isfile(f):
                    # print(f)
                    subPath.append(f)

            ###################################################################################
            # step 3: extracting the submodel identifier, part id, and the supplier id  from all the submodels in the defined directory

            added = []
            notadded = []

            for f in range(len(subPath)):
                name = subPath[f]
                with open(name, 'r') as f:
                    sub_data = json.load(f)

                submodel_id = sub_data[0]['identification']['id']
                part_id = sub_data[0]['idShort']
                supplier_id = sub_data[0]['submodelElements'][1]['value'][1]['value']

                # preparing the submodel id for JSON format
                strsub_id = str(submodel_id).translate({ord(i): None for i in '{}'})
                sub_id_load = '[{"keys": [{"type": "Submodel", "idType": "IRI", "value":' + f'"{strsub_id}"' + ',"local": true}]}]'
                sub_id_json = json.dumps(sub_id_load)
                jsonsub_id_load = json.loads(sub_id_json)
                submodel_idjson = json.loads(jsonsub_id_load.replace("\'", '"'))

                ###################################################################################
                # step 4: by comparing the part ids of the submodels with the part ids extracted from the AASv0, the code identifies which submodels belong to the AAS and starts the importing process

                if part_id in bom_partid:
                    aas_data['submodels'].extend(sub_data)
                    aas_data['assetAdministrationShells'][0]['submodels'].extend(submodel_idjson)

                    with open(f'AAS gearbox/{filename}_new.json', 'w') as n:
                        json.dump(aas_data, n)

                    # Opening the Json file and retrieving the data to an object store that is AAS compliant
                    with open(f'AAS gearbox/{filename}_new.json', encoding='utf-8-sig') as json_file:
                        json_file_data = aas.adapter.json.read_aas_json_file(json_file)

                    # Creating the AASX file from the data that has been retrieved in the previous step
                    with aasx.AASXWriter(f'AAS gearbox/{filename}_AASnew.aasx') as writer:
                        writer.write_aas(
                            aas_id=model.Identifier(f'{aas_identifier}', model.IdentifierType.IRI),
                            object_store=json_file_data,
                            file_store=None,
                            submodel_split_parts=False)  # for compatibility with AASX Package Explorer
                        # Write the AAS and everything belonging to it to the AASX package
                        # The `write_aas()` method will automatically fetch the AAS object with the given identification, the referenced
                        # Asset object and all referenced Submodel and ConceptDescription objects from the ObjectStore. It will also
                        # scan all sbmodels for `File` objects and fetch the referenced auxiliary files from the SupplementaryFileContainer.
                        print(f'Import of the submodel {part_id} in the AAS is successful')
                else:
                    notadded.append(part_id)
                    print(f'submodels with part id {part_id} has not been imported as they do not belong in this AAS')


            time.sleep(2)  # Update interval - adjust as needed

    def start_updating(self):
        if not self.running:
            self.running = True
            self.update_thread = threading.Thread(target=self.update_file)
            self.update_thread.start()
            # Disable the input fields and start button, enable the stop button while running
            # self.param1.config(state='disabled')
            # self.param2.config(state='disabled')
            # self.param3.config(state='disabled')
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')

    def stop_updating(self):
        self.running = False
        self.update_thread.join()
        # Re-enable the input fields and start button, disable the stop button after stopping
        # self.param1.config(state='normal')
        # self.param2.config(state='normal')
        # self.param3.config(state='normal')
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')


if __name__ == "__main__":
    root = tk.Tk()
    app = BackgroundUpdater(root)
    root.mainloop()
