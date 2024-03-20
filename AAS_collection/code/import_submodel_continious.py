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

# #inputs
# filename = "gearboxJSON"  # file name of the AAS V0 file in JSON format
directory = 'AAS gearbox/submodels/New template' #directory of the folder where the submodels are stored
#aas_identifier = 'urn:cam.ac.uk:ifm:aas:1:1:gearbox' #unique identifier of the AAS v0

bom = {
    'id': 'IXY898',
    'parts': ["barcode0", "barcode1", "barcode2"],
    'quantity': ["1", "2", "3"]
}

def checkId(barcodeId):
    if barcodeId[0].isnumeric():
        return "X" + barcodeId
    else:
        return barcodeId

def undoCheckId(barcodeId):
    if barcodeId[0]== "X":
        return barcodeId[1:]
    else:
        return barcodeId
    

def bomsubmodel(productbarcode, bom, direc, tempDire, name):

    if productbarcode == bom['id']:
        #opening the template of the BOM submodel
        with open(tempDire +'BOM_template.json', 'r') as f:
            bom_template = json.load(f)

        #opening the template of the submodel elements of the BOM
        with open(tempDire +'BOMelement_template.json', 'r') as n:
            bomelement_template = json.load(n)

        #adding the 'idshort' of the bom - the idshort will be in format 'bom_productbarcode'
        bom_productid= f'BOM_{productbarcode}'
        bom_template[0]['idShort'] = checkId(bom_productid)

        #This is a loop that goes through the parts in the BOM and adds them as submodel elements into the submodel of the BOM
        for i in range(len(bom['parts'])):
            part = json.loads(json.dumps(bomelement_template))
            part[0]['idShort']= f'partnumber_{i}'
            part[0]['value'][0]['value'] = bom['parts'][i]
            part[0]['value'][0]['idShort']= f'barcodepart_{i}'
            part[0]['value'][1]['value']= bom['quantity'][i]
            part[0]['value'][1]['idShort'] = f'quantitypart_{i}'
            bom_template[0]['submodelElements'].extend(part)

        #This part extracts the long identifier of the BOM submodel and prepares it to be added to the AAS
        submodel_id = bom_template[0]['identification']['id']
        strsub_id = str(submodel_id).translate({ord(i): None for i in '{}'})
        sub_id_load = '[{"keys": [{"type": "Submodel", "idType": "IRI", "value":' + f'"{strsub_id}"' + ',"local": true}]}]'
        sub_id_json = json.dumps(sub_id_load)
        jsonsub_id_load = json.loads(sub_id_json)
        submodel_idjson = json.loads(jsonsub_id_load.replace("\'", '"'))

        #creating the new bill of materials submodel
        with open(f'{direc}/BOM_{productbarcode}.json', 'w') as n:
            json.dump(bom_template, n, indent=4)

###From here we have the BOM submodel and the identifier of the BOM submodel to add to the main AAS
##############################
        productid= productbarcode[:4]

        #opening the BOM submodel
        with open(f'{direc}/BOM_{productbarcode}.json', 'r') as k:
           submodel_bom= json.load (k)

        #adding the BOM submodel to the AAS of the product
        with open(f'{tempDire}/{productid}_template.json', 'r') as f:
            aasdata = json.load(f)
            aasdata['submodels'].extend(submodel_bom)
            aasdata['assetAdministrationShells'][0]['submodels'].extend(submodel_idjson)

            idbarcode = aasdata['assetAdministrationShells'][0]["identification"]["id"] + name + ":" + productid
            aasdata['assetAdministrationShells'][0]["identification"]["id"] = idbarcode

        #Storing the new AAS of the product, containing the BOM, in a new json file
        with open(f'{direc}/{productbarcode}.json', 'w') as n:
            json.dump(aasdata, n)

        # Opening the Json file and retrieving the data to an object store that is AAS compliant
        with open(f'{direc}/{productbarcode}.json', encoding='utf-8-sig') as json_file:
            json_file_data = aas.adapter.json.read_aas_json_file(json_file)
        
        

        # Creating the AASX file from the data that has been retrieved in the previous step
        with aasx.AASXWriter(f'{direc}/{productbarcode}.aasx') as writer:
            writer.write_aas(
                aas_id=model.Identifier(f'{idbarcode}', model.IdentifierType.IRI),
                object_store=json_file_data,
                file_store=None,
                submodel_split_parts=False)  # for compatibility with AASX Package Explorer
            # Write the AAS and everything belonging to it to the AASX package
            # The `write_aas()` method will automatically fetch the AAS object with the given identification, the referenced
            # Asset object and all referenced Submodel and ConceptDescription objects from the ObjectStore. It will also
            # scan all sbmodels for `File` objects and fetch the referenced auxiliary files from the SupplementaryFileContainer.

#hello=bomsubmodel('IXY898')

