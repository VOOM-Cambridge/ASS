# -*- coding: utf-8 -*-
"""
Created on Mon Mar  8 17:32:35 2021

@author: Tasnim
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Nov  2 12:42:13 2020

@author: Tasnim Ahmed
"""
#Libraries
import pandas as pd 
from aas import model
import aas.adapter.xml
import datetime
from pathlib import Path  # Used for easier handling of auxiliary file's local path

import pyecma376_2  # The base library for Open Packaging Specifications. We will use the OPCCoreProperties class.
from aas.adapter import aasx
###############################################################################
                              ##### Details to be edited ########
#Excel sheet name that contains the AAS data
excel= "DrillingMachine.xlsx"

#Do you want to include a Bill of Material submodel? (insert: yes/no)
include_BOM = "no"

#IRI ID general syntax. If the desired ID is custom please don't forget to 
# specify it in the id_type 
ID="https://www.industry40lab.org/ids/aas/"

################################################################################
                       ########importing excel sheets with the data ##### 

A= 0                                                           #Index of the Asset, always stays the same
Astex= pd.read_excel(excel,sheet_name='Asset')                 #Assets Sheet 
SMex= pd.read_excel(excel,sheet_name='Submodels')              #Submodel Sheet
PPex= pd.read_excel(excel,sheet_name='Properties')             #Properties Sheet
Filex= pd.read_excel(excel,sheet_name='Files')                 #Files Sheet
BOM= pd.read_excel(excel,sheet_name='BOM')                     #bill of materials sheet 

##############################################################################
                           #### Creating the AAS #######
                           
## Creating the entities for the bill of materials if present 
if include_BOM =='yes':
    entity_1=[]
    for b in range(len(BOM)):
        en = model.Entity(
        id_short=BOM.entityName[b],
        entity_type=model.EntityType.SELF_MANAGED_ENTITY,
        statement=(),
        asset=model.AASReference((model.Key(type_=model.KeyElements.ASSET,
                                            local=False,
                                            value=BOM.referance[b],
                                            id_type=model.KeyType.IRI),),
                                 model.Asset),
        category=None,
        description={'en-us': BOM.description[b]},
        parent=None,
        qualifier=None,
        kind=model.ModelingKind.INSTANCE
        )
        entity_1.append(en)
    
## Creating the bill of materials & adding the entities to it    
    bill_of_material = model.Submodel(
            identification=model.Identifier(id_= ID + Astex.BofM[A],
                                            id_type=model.IdentifierType.IRI),
            submodel_element=(entity_1),
            id_short='BillOfMaterial',
            description={'en-us': Astex.BofMdescription[A]},
            administration=model.AdministrativeInformation(version='0.1'))

## Defining the Asset
asset =model.Asset(
        kind=model.AssetKind.INSTANCE,
        identification=model.Identifier(id_= ID + Astex.Identifier[A],
                                        id_type=model.IdentifierType.IRI),
        id_short= Astex.id_short[A],
        category=None,
        description={'en-us': Astex.AssetName [A]},
        parent=None,
        administration=model.AdministrativeInformation(),
        asset_identification_model=None,
        bill_of_material=model.AASReference((model.Key(type_=model.KeyElements.SUBMODEL,
                                                       local=False,
                                                       value= ID + Astex.BofM[A],
                                                       id_type=model.KeyType.IRI),),
                                            model.Submodel))

#Defining the Submodels & relative Properties
submodeln=[]                                                                      #List of Submodels

for i in range (len(SMex)):                                                      #Submodels Loop
    submodel_elements_=[]                                                        #List of Properties           
    for x in range (len(Filex)):                                                 #Files Loop
        if Filex.SMname [x] == SMex.Sidentifier [i]: 
            F= model.File(
                id_short=Filex.Fname[x],
                mime_type= "file/pdf" ,
                value= "to be set" ,
                category='PARAMETER',
                description={'en-us': 'File object'},
                parent=None,
                semantic_id=model.Reference((model.Key(
                    type_=model.KeyElements.GLOBAL_REFERENCE,
                    local=False,
                    value= ID + Filex.IID[x],
                    id_type=model.KeyType.IRI),)),
               qualifier=None,
               kind=model.ModelingKind.INSTANCE)
            submodel_elements_.append(F)
            
    for x in range (len(PPex)):                                                 #Properties Loop
        if PPex.SMname [x] == SMex.Sidentifier [i]:
            
            Prop = model.Property(
                id_short=PPex.Pidshort[x],
                value_type=model.datatypes.String,
                value=PPex.Value[x],
                description= {'en-us':PPex.Description[x]},
                semantic_id=model.Reference(
                    (model.Key(
                        type_=model.KeyElements.GLOBAL_REFERENCE,
                        local=False,
                        value=ID + PPex.semanticid[x],
                        id_type=model.KeyType.IRI
                        ),)
                    ))
            submodel_elements_.append(Prop)
     
    S= model.Submodel( identification=model.Identifier(ID + SMex.Sidentifier[i], 
                                                       model.IdentifierType.IRI), 
                  submodel_element=( submodel_elements_), id_short=SMex.Smname[i])
    submodeln.append(S)

## Adding the bill of materials submodel 
if include_BOM =='yes':
    submodeln.append(bill_of_material)


## Creating the Asset Administration Shell
submodel_reference_list =list()
for sub in submodeln:
    submodel_reference_list.append( model.AASReference.from_referable(sub))
    
aashell = model.AssetAdministrationShell(
        identification=model.Identifier(id_=ID + Astex.AAS[A],
                                        id_type=model.IdentifierType.IRI),
        id_short=Astex.AssetName[A],
        category=None,
        description={'en-us': Astex.AASdescription[A]},
        parent=None,
        administration=model.AdministrativeInformation(version='0.1',
                                                       revision='0'),
        security=None,
    asset=model.AASReference.from_referable(asset),
    submodel=(submodel_reference_list
    ))


    
##############################################################################
                             ##### Creating the XML file #######

obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
obj_store.add(asset)
for sub in submodeln:
    obj_store.add(sub)
obj_store.add(aashell)

with open('data.xml', 'wb') as xml_file:
    aas.adapter.xml.write_aas_xml_file(xml_file, obj_store)
    

file_store = aasx.DictSupplementaryFileContainer()
with open(Path(__file__).parent / 'data' / 'TestFile.pdf', 'rb') as f:
    actual_file_name = file_store.add_file("/aasx/suppl/MyExampleFile.pdf", f, "application/pdf")
    
with aasx.AASXWriter("MyAASXPackage.aasx") as writer:
    # Write the AAS and everything belonging to it to the AASX package
    # The `write_aas()` method will automatically fetch the AAS object with the given identification, the referenced
    # Asset object and all referenced Submodel and ConceptDescription objects from the ObjectStore. It will also
    # scan all sbmodels for `File` objects and fetch the referenced auxiliary files from the SupplementaryFileContainer.
    writer.write_aas(aas_id=model.Identifier(ID + Astex.AAS[A], model.IdentifierType.IRI),
                     object_store=obj_store,
                     file_store=file_store,
                     submodel_split_parts=False)  # for compatibility with AASX Package Explorer