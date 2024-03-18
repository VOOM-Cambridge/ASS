import json
from datetime import datetime
import time
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

""" 
This class is designed to help format use of the influx client and API
For each databases connected to, organisations or buckets a different instance can be created
"""
class influxUploadData:
    def __init__(self, config_file_json):
        self.org = config_file_json['org']
        self.token = config_file_json['token']
        self.url = config_file_json['url']
        self.freq = config_file_json["frequency_record_seconds"]
        self.influx_client = InfluxDBClient(
            url=self.url,
            token=self.token,
            org=self.org,
            verify_ssl=False)
        #print(self)
    
    def store_data(self, reading_name, data, machine_name, measurementName, timeStamp):
        # make timeStamp input = None or [] to store the time now otherwise it uses timeStamp
        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        if type(data) != list and type(data) != dict: 
            # if not a list format make it a list format 
            data = [data]
            machine_name = [machine_name]
            reading_name = [reading_name]
            timeStamp = [timeStamp]
        leng = len(data)
        for i in range(leng):
            if timeStamp[i] == None or timeStamp[i] == []:
                date_time = timeStamp[i]
                point = Point.measurement(measurementName).tag("machine", machine_name[i]).field(reading_name[i], data[i]).time(date_time)
            else:
                point = Point.measurement(measurementName).tag("machine", machine_name[i]).field(reading_name[i], data[i])
            self.write_api.write(bucket=self.bucketName, org=self.org, record=point)
            #print("submitted")

    