import tomli, csv
import os
from fetchDataInflux import fetchData
from freppleAPImodule import freppleConnect 
import json
from datetime import datetime, timedelta
import time
import pytz
import random
from pathlib import Path

utc=pytz.UTC

# collect data on
#  1. Energy Use
#  2. Material Waste
#  3. Prodcut Scrap
#  4. Material Use
#  5. Order timeing 
    
def findEnergyData(config, orderNum, sTimeIn, eTimeIn):
    # find the equipment names with that order

    #machine_list = ["LR_Mate_3", "M6_cell_3"]
    machine_list = config["machine_list"]
    approxTime = 300
    diff = 150
    energyTotalFull =0
    try:
        sTime, eTime = influxClient.jobLengthTime(orderNum, 200)
    except:
        print("no order found")
    if config["frequency"] == "per product":
        dataBack = frepple.ordersIn("GET", {"name": str(orderNum)})
        if dataBack != None:
            numberInOrder = dataBack["quantity"]
    else: # frequency is per order or assumed to be per order type
        numberInOrder = 1
    
    for name in machine_list:
        energyTotal = 0
        
        if config["method"] == "tracking":
            # try tracking infomraiton 
            energyTotal = influxClient.findEnergyData(sTime, eTime, name)
        
        elif config["method"] == "signal":
            # try singal processing method
            output, diffarray = influxClient.findEnergyDataAssembly(sTime, eTime, name, approxTime, diff)
            energyTotal = influxClient.findEnergyData(output[0], output[1], name)

        elif config["method"] == "machine":
            energyTotal = influxClient.findEnergyData(sTimeIn, eTimeIn, name)

        elif config["method"] == "MES":
            print("MES has no energy date")

        energyTotalFull += energyTotal

    return energyTotalFull/numberInOrder


def findMaterialUseData(frequency, item, numberInOrder):
    # find the equipment names with that order
    try:
        data = frepple.findAllPartsMaterials(item)
        materialUse =[]
        materialType = []
        for i in range(len(data)):
            material = data[i][0]
            if "ABS" in material:
                materialUse.append(data[i][1]*float(numberInOrder)*1020*0.00175*0.00175/4) # density*D^2/4*L = [kg]
            else:
                materialUse.append(data[i][1]*float(numberInOrder))
            materialType.append(material)
        if frequency == "per product":
            materialUse = [mat/float(numberInOrder) for mat in materialUse]
        return materialUse, materialType
    except Exception as e:
        return "", ""


def findJobTimesTracking(config_order_time, order):
    if config_order_time["method"] == "tracking" and order != "":
        timeStart, timeEnd = influxClient.jobLengthTime(order, 300)
    return timeStart, timeEnd 

def findJobTimesSignal(config_order_time, order):
    data = influxClient.jobLengthAndTimeFile(config_order_time['machine'], 300)
    return data

def create_json(dict_file):
    # Serializing json into a json file
    json_object = json.dumps(dict_file, indent=4)
    # Writing to sample.json
    script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
    rel_path = "output/json/" + dict_file["name"].replace(".", "_") + ".json"
    rel_path = rel_path.replace(" ", "_")
    abs_file_path = os.path.join(script_dir,rel_path)
    i = 1
    while os.path.isfile(abs_file_path) and os.access(abs_file_path, os.R_OK):
        with open(abs_file_path, "r") as outfile:
            data = json.load(outfile)
            if data["name"] == dict_file["name"] and data["start time"] == dict_file["start time"] and data["end time"] == dict_file["end time"]:
                #print("Data already added")
                return 1
        rel_path = "/output/json/" + dict_file["name"].replace(".", "_") + str(i) + ".json"
        rel_path = rel_path.replace(" ", "_")
        abs_file_path = r'%s' % (script_dir + rel_path)
        i = i+ 1 
    with open(abs_file_path, "w") as outfile:   
        outfile.write(json_object)
        return 0

