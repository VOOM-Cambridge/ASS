import json
from datetime import datetime, timedelta
import time
from uploadDataInflux import influxUploadData
import logging
from scipy.signal import find_peaks
import numpy as np


class fetchData(influxUploadData):
        
    def findWorkData(self, startTime, endTime, diff, location):
        
        query_api = self.influx_client.query_api()
        eTime = round(time.mktime(endTime.timetuple())) + diff
        sTime = round(time.mktime(startTime.timetuple())) - diff
            # query to find all the different people who logged in durign that job in case more thank one
        query = 'from(bucket: "worker_data")\
                    |> range(start: '+str(sTime)+', stop: '+str(eTime)+')\
                    |> filter(fn: (r) => r["_measurement"] == "worker_scan")\
                    |> filter(fn: (r) => r["location"] == "'+ location +'")\
                    |> filter(fn: (r) => r["state"] == "Log in")\
                    |> unique(column: "_value")'
        table = query_api.query(query)
        output = table.to_values(columns=['_value'])
            # take value from integration and divide by the number of seconds past 
        workerList = []
        timePast = []
        [workerList.append(x[0]) for x in output]
        logInInfo = []
        logOutInfo = []
        for worker in workerList:
            
            query1 = 'from(bucket: "worker_data")\
                    |> range(start: '+str(sTime)+', stop: '+str(eTime)+')\
                    |> filter(fn: (r) => r["_measurement"] == "worker_scan")\
                    |> filter(fn: (r) => r["location"] == "'+ location +'")\
                    |> filter(fn: (r) => r["state"] == "Log in")\
                    |> filter(fn: (r) => r["_value"] == "'+ worker +'")'
            
            query2 = 'from(bucket: "worker_data")\
                    |> range(start: '+str(sTime)+', stop: '+str(eTime)+')\
                    |> filter(fn: (r) => r["_measurement"] == "worker_scan")\
                    |> filter(fn: (r) => r["location"] == "'+ location +'")\
                    |> filter(fn: (r) => r["state"] == "Log out")\
                    |> filter(fn: (r) => r["_value"] == "'+ worker +'")'
            
            tableIn = query_api.query(query1)
            tableOut = query_api.query(query2)
            outputIn = tableIn.to_values(columns=['_time'])
            outputOut = tableOut.to_values(columns=['_time'])
            [logInInfo.append(x[0]) for x in outputIn]
            [logOutInfo.append(x[0]) for x in outputOut]
            # print(worker)
            # print(logInInfo)
            # print(logOutInfo)
            if len(outputOut)>0 and len(outputIn)>0:
                timeP = []
                minRange = min(len(outputOut),len(outputIn))
                for i in range(minRange):
                    timeP.append((outputOut[i][0] - outputIn[i][0]).total_seconds())
                timePast.append(timeP)
        timeP2 =[]
        timeBetween = []
        minRange = min(len(logInInfo),len(logOutInfo))
        logInInfo.sort()
        logOutInfo.sort()
        for i in range(1, minRange):
            timeBetween.append((logInInfo[i] - logOutInfo[i-1]).total_seconds())
            timeP2.append((logOutInfo[i] - logInInfo[i]).total_seconds())
        #tot = (endTime-startTime).total_seconds()
        return workerList, timeP2, timeBetween #, tot
    
    def findWorkDataNew(self, startTime, endTime, diff, location):
        query_api = self.influx_client.query_api()
        eTime = round(time.mktime(endTime.timetuple())) + diff
        sTime = round(time.mktime(startTime.timetuple())) - diff
            # query to find all the different people who logged in durign that job in case more thank one
        query = 'from(bucket: "worker_data")\
                    |> range(start: '+str(sTime)+', stop: '+str(eTime)+')\
                    |> filter(fn: (r) => r["_measurement"] == "worker_scan")\
                    |> filter(fn: (r) => r["location"] == "'+ location +'")\
                    |> filter(fn: (r) => r["state"] == "Log in")\
                    |> unique(column: "id")'
        table = query_api.query(query)
        output = table.to_values(columns=['id'])
        # take value from integration and divide by the number of seconds past 
        workerList = []
        timePast = []
        [workerList.append(x[0]) for x in output]
        logInInfo = []
        logOutInfo = []
        for worker in workerList:
            
            query1 = 'from(bucket: "worker_data")\
                    |> range(start: '+str(sTime)+', stop: '+str(eTime)+')\
                    |> filter(fn: (r) => r["_measurement"] == "worker_scan")\
                    |> filter(fn: (r) => r["location"] == "'+ location +'")\
                    |> filter(fn: (r) => r["state"] == "Log in")\
                    |> filter(fn: (r) => r["id"] == "'+ worker +'")'
            
            query2 = 'from(bucket: "worker_data")\
                    |> range(start: '+str(sTime)+', stop: '+str(eTime)+')\
                    |> filter(fn: (r) => r["_measurement"] == "worker_scan")\
                    |> filter(fn: (r) => r["location"] == "'+ location +'")\
                    |> filter(fn: (r) => r["state"] == "Log out")\
                    |> filter(fn: (r) => r["id"] == "'+ worker +'")'
            
            tableIn = query_api.query(query1)
            tableOut = query_api.query(query2)
            outputIn = tableIn.to_values(columns=['_time'])
            outputOut = tableOut.to_values(columns=['_time'])
            [logInInfo.append(x[0]) for x in outputIn]
            [logOutInfo.append(x[0]) for x in outputOut]
            print(worker)
            if len(outputOut)>0 and len(outputIn)>0:
                print("**********")
                timeP = []
                minRange = min(len(outputOut),len(outputIn))
                for i in range(minRange):
                    timeP.append((outputOut[i][0] - outputIn[i][0]).total_seconds())
                timePast.append(timeP)
        timeP2 =[]
        timeBetween = []
        minRange = min(len(logInInfo),len(logOutInfo))
        logInInfo.sort()
        logOutInfo.sort()
        print(logInInfo)
        print(len(logInInfo))
        print(logOutInfo)
        print(len(logOutInfo))
        for i in range(5, minRange):
            timeBetween.append((logInInfo[i] - logOutInfo[i-1]).total_seconds())
            timeP2.append((logOutInfo[i] - logInInfo[i]).total_seconds())
        return workerList, timePast, timeBetween
    
    def findEnergyUse(self, startTime, endTime, robotName):
        powerValueFinal = 0
        if type(robotName) != list:
            robotName = [robotName]
        for robotN in robotName:
            query_api = self.influx_client.query_api()
            eTime = round(time.mktime(endTime.timetuple()))
            sTime = round(time.mktime(startTime.timetuple()))
            # query to integrate the machine state curve to find utilisation
            query = 'from(bucket: "power_monitoring")\
                |> range(start:' + str(sTime) +', stop: '+ str(eTime) + ')\
                |> filter(fn: (r) => r["_measurement"] == "equipment_power_usage")\
                |> filter(fn: (r) => r["_field"] == "power" or r["_field"] == "power2" or r["_field"] == "power3")\
                |> filter(fn: (r) => r["machine"] == "'+robotN+'")\
                |> integral(unit: 1s)'
            table = query_api.query(query)
            output = table.to_values(columns=['_value'])
            #print(output)
            # take value from integration and divide by the number of seconds past 
            try:
                if len(output) == 1:
                    powerValue = output[0][0]
                else:
                    powerValue = sum(sum(output,[]))
            except:
                powerValue = 0
                print("no power values found in data")
            powerValueFinal = powerValueFinal + powerValue

        return powerValueFinal/3600000
    
    
    def jobFindChildren(self, barcode, numberDaysBack):
        query_api = self.influx_client.query_api()
        if barcode == None:
            return "unkown"
        query = 'from(bucket: "tracking_data_comp")\
                |> range(start: -' + str(numberDaysBack) + ')\
                |> filter(fn: (r) => r["_measurement"] == "Tracking_comp")\
                |> filter(fn: (r) => r["_field"] == "child")\
                |> filter(fn: (r) => r["parent"] == "'+ barcode +'")'
        table = query_api.query(query)
        output = table.to_values(columns=['_value'])
        out = [x[0] for x in output]
        return out
    
    def jobFindBOM(self, barcode, numberDaysBack):
        query_api = self.influx_client.query_api()
        if barcode == None:
            return "unkown"
        query = 'from(bucket: "tracking_data_comp")\
                |> range(start: -' + str(numberDaysBack) + ')\
                |> filter(fn: (r) => r["_measurement"] == "Tracking_comp")\
                |> filter(fn: (r) => r["_field"] == "child")\
                |> filter(fn: (r) => r["parent"] == "'+ barcode +'")'
        table = query_api.query(query)
        output = table.to_values(columns=['_value'])
        out = {}
        out["id"] = barcode
        out["parts"] = []
        out["quantity"] = []
        for x in output:
            if x[0] in out["parts"]:
                ind = out["parts"].index(x[0])
                out["quantity"][ind] = out["quantity"][ind] +1
            else:
                out["parts"].append(x[0])
                out["quantity"].append(1)
        for i in range(len(out["quantity"])):
           out["quantity"][i]= str(out["quantity"][i])
           out["parts"][i]= out["parts"][i].replace(" ", "_").replace(".", "_")
        return out
    
    def jobFindParents(self, barcode, numberDaysBack):
        query_api = self.influx_client.query_api()
        if barcode == None:
            return "unkown"
        query = 'from(bucket: "tracking_data_comp")\
                |> range(start: -' + str(numberDaysBack) + ')\
                |> filter(fn: (r) => r["_measurement"] == "Tracking_comp")\
                |> filter(fn: (r) => r["_field"] == "parent")\
                |> filter(fn: (r) => r["child"] == "' + barcode + '")'
        table = query_api.query(query)
        output = table.to_values(columns=['_value'])
        out = [x[0] for x in output]
        return out
    
    def findEnergyData(self, startTime, endTime, robotName):
        powerValueFinal = 0
        if type(robotName) != list:
            robotName = [robotName]
        for robotN in robotName:
            query_api = self.influx_client.query_api()
            eTime = round(time.mktime(endTime.timetuple()))
            sTime = round(time.mktime(startTime.timetuple()))
            # query to integrate the machine state curve to find utilisation
            query = 'from(bucket: "power_monitoring")\
                |> range(start:' + str(sTime) +', stop: '+ str(eTime) + ')\
                |> filter(fn: (r) => r["_measurement"] == "equipment_power_usage")\
                |> filter(fn: (r) => r["_field"] == "power" or r["_field"] == "power2" or r["_field"] == "power3")\
                |> filter(fn: (r) => r["machine"] == "'+robotN+'")'
            table = query_api.query(query)
            output = table.to_values(columns=['_field', '_time','_value'])
            #print(output)
            # take value from integration and divide by the number of seconds past 
        
        x = []
        x2 =[]
        x3 =[]
        timeVal = []
        timeVal2 = []
        timeVal3 = []
        for out in output:
            if out[0] == "power":
                timeVal.append(out[1])
                x.append(out[2])
            elif out[0] == "power2":
                timeVal2.append(out[1])
                x2.append(out[2])
            elif out[0] == "power3":
                timeVal3.append(out[1])
                x3.append(out[2])
       # print([len(x), len(x2), len(x3)])
        maxLen = max([len(x), len(x2), len(x3)])
        for i in range(maxLen):
            try:
                x[i] = x[i] + x2[i] + x3[i]
            except: 
                x[i] = x[i]
        return x, timeVal
    
    def findEnergyDataSignal(self, startTime, endTime, robotName, approxAssTime, diff):
        # values 
        samplesTime = 10
        minSamplesBetween = 1
        minSamplesBetweenBig = 3
        timeBetweenAssem = approxAssTime #seconds
        #maxAssTime = 400 # seconds
        diss = int(timeBetweenAssem/samplesTime)

        query_api = self.influx_client.query_api()
        eTime = round(time.mktime(endTime.timetuple()))
        sTime = round(time.mktime(startTime.timetuple()))
        # query to integrate the machine state curve to find utilisation
        query = 'from(bucket: "power_monitoring")\
            |> range(start:' + str(sTime) +', stop: '+ str(eTime) + ')\
            |> filter(fn: (r) => r["_measurement"] == "equipment_power_usage")\
            |> filter(fn: (r) => r["_field"] == "power" or r["_field"] == "power2" or r["_field"] == "power3")\
            |> filter(fn: (r) => r["machine"] == "'+robotName+'")'
        table = query_api.query(query)
        output = table.to_values(columns=['_time','_value'])
        x = []
        timeVal = []
        [x.append(y[1]) for y in output]
        [timeVal.append(y[0]) for y in output]
        peaks, properties = find_peaks(x, prominence=60, width=minSamplesBetween, distance=diss )
        peaksBig, propertiesB = find_peaks(x, prominence=200, width=minSamplesBetweenBig)
        peaksBig2, propertiesB2 = find_peaks(x, prominence=500, width=minSamplesBetween)
        peaksBig = np.concatenate((peaksBig, peaksBig2))
        peakXVal = []
        peakXValBig = []
        [peakXVal.append(x[y]) for y in peaks]
        [peakXValBig.append(x[y]) for y in peaksBig]
        timingsAssem = []
        diffArray = []
        peakList =[]

        try:
            timePeakOld = timeVal[0]
        except:
            print("no energy data")
        for peak in peaks:
            timePeak = timeVal[peak]
            diffBetween = (timePeak - timePeakOld).total_seconds()
            if peak in peaksBig or diffBetween > approxAssTime + diff or diffBetween < approxAssTime - diff :
                # then more than one tray is moving, otherwise one tray moving
                timePeakOld = timePeak
            else:
                # one tray moving so job finished
                timingsAssem.append([timePeakOld, timePeak])
                diffArray.append(diffBetween)
                timePeakOld = timePeak
                peakList.append(peak)
        #print(diffArray)
        #print(output)
        # take value from integration and divide by the number of seconds past 
        return timingsAssem, diffArray
    
    def findJobsAtLocation(self, location, numbersecondsBack):
        query_api = self.influx_client.query_api()
        
        query = 'from(bucket: "tracking_data")\
                |> range(start: -' + str(numbersecondsBack) + ')\
                |> filter(fn: (r) => r["_measurement"] == "tracking")\
                |> filter(fn: (r) => r["location"] == "'+location+'")'
        table = query_api.query(query)
        output = table.to_values(columns=['_value'])

        return output  # output of vlaues [[value1], [value2] .. ]


    def jobLengthTime(self, barcode, numberDaysBack, locationStart, locationEnd):
        query_api = self.influx_client.query_api()
        if barcode == None:
            return "unkown", "unkown"
        
        query = 'from(bucket: "tracking_data")\
                |> range(start: -' + str(numberDaysBack) + ')\
                |> filter(fn: (r) => r["_measurement"] == "tracking")\
                |> filter(fn: (r) => r["_value"] == "'+barcode+'")\
                |> filter(fn: (r) => r["location"] == "'+locationEnd+'")'
        table = query_api.query(query)
        output = table.to_values(columns=['_time'])
        if len(output) == 1:
            timeEnd = output[0]
        elif len(output) > 1:
            finalTimes =[]
            # check the barcode wasn't scnaned twice by accident, if so keep the first scan
            for i in range(1, len(output)):
                if (output[i][0] - output[i-1][0]).total_seconds() > 30:
                    finalTimes.append(output[i-1])
                    if i == len(output)-1:
                        finalTimes.append(output[i])
            timeEnd = finalTimes
        else:
            timeEnd = "unkown"

        query_api = self.influx_client.query_api()
        query = 'from(bucket: "tracking_data")\
                |> range(start: -' + str(numberDaysBack) + ')\
                |> filter(fn: (r) => r["_measurement"] == "tracking")\
                |> filter(fn: (r) => r["_value"] == "'+barcode+'")\
                |> filter(fn: (r) => r["location"] == "'+locationStart+'")'
        table = query_api.query(query)
        output = table.to_values(columns=['_time'])
        if len(output) == 1:
            timeStart = output[0]
        elif len(output) > 1:
            finalTimes =[]
            # check the barcode wasn't scnaned twice by accident, if so keep the first scan
            for i in range(1, len(output)):
                if (output[i][0] - output[i-1][0]).total_seconds() > 30:
                    
                    finalTimes.append(output[i-1])
                    if i == len(output)-1:
                        finalTimes.append(output[i])
            timeStart = finalTimes
        else:
            timeStart = "unkown"

        # compare readings if any to see if start and end scan were close showing test was too fast
        # limit set to 5 seconds
        iE =[]
        iS =[]
        
        if timeStart != "unkown" and timeEnd != "unkown":
            for indS in timeStart:
                for indE in timeEnd:
                    try:
                        if (indE[0] - indS[0]).total_seconds() < 5:
                            iE.append(indE)
                            iS.append(indS)
                    except:
                        if (type(indE)==list and type(indS)!=list):
                            indE = indE[0]
                        elif(type(indS)==list and type(indE)!=list):
                            indS = indS[0]

                        if (indE - indS).total_seconds() < 5:
                            iE.append(indE)
                            iS.append(indS)
                            
            for i in iE:
                try:
                    timeEnd.remove(i[0])
                except: 
                    True
            for i in iE:
                try:
                    timeStart.remove(i[0])
                except: 
                    True

        if type(timeEnd) ==list or type(timeStart) == list:
            if len(timeEnd) != len(timeStart):
                print("error data not the same length")
                timeStart = "unkown"
                timeEnd = "unkown"
        if (timeStart == "unkown" and timeEnd != "unkown") or (timeStart != "unkown" and timeEnd == "unkown"):
            timeEnd = "unkown"
            timeStart = "unkown"
        return timeStart, timeEnd
    
    def jobLengthEnergyWithTracking(self, machine, timesBack, locationS, locationE):
        data =[]
        # data contians [ startTime endTime duration jobFile complete, energyUse, machine]
        # find all the barcode numbers
        query_api = self.influx_client.query_api()
        query = 'from(bucket: "tracking_data")\
                        |> range(start: -' + timesBack + ')\
                        |> filter(fn: (r) => r["_measurement"] == "tracking")\
                        |> filter(fn: (r) => r["_field"] == "id")\
                        |> unique()'
        table = query_api.query(query)    
        barcodes = table.to_values(columns=['_value'])

        # for each barcode found find the job length times if they exist
        for barcode in barcodes:
            startTime, endTime = self.jobLengthTime(barcode[0], timesBack, locationS, locationE)
            
            if startTime != "unkown" or endTime != "unkown" or len(startTime) != len(endTime):
                startTime = self.makeList(startTime)
                endTime = self.makeList(endTime)
                for i in range(len(startTime)):
                    try:
                        datPart = self.fillData(startTime[i][0], endTime[i][0], machine, False, barcode)
                    except:
                        datPart = self.fillData(startTime[i], endTime[i], machine, False, barcode)
                    data.append(datPart)
        return data
    
    def makeList(self, valueIn):
        if type(valueIn) != list and len(valueIn) ==1:
            return [valueIn]
        else:
            return valueIn
        

    def jobLengthEnergyWithSignal(self, machine, timesBack):
        data =[]
        # data contians [ startTime endTime duration jobFile complete, energyUse, machine]
        query_api = self.influx_client.query_api()
        query = 'from(bucket: "printer_data")\
                    |> range(start: -' + timesBack + ')\
                    |> filter(fn: (r) => r["_measurement"] == "API_data")\
                    |> filter(fn: (r) => r["machine"] == "'+ machine+ '")\
                    |> filter(fn: (r) => r["_field"] == "status")\
                    |> derivative()\
                    |> filter(fn: (r) => r._value != 0)'
        table = query_api.query(query)    
        outputDeriv = table.to_values(columns=['_time', '_value'])
        query_api = self.influx_client.query_api()
        query = 'import "date"\
                import "influxdata/influxdb/monitor"\
                from(bucket: "printer_data")\
                    |> range(start: -' + timesBack + ')\
                    |> filter(fn: (r) => r["_measurement"] == "API_data")\
                    |> filter(fn: (r) => r["machine"] == "'+ machine+ '")\
                    |> filter(fn: (r) => r["_field"] == "status")\
                    |> monitor.deadman(t: date.add(d: -5m, to: now()))'
        table = query_api.query(query)
        outputOnOff = table.to_values(columns=['_time'])
        for i in range(len(outputDeriv)-1):
            if outputDeriv[i][1] > 0 and outputDeriv[i+1][1] < 0:
                # starting print job and end time found by off and on signal
                # check no lost connection signaling off during produciton
                if self.checkDates(outputDeriv[i][0], outputDeriv[i+1][0], outputOnOff) == None:
                    if outputDeriv[i][0] < outputDeriv[i+1][0]:
                        datPart = self.fillData(outputDeriv[i][0], outputDeriv[i+1][0], machine, True, "")
                        data.append(datPart)
                    else:
                        print("Error: time print out")
                else:
                    print("Time found in between on off time")
        return data

    def fillData(self, startTime, endTime, machines, machineSignal, barcode):
        # data contians [ startTime, endTime, duration, jobFile/barcode, complete, energyUse, machine]
        datPart = [0, 0, 0, "", "", "", ""]
        datPart[0] = startTime
        datPart[1] = endTime
        datPart[2] = (datPart[1] - datPart[0]).total_seconds()
        machineStr = ""
        energy =0
        if type(machines) != list:
            machines = [machines]
        for machine in machines:
            energy = energy + self.findEnergyUse(datPart[0], datPart[1], machine)
            machineStr = machineStr + machine
            if machineSignal:
                barcodeClosest = self.findClosestBarcode(datPart[1], machine)
                if barcodeClosest:
                    datPart[3] = barcodeClosest
                else:
                    datPart[3] = self.findFileJobName(datPart[0], datPart[1], machine)
                datPart[4] = self.checkComplete(datPart[0], datPart[1], machine)
            else:
                datPart[3] = barcode[0]
                machineStr = ""
        datPart[5] = energy
        datPart[6] = machineStr
        return datPart

    def checkDates(self, sTime, eTime, checkTime):
        i = 0
        indexes = []
        for cTimes in checkTime:
            try:
                if sTime < cTimes[0] < eTime:
                    indexes.append(i)
                i =+ i
            except AssertionError as error:
                print(error)
        if indexes == []:
            return None
        else:
            return indexes

    def findClosestBarcode(self, endTime, machine):
        endTimeDelta = (endTime + timedelta(hours=12))
        endTimeStart = (endTime - timedelta(hours=12))
        eTime = round(time.mktime(endTimeDelta.timetuple()))
        sTime = round(time.mktime(endTimeStart.timetuple()))
        query_api = self.influx_client.query_api()
        query = 'from(bucket: "tracking_data_comp")\
                |> range(start:' + str(sTime) +', stop: '+ str(eTime) + ')\
                |> filter(fn: (r) => r["_measurement"] == "Tracking_comp")\
                |> filter(fn: (r) => r["_field"] == "child")\
                |> filter(fn: (r) => r["parent"] == "'+ machine +'")'
        table = query_api.query(query)
        output = table.to_values(columns=['_value', '_time'])
        timeFromClosest = abs(timedelta(days=365).total_seconds())
        reading = None
        for out in output:
            eTime = endTime.replace(tzinfo=None)
            timeFromReading = abs((out[1].replace(tzinfo=None) - eTime).total_seconds())
            if timeFromReading < timeFromClosest:
                timeFromClosest = timeFromReading
                reading = out
        if reading:
            return reading[0]
        else:
            return None

    def findFileJobName(self, startTime, endTime, machine):
        eTime = round(time.mktime(endTime.timetuple()))
        sTime = round(time.mktime(startTime.timetuple()))
        query_api = self.influx_client.query_api()
        query = 'from(bucket: "printer_data")\
                    |> range(start:' + str(sTime) +', stop: '+ str(eTime) + ')\
                    |> filter(fn: (r) => r["_measurement"] == "API_data")\
                    |> filter(fn: (r) => r["_field"] == "file")\
                    |> filter(fn: (r) => r["machine"] == "'+ machine+ '")\
                    |> filter(fn: (r) => r._value != "")\
                    |> unique()'
        table = query_api.query(query)
        output = table.to_values(columns=['_value'])
        return output[0][0]
    
    def checkComplete(self, startTime, endTime, machine):
        eTime = round(time.mktime(endTime.timetuple()))
        sTime = round(time.mktime(startTime.timetuple()))
        query_api = self.influx_client.query_api()
        query = 'from(bucket: "printer_data")\
                    |> range(start:' + str(sTime) +', stop: '+ str(eTime) + ')\
                    |> filter(fn: (r) => r["_measurement"] == "API_data")\
                    |> filter(fn: (r) => r["machine"] == "'+ machine+ '")\
                    |> filter(fn: (r) => r["_field"] == "progress")\
                    |> max()'
        table = query_api.query(query)
        output = table.to_values(columns=['_value'])
        if output != []:
            if output[0][0] > 85:
                return True
            else:
                return False
        else:
            return ""
            
    def jobLengthAndTimeFile(self, machines, numberDaysBack):
        data = []
        for machine in machines:
            query_api = self.influx_client.query_api()
            query = 'from(bucket: "printer_data")\
                    |> range(start: -' + str(numberDaysBack) + 'd)\
                    |> filter(fn: (r) => r["_measurement"] == "API_data")\
                    |> filter(fn: (r) => r["_field"] == "file")\
                    |> filter(fn: (r) => r["machine"] == "'+ machine+ '")\
                    |> filter(fn: (r) => r._value != "")\
                    |> unique()'
            
            table = query_api.query(query)
            output = table.to_values(columns=['_value'])
            # output is a list of files printed on that printer
            fileData = []
            for files in output:
                query_api = self.influx_client.query_api()
                query = 'from(bucket: "tracking_data")\
                        |> filter(fn: (r) => r["_measurement"] == "tracking")\
                        |> filter(fn: (r) => r["_field"] == "file")\
                        |> filter(fn: (r) => r["machine"] == "'+ machine + '")\
                        |> filter(fn: (r) => r._value != "'+ files + '")\
                        |> last()'
                table = query_api.query(query)
                output = table.to_values(columns=['_time'])
                if len(output) == 1:
                    timeEnd = output[0]
                elif len(output) > 1:
                    timeEnd = output
                else:
                    timeEnd = "unkown"

                query_api = self.influx_client.query_api()
                query = 'from(bucket: "tracking_data")\
                        |> filter(fn: (r) => r["_measurement"] == "tracking")\
                        |> filter(fn: (r) => r["_field"] == "file")\
                        |> filter(fn: (r) => r["machine"] == "'+ machine + '")\
                        |> filter(fn: (r) => r._value != "'+ files + '")\
                        |> first()'
                table = query_api.query(query)
                output = table.to_values(columns=['_time'])
                if len(output) == 1:
                    timeStart = output[0]
                elif len(output) > 1:
                    timeStart = output
                else:
                    timeStart = "unkown"

                fileData = [machine, files, timeStart, timeEnd]
                data.append(fileData)

        return data

    def findTimeInUse(self, machine, numberDaysBack):
        query_api = self.influx_client.query_api()
        query = 'from(bucket: "power_monitoring")\
                |> range(start: -' + str(numberDaysBack) + 'd)\
                |> filter(fn: (r) => r["_measurement"] == "equipment_power_usage")\
                |> filter(fn: (r) => r["_field"] == "machineState")\
                |> filter(fn: (r) => r["machine"] == "' + machine +'")\
                |> aggregateWindow(every: 10, fn: mode, createEmpty: false)'
                
        table = query_api.query(query)
        output = table.to_values(columns=['_time', '_value'])
        data = []
        oldState = 0
        timeOld = output[0][0]
        for ind in range(len(output)):
            newState = output[ind][1]
            if newState != oldState :
                timeS= output[ind][0]
                if oldState == 1:
                    data.append([oldState, timeOld, timeS])
                timeOld = output[ind][0]
                oldState = newState
        return data
    
    def findTimeLastData(self, dataName, bucketName, numberDaysBack):

        query_api = self.influx_client.query_api()
        query = 'from(bucket: '+ bucketName +')\
                |> range(start: -' + str(numberDaysBack) + 'd)\
                |> filter(fn: (r) => r["_measurement"] == '+ dataName +')\
                |> last()\
                |> keep(columns: ["_time"])'
        table = query_api.query(query)
        output = table.to_values(columns=['_time'])
        timeOld = output[0][0]

        return timeOld
        
                