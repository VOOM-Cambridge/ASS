import datetime
from pathlib import Path  # Used for easier handling of auxiliary file's local path
import os
from aas.adapter import aasx
import json
from aas import model
import aas.adapter.json
import aas.adapter.xml
from aas.adapter import aasx

#inputs
filename = "gearboxJSON"  # file name of the AAS V0 file in JSON format
directory = 'AAS gearbox/submodels/New template' #directory of the folder where the submodels are stored
aas_identifier = 'urn:cam.ac.uk:ifm:aas:1:1:gearbox' #unique identifier of the AAS v0


###################################################################################
# step 1: extracting the AAS data into python and populating the part ids of the submodels to be imported
bom_partid= []
with open (f'AAS gearbox/{filename}.json', 'r') as f:
    aas_data= json.load(f)
bom= aas_data['submodels'][2]['submodelElements']

for i in range(len(bom)):
    p= bom[i]['value'][0]['value']
    bom_partid.append(p)

print (f'The submodels to be imported are the ones with the following part id: {bom_partid}')

###################################################################################
# step 2: Assign  the directory in which the imported submodels are present

subPath=[]
# iterate over files in that directory
for filename1 in os.listdir(directory):
    f = os.path.join(directory, filename1)
    # checking if it is a file
    if os.path.isfile(f):
        # print(f)
        subPath.append(f)

###################################################################################
# step 3: extracting the submodel identifier, part id, and the supplier id  from all the submodels in the defined directory

added=[]
notadded=[]

for f in range(len(subPath)):
    name= subPath[f]
    with open (name, 'r') as f:
        sub_data= json.load(f)

    submodel_id = sub_data[0]['identification']['id']
    part_id = sub_data[0]['idShort']
    supplier_id = sub_data[0]['submodelElements'][1]['value'][1]['value']

    #preparing the submodel id for JSON format
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
            json.dump( aas_data, n)

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
    else:
        notadded.append(part_id)
        print(f'submodels with part id {part_id} has not been imported as they do not belong in this AAS')