def add_data_together(example, data, config):
    # remove extra element
    #del example[0]["submodelElements"][6]
    #del example[0]["submodelElements"][3]["value"][1]

    #factory name details 
    example[0]["idShort"] = config["Factory"]["name"] #+ str(random.randrange(1, 10000))
    example[0]["submodelElements"][1]["value"][0]["value"] = config["Factory"]["name"] # Factory name
    example[0]["submodelElements"][1]["value"][2]["value"] = config["Factory"]["address"]
    example[0]["submodelElements"][1]["value"][3]["value"] = config["Factory"]["email"]
    # Not sure about this bit 
    # order unique id
    # example[0]["submodelElements"][0]["value"][1]["value"] = str(data["name"]) # unique to company

    # Order details [0] - > [0 -> Part name ] [1 -> quantity] [2 -> order_barcode/numeber]
    example[0]["submodelElements"][0]["value"][0]["value"] = str(data["item"])
    example[0]["submodelElements"][0]["value"][1]["value"] = str(data["quantity"])
    example[0]["submodelElements"][0]["value"][2]["value"] = str(data["name"])
    
    # Total energy
    example[0]["submodelElements"][2]["value"] = str(data["energy use"])

    # Total material
    mat_type_history = []
    if type(data["material use"]) == list:
        i = 0
        for material in data["material use"]:
            matType = str(data["material type"][i])
            if i == 0:
                example[0]["submodelElements"][3]["value"][0]["value"] = str(material)
                example[0]["submodelElements"][3]["value"][0]["idShort"] = matType
                mat_type_history.append(matType)
            else:
                # add new material 
                example[0]["submodelElements"][3]["value"].append(str(example[0]["submodelElements"][3]["value"][0]))
                example[0]["submodelElements"][3]["value"][i]["value"] = str(material)
                if matType in mat_type_history:
                    example[0]["submodelElements"][3]["value"][i]["idShort"] = matType + "_" + str(material)
                else:
                    example[0]["submodelElements"][3]["value"][i]["idShort"] = matType
                mat_type_history.append(matType)
            i +=1
    else:
        try:
            del example[0]["submodelElements"][3]["value"][1]
        except:
            print("no secodn element to deleate")

    i = 0
    # remove second process if there
    if len(config["Factory"]["process"]) == 0:
        del example[0]["submodelElements"][4]["value"][0]["value"]
        del example[0]["submodelElements"][4]["value"][1]["value"]
    elif len(config["Factory"]["process"])>1:
        del example[0]["submodelElements"][4]["value"][1]["value"] 
    
    for proc in config["Factory"]["process"]:
        if i == 0:
            # Processes uses exisitng element
            example[0]["submodelElements"][4]["value"][i]["value"] = str(proc)
        else:
            # create new one
            example[0]["submodelElements"][4]["value"].append(str(example[0]["submodelElements"][4]["value"][0]))
            example[0]["submodelElements"][4]["value"][i]["value"] = str(proc)
            example[0]["submodelElements"][4]["value"][i]["idShort"] = "Process_" + str(i) + str(proc)
        i +=1

    # items = data["item"] 
    # if type(items) == list and len(items) > 1:
    #     # multiple items to add
    #     j = 5
    #     for item in items:
    #         if j == 5:
    #         # Processes uses exisitng element
    #             example[0]["submodelElements"][j]["idShort"] = item + data["name"].replace(" ", "_")
    #             try:
    #                 example[0]["submodelElements"][j]["value"][0]["value"] = str(data["energy use"][0])
    #                 example[0]["submodelElements"][j]["value"][1]["value"] = str(data["material use"][0])
    #             except:
    #                 example[0]["submodelElements"][j]["value"][0]["value"] = "unknown"
    #                 example[0]["submodelElements"][j]["value"][1]["value"] = "unknown"
    #         else:
    #             # create new one
    #             example[0]["submodelElements"][j]= example[0]["submodelElements"][5]
    #             example[0]["submodelElements"][j]["idShort"] = item + data["name"].replace(" ", "_")
    #             try:
    #                 example[0]["submodelElements"][j]["value"][0]["value"] = str(data["energy use"][j-5])
    #                 example[0]["submodelElements"][j]["value"][1]["value"] = str(data["material use"][j-5])
    #             except:
    #                 example[0]["submodelElements"][j]["value"][0]["value"] = "unknown"
    #                 example[0]["submodelElements"][j]["value"][1]["value"] = "unknown"
            
    # else:
    #     # only one item to add
    #     example[0]["submodelElements"][5]["idShort"]  = items + data["name"].replace(" ", "_")
    #     try:
    #         example[0]["submodelElements"][5]["value"][0]["value"] = str(data["energy data"]/data["quantity"])
    #         example[0]["submodelElements"][5]["value"][1]["value"] = str(data["material data"]/data["quantity"])
    #     except:
    #         example[0]["submodelElements"][5]["value"][0]["value"] = "unknown"
    #         example[0]["submodelElements"][5]["value"][1]["value"] = "unknown"

    return example

