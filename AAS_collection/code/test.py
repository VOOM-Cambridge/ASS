import json
import os
from fetchDataInflux import fetchData
import tomli
from influxdb_client import InfluxDBClient, Point
from datetime import datetime, timedelta
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
# user =config["frepple_info"]["user"]
# password = config["frepple_info"]["password"]
# URL = config["frepple_info"]["URL"]

# configInflux = config["influx_info"]
# fileType = config["Factory"]["fileType"]
# # intialise the connection to the database and MES
# influxClient = fetchData(configInflux)

# #sTime, eTime = influxClient.jobLengthTime("", 200)
# data = influxClient.jobFindChildren("3DOR1000", 100)
# #data = influxClient.jobFindParents('1177', 100)

# #data = influxClient.findClosestBarcode(endTime, "3DP100400")
# print(data)

# for dat in data:
#     print(influxClient.jobFindChildren(dat, 100))
    
x = "C:\\Users\\sjb351\\OneDrive - University of Cambridge\\Work file\\Programing.Development\\AAS work\\AAS_data\\product\\blob_2_aw_gcode.json"

ans = os.path.isFile()
print(ans)