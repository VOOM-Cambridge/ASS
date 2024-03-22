import json
import os
from fetchDataInflux import fetchData
import tomli
from influxdb_client import InfluxDBClient, Point
from datetime import datetime, timedelta
from freppleAPImodule import freppleConnect
script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
# rel_path = "/output/AAS/Submodel.json"

# with open(abs_file_path) as json_file:
#     example = json.load(json_file)

# dispatch time
# copy example["submodelElements"][5]
# example["submodelElements"][5]["idShort"] = "name of part"
# example["submodelElements"][5]["value"][0]["value"] = "energy per part"
# example["submodelElements"][5]["value"][1]["value"] = "material per part"
# del example["submodelElements"][6] if one part



rel_path = "/config/config_3d_IP.toml"
abs_file_path = script_dir + rel_path
with open(abs_file_path, mode="rb") as fp:
    config = tomli.load(fp)

# # connect to MES
user =config["frepple_info"]["user"]
password = config["frepple_info"]["password"]
URL = config["frepple_info"]["URL"]
frepple = freppleConnect(user, password, URL)

configInflux = config["influx_info"]
influxClient = fetchData(configInflux)
# fileType = config["Factory"]["fileType"]
# # intialise the connection to the database and MES


#data = frepple.ordersIn("GETALL", {"name": "EMS00000"})

# #sTime, eTime = influxClient.jobLengthTime("", 200)
# data = influxClient.jobFindChildren("3DOR1000", 100)
data = influxClient.jobFindBOM('DSTLV10007', 100)

# #data = influxClient.findClosestBarcode(endTime, "3DP100400")
print(data)

# for dat in data:
#     print(influxClient.jobFindChildren(dat, 100))