def findAASFromDirec(directory, filename):
    if file_exists(directory, filename):
        direct = os.path.join(directory, filename)
        with open(direct) as json_file:
            data_example = json.load(json_file)
            return data_example
    else:
        return None

def make_parent_AAS(BOM, parent, config,  script_dir):
    totalEnergy = 0
    totalMaterial = []
    mateiralType = []
    quantity = []
    itemName = []
    print(BOM)
    for barcode in BOM:
        print(script_dir)
        new_path = "AAS_data/product/"
        rel_path = os.path.join(script_dir, new_path)
        fileName = str(barcode).replace(".", "_").replace(" ", "_")  + ".json"
        # find ass from barcode
        dictOut = findAASFromDirec(rel_path, fileName)
        if not dictOut:
            j = 1
            while j < 5:
                rel_path = os.path.join(script_dir, new_path) #r'%s' % (script_dir + new_path)
                newFile = str(barcode).replace(".", "_").replace(" ", "_")  + str(j) + ".json"
                dict = findAASFromDirec(rel_path, newFile)
                if dict != None:
                    dictOut = dict
                j = j + 1
        if dictOut and dictOut != None:
            print("data")
            # combining  items together if not combined
            tempItem = dictOut[0]["submodelElements"][0]["value"][0]["value"]
            tempQuant = dictOut[0]["submodelElements"][0]["value"][1]["value"]
            
            if tempItem in itemName:
                index = itemName.index(tempItem)
                quantity[index] = quantity[index] + float(tempQuant)
            else:
                quantity.append(float(tempQuant))
                itemName.append(tempItem)
                
            # add the enrgy used together
            totalEnergy = totalEnergy + float(dictOut[0]["submodelElements"][2]["value"])

            # find array of all materials and add togethe rif the same material
            mat = len(dictOut[0]["submodelElements"][3]["value"]) 
            for i in range(mat):
                tempMat = dictOut[0]["submodelElements"][3]["value"][i]["idShort"] 
                tempVal = dictOut[0]["submodelElements"][3]["value"][i]["value"]
                print(tempMat)
                print(tempVal)
                if type(tempVal) == list:
                    try:
                        tempVal = float(tempVal[0]["value"])
                    except:
                        print("can't find value material")
                else:
                    tempVal = 0
                
                if(tempMat in mateiralType):
                    index = mateiralType.index(tempMat)
                    totalMaterial[index] = totalMaterial[index] + float(tempVal)
                else:
                    mateiralType.append(tempMat)
                    totalMaterial.append(float(tempVal))
                    
            #factory name details 
            name = dictOut[0]["idShort"] 
            factName = dictOut[0]["submodelElements"][1]["value"][0]["value"] 
            factAddress =dictOut[0]["submodelElements"][1]["value"][2]["value"]
            email = dictOut[0]["submodelElements"][1]["value"][3]["value"]

        # add/compile into new AAS for order
    if len(itemName) == 1:
        # only one type of product
        dic = {}
        dic["name"] = parent
        dic["item"] = itemName
        dic["quantity"] = quantity
        dic["start time"] = ""
        dic["end time"] = ""
        dic["job duration"] = ""
        dic["energy use"] = totalEnergy
        dic["machine"] = ""
        dic["material use"] = totalMaterial
        dic["material type"] = mateiralType
        # create new dict for eact type
        add_to_aas(dic, "Order",config)
    elif len(itemName) > 1:
        for i in len(itemName):
            dic = {}
            dic["name"] = parent
            dic["item"] = itemName[i]
            dic["quantity"] = quantity[i]
            dic["start time"] = ""
            dic["end time"] = ""
            dic["job duration"] = ""
            dic["energy use"] = totalEnergy
            dic["machine"] = ""
            dic["material use"] = totalMaterial
            dic["material type"] = mateiralType
            # create new dict for each type
            add_to_aas(dic, "Order", config)
    else:
        print("can't find ASS in order")


