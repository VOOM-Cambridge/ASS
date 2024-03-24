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



rel_path = "/config/config_DS_IP.toml"
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
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

def clear_bucket_data(bucket_name):
    # Initialize InfluxDB client
    client = InfluxDBClient(url=configInflux["url"], token=configInflux["token"], org=configInflux["org"])

    # Get delete API
    delete_api = client.delete_api()

    # Delete all data from the bucket
    delete_api.delete(start="1970-01-01T00:00:00Z", stop="2100-01-01T00:00:00Z", predicate='', bucket=bucket_name)

    print(f"All data deleted from the '{bucket_name}' bucket.")

# Example usage:
bucket_name = "your_bucket_name"
clear_bucket_data("tracking_data")


# #data = influxClient.findClosestBarcode(endTime, "3DP100400")


# for dat in data:
#     print(influxClient.jobFindChildren(dat, 100))
