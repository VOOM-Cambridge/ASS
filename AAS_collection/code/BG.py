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

# root
# directory = In AAS submodels
# direcAASX = out part

class BackgroundUpdater:
    def __init__(self, directory, direcAASX):
        self.root = tk.Tk()
        self.root.title("Submodel Importer")
        self.root.geometry("300x100")
        self.direcAASX = direcAASX
        self.directory = directory

        # # Flag to control the background operation
        # self.running = False
        # # Setup the start button
        # self.start_button = tk.Button(self.root, text="Start Importing", command=self.start_updating())
        # self.start_button.pack(padx=20, pady=10)

        # # Setup the stop button
        # self.stop_button = tk.Button(self.root, text="Stop Importing", command=self.stop_updating, state=tk.DISABLED)
        # self.stop_button.pack(padx=20, pady=10)

    def checkId(self, barcodeId):
        if barcodeId[0].isnumeric():
            return "X" + barcodeId
        else:
            return barcodeId

    def undoCheckId(self, barcodeId):
        if barcodeId[0]== "X":
            return barcodeId[1:]
        else:
            return barcodeId
    

    def update_file(self, productbarcode):
        productid= productbarcode[:4]

        
        ###################################################################################
        # step 1: extracting the AAS data into python and populating the part ids of the submodels to be imported
        bom_partid = []
        with open(f'{self.direcAASX}/{productbarcode}.json', 'r') as f:
            aas_data = json.load(f)
        number_of_submodels= aas_data['submodels']

        for i in range(len(number_of_submodels)):
            submodel_id = self.undoCheckId(aas_data['submodels'][i]['idShort'])
            BOM_id= f'BOM_{productbarcode}'
            if submodel_id == BOM_id:
                bom= aas_data['submodels'][i]['submodelElements']

        for i in range(len(bom)):
            p = bom[i]['value'][0]['value']
            bom_partid.append(p)

        print(f'The submodels to be imported are the ones with the following part id: {bom_partid}')

        ###################################################################################
        # step 2: Assign  the directory in which the imported submodels are present

        subPath = []
        # iterate over files in that directory
        for filename1 in os.listdir(self.directory):
            f = os.path.join(self.directory, filename1)
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
            part_id = self.undoCheckId(sub_data[0]['idShort'])

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
                idbarcode = aas_data['assetAdministrationShells'][0]["identification"]["id"]
                print(idbarcode)
                with open(f'{self.direcAASX}/{productbarcode}_new.json', 'w') as n:
                    json.dump(aas_data, n)

                # Opening the Json file and retrieving the data to an object store that is AAS compliant
                with open(f'{self.direcAASX}/{productbarcode}_new.json', encoding='utf-8-sig') as json_file:
                    json_file_data = aas.adapter.json.read_aas_json_file(json_file)
                

                # Creating the AASX file from the data that has been retrieved in the previous step
                with aasx.AASXWriter(f'{self.direcAASX}/{productbarcode}_AASnew.aasx') as writer:
                    writer.write_aas(
                        aas_id=model.Identifier(f'{idbarcode}', model.IdentifierType.IRI),
                        object_store=json_file_data,
                        file_store=None,
                        submodel_split_parts=False)  # for compatibility with AASX Package Explorer
                    # Write the AAS and everything belonging to it to the AASX package
                    # The `write_aas()` method will automatically fetch the AAS object with the given identification, the referenced
                    # Asset object and all referenced Submodel and ConceptDescription objects from the ObjectStore. It will also
                    # scan all sbmodels for `File` objects and fetch the referenced auxiliary files from the SupplementaryFileContainer.
                    print(f'Import of the submodel {part_id} in the AAS is successful')
            # else:
            #     notadded.append(part_id)
                #print(f'submodels with part id {part_id} has not been imported as they do not belong in this AAS')


            time.sleep(2)  # Update interval - adjust as needed

    # def start_updating(self):
    #     if not self.running:
    #         self.running = True
    #         self.update_thread = threading.Thread(target=self.update_file(barcode))
    #         self.update_thread.start()
    #         self.start_button.config(state='disabled')
    #         self.stop_button.config(state='normal')

    # def stop_updating(self):
    #     self.running = False
    #     self.update_thread.join()
    #     self.start_button.config(state='normal')
    #     self.stop_button.config(state='disabled')

    def run(self, barcode):
        #self.root.mainloop()
        self.update_file(barcode)


# if __name__ == "__main__":
#     root = tk.Tk()
#     directory = 'AAS gearbox/submodels/New template'
#     app = BackgroundUpdater(root, directory, direcAASX)
#     root.mainloop()