def add_to_aas(dict_file_in, typeIn, config):
    # open json file of aas template
    script_dir = findCurrentStore() #os.path.dirname(__file__) #<-- absolute dir the script is in
    rel_path = "AAS_data/templates/Submodel_SR3.json"
    abs_file_path = os.path.join(script_dir, rel_path)
    with open(abs_file_path) as json_file:
        data_example = json.load(json_file)

    # add dict_file data to ass template
    # dict_file_in = AAS submodel 
    # data_example = template AAS
    dict_file = add_data_together(data_example,dict_file_in, config)

    # Serializing json
    json_object = json.dumps(dict_file, indent=4)
    # Writing to sample.json
    script_dir =  findCurrentStore() #os.path.dirname(__file__) #<-- absolute dir the script is in
    
    if typeIn == "Order":
        directory_path  = "AAS_data/order/" 
    elif typeIn == "Product":
        directory_path = "AAS_data/product/"
    else:
        directory_path =  "AAS_data/" 
    rel_path = directory_path + dict_file_in["name"].replace(".", "_").replace(" ", "_") + ".json"
    abs_file_path = os.path.join(script_dir, rel_path)
    i = 1
    while os.path.isfile(abs_file_path) and os.access(abs_file_path, os.R_OK):
        with open(abs_file_path, "r") as outfile:
            data = json.load(outfile)
            if data == dict_file: 
                #print("Data already added")
                return 1
        rel_path = directory_path  + dict_file_in["name"].replace(".", "_") + str(i) + ".json"
        rel_path = rel_path.replace(" ", "_")
        abs_file_path = os.path.join(script_dir, rel_path.replace(" ", "_"))
        i = i+ 1 
    with open(abs_file_path, "w") as outfile:   
        outfile.write(json_object)
        return 0

def add_to_excel(dict_file, csv_file):
    if type(dict_file)==list:
        mydict =dict_file
    else:
        mydict = [dict_file]
    
    fields = ['name', 'item', 'quantity', 'start time', 'end time',  'job duration', 'energy use', 'machine', 'material use', 'material type']
    script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
    rel_path = csv_file
    abs_file_path = os.path.join(script_dir, rel_path)
    if os.path.isfile(abs_file_path) and os.access(abs_file_path, os.R_OK):
        with open(abs_file_path, newline='') as file: 
            reader = csv.reader(file)
            dataOld = list(reader)

    if not os.path.isfile(abs_file_path) and not os.access(abs_file_path, os.R_OK):
        with open(abs_file_path, 'w', newline='') as file: 
            writer = csv.DictWriter(file, fieldnames = fields)
            # writing headers (field names)
            writer.writeheader()
            writer.writerows(mydict)
    else:
      with open(abs_file_path, 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames = fields)
            notInFile = True
            for mydictrows in mydict:
                for datarows in dataOld:
                    if mydictrows[fields[0]] == datarows[0] and mydictrows[fields[1]] == datarows[1] and mydictrows[fields[3]] == datarows[3] and mydictrows[fields[4]] == datarows[4]:
                        notInFile =False
                if notInFile:
                    writer.writerow(mydictrows)

def findOrderInfo(barcode):
    dataBack = frepple.ordersIn("GET", {"name": str(barcode)})
    if len(dataBack) !=0:
        if type(dataBack) == list:
            itemName = dataBack[0]["item"]
            quantity = dataBack[0]["quantity"]
        else:
            itemName = dataBack["item"]
            quantity = dataBack["quantity"]
        return itemName, quantity
        # no order data from frepple try to find item informaiton based on file
    dataBack = frepple.itemsFunc("GETALL", {"decritpion": str(barcode)})
    if len(dataBack) !=0:
        if type(dataBack) == list:
            itemName = dataBack[0]["item"]
            quantity = dataBack[0]["quantity"]
        else:
            itemName = dataBack["item"]
            quantity = dataBack["quantity"]
        return itemName, quantity
    itemName = ""
    quantity = 1
    
    return itemName, quantity

def createDictAndSave(dat, last_reading_stored, config):
    dictionaryOdASSData = {}
    dictionaryOdASSData["name"] = dat[3]
    itemName, quantity = findOrderInfo(dat[3])
    dictionaryOdASSData["item"] = itemName
    dictionaryOdASSData["quantity"] = quantity
    dictionaryOdASSData["start time"] = dat[0].strftime("%Y-%m-%d %H:%M:%S") 
    dictionaryOdASSData["end time"] = dat[1].strftime("%Y-%m-%d %H:%M:%S") 
    dictionaryOdASSData["job duration"] = (dat[1]-dat[0]).total_seconds()
    dictionaryOdASSData["energy use"] = dat[5]
    dictionaryOdASSData["machine"] = dat[6]
    materialUse, materialType = findMaterialUseData(config["material_use"]["frequency"], itemName, quantity)
    dictionaryOdASSData["material use"] = materialUse
    dictionaryOdASSData["material type"] = materialType
    # create Json file 
    # create Json or excel file 
                    
    if "json" in fileType or "JSON" in fileType:
        create_json(dictionaryOdASSData)
    if "csv" in fileType or "CSV" in fileType:
        add_to_excel(dictionaryOdASSData, "output/csv/AAS_Data.csv")
    if "aas" in fileType or "AAS" in fileType:
        add_to_aas(dictionaryOdASSData, "Product", config)
    dat[0] =dat[0].replace(tzinfo=utc)
    #dat[0] = utc.localize(dat[0])

    if dat[0] > last_reading_stored:
        last_reading_stored = dat[0]
    return last_reading_stored


def updateExcelorDict(config, freppleConnect, timeSinceLast, fileType):
    # update or add to JSON files or excel of both
    # find the order number or name of file if none
    # search for all complete orders in MES first
    # find days/time back since last reading
    last_reading_stored = datetime.now() - timedelta(seconds= timeSinceLast)
    last_reading_stored = utc.localize(last_reading_stored)
    timeSinceLast = str(round(timeSinceLast)) + "s"
    if config["Factory"]["name"] == "3D Printing":
        machine = config["Factory"]["machine"]
        for machin in machine:
            data = influxClient.jobLengthEnergyWithSignal(machin, timeSinceLast)
            #data = [ startTime [0], endTime [1], duration [2], jobFile/barcode [3], 
                    # complete [4], energyUse [5], machine [6]]
            #data = findJobTimesSignal(config["order_time_taken"], [])
            for dat in data:
                if dat[4] != False:
                    last_reading_stored = createDictAndSave(dat, last_reading_stored, config)
    elif config["Factory"]["name"] == "Manual Assembly":
        machine = config["Factory"]["machine"]
        for machin in machine:
            data = influxClient.jobLengthEnergyWithTracking(machin, timeSinceLast, config["order_time_taken"]["start_location"], config["order_time_taken"]["end_location"])
            for dat in data:
                # create new file
                last_reading_stored = createDictAndSave(dat, last_reading_stored, config)
    elif config["Factory"]["name"] == "Robot Lab":
        machine = config["Factory"]["machine"]
        for machin in machine:
            data = influxClient.jobLengthEnergyWithTracking(machin, timeSinceLast, config["order_time_taken"]["start_location"], config["order_time_taken"]["end_location"])
            for dat in data:
                # create new file
                print(dat)
                last_reading_stored = createDictAndSave(dat, last_reading_stored, config)
    else:
        print("file found")

    return last_reading_stored
        
def updateOrderASS(config, frepple, timeSinceLast, fileType, locationOut):
    script_dir =  findCurrentStore()
    timeSinceLast = str(round(timeSinceLast)) + "s"
    ordersCompleated = influxClient.findJobsAtLocation(locationOut, timeSinceLast)
    if ordersCompleated: # orderscompleated is not null
        for order in ordersCompleated:
            # check if AAS already exisits 
            path_local = "AAS_data/product/"
            rel_path =  os.path.join(script_dir, path_local) 
            filename = str(order) + ".json"
            print("*********")
            print(script_dir)
            print(rel_path)
            if not file_exists(rel_path, filename):
                # find all children asociated with the ASS 
                BOM = influxClient.jobFindChildren(order[0], 300)
                if len(BOM) > 0:
                    # create an order ASS 
                    make_parent_AAS(BOM, order[0], config,  script_dir)


def file_exists(directory, filename):
    filepath = os.path.join(directory, filename)
    return os.path.exists(filepath)

def folder_exists(directory, folder_name):
    # Get the current working directory
    # Construct the path to the folder
    folder_path = os.path.join(directory, folder_name)
    # Check if the folder exists
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        return True
    else:
        return False

def findCurrentStore():
    path = os.getcwd()
    if not folder_exists(path, "AAS_data"):
        parent = os.path.abspath(os.path.join(path, os.pardir))
        if not folder_exists(parent, "AAS_Data"):
            script_dir = os.path.abspath(os.path.join(parent, os.pardir))
        else:
            script_dir = parent
    else:
        script_dir = path
    return script_dir

if __name__ == "__main__":
    script_dir_con = os.path.dirname(__file__) #<-- absolute dir the script is in
    rel_path = "config\\config_3d_IP.toml"
    abs_file_path = os.path.join(script_dir_con, rel_path)

    with open(abs_file_path, mode="rb") as fp:
        config = tomli.load(fp)

    # connect to MES
    user =config["frepple_info"]["user"]
    password = config["frepple_info"]["password"]
    URL = config["frepple_info"]["URL"]

    configInflux = config["influx_info"]
    fileType = config["Factory"]["fileType"]
    # intialise the connection to the database and MES
    print(configInflux)
    influxClient = fetchData(configInflux)
    try:
        frepple = freppleConnect(user, password, URL)
    except:
        print("No MES connection")
        frepple =""

    
    # Check for last exisitng file in folder of AAS data   
    # script_dir = Path(__file__).parent.parent
    script_dir = findCurrentStore()
    print("scipt dir")
    print(script_dir)
    path_local = "AAS_data/product/"

    #script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
    dateLastUpdate = utc.localize(datetime.now() - timedelta(hours = config["Factory"]["first_check"]))
    if fileType == "JSON" or fileType == "json":
        #rel_path = "output/json/"
        rel_path = "AAS_data/product/"
        abs_file_path = os.path.join(script_dir, rel_path)
        
        most_recent_file = None
        most_recent_time = 0
        fileFound = False
        for entry in os.scandir(abs_file_path):
            if entry.is_file():
                fileFound = True
                # get the modification time of the file using entry.stat().st_mtime_ns
                mod_time = entry.stat().st_mtime_ns
                if mod_time > most_recent_time:
                    # update the most recent file and its modification time
                    most_recent_file = entry.name
                    most_recent_time = mod_time
                    
        if fileFound:
            rel_path = "AAS_data/product/" + most_recent_file 
            abs_file_path = os.path.join(script_dir, rel_path)
            print(abs_file_path)
            print("exisitng files")
            with open(abs_file_path, "r") as outfile:
                data = json.load(outfile)
                dateLastUpdate = utc.localize(datetime.strptime(data["start time"], '%Y-%m-%d %H:%M:%S'))
    
    else: # not json file look for csv file if it exisits 
        rel_path = "AAS_data/product/AAS_Data.csv"
        abs_file_path = os.path.join(script_dir, rel_path)
        if os.path.isfile(abs_file_path) and os.access(abs_file_path, os.R_OK):
            with open(abs_file_path, newline='') as file: 
                reader = csv.reader(file)
                i = 0
                for row in reader:
                    i +=1
                    if i > 2:
                        newDate = utc.localize(datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S'))
                        if newDate > dateLastUpdate:
                            dateLastUpdate = newDate
                
    timLastupdate = utc.localize(datetime.now())
    while True:
        
        print("Started collecting")
        timeWait = config["Factory"]["frequencyUpdate"]
        if ((utc.localize(datetime.now()) - timLastupdate ).total_seconds()/5)> timeWait:
            print("updating ...")
            
            dateLastUpdate = utc.localize(datetime(year = dateLastUpdate.year, 
                                       month = dateLastUpdate.month, 
                                       day = dateLastUpdate.day, hour =0, minute =0, second =1))
            timeSinceLast = (utc.localize(datetime.now()) - dateLastUpdate).total_seconds()
            # print(timeSinceLast)
            dateLastUpdate = updateExcelorDict(config, frepple, timeSinceLast, fileType)
            print("completed, last reading at" + dateLastUpdate.strftime("%Y-%m-%d %H:%M:%S"))
            
            updateOrderASS(config, frepple, timeSinceLast, "AAS", "Goods Out")

            timLastupdate = utc.localize(datetime.now())


        else:
            time.sleep(10)


    


