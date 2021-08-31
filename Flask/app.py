from flask import Flask, redirect, render_template, request, session, url_for, Response

import psutil
import json
import platform
import time
import subprocess
import os 
import sys


##settings 

dir_path = os.path.dirname(os.path.realpath(__file__))
print(dir_path)
app = Flask(__name__, static_url_path='')



os.chdir(dir_path)


########## serving functions

@app.route('/')
def index():
    
    return render_template('index.html')


@app.route('/staticdata',methods=['GET', 'POST'])
def stream():              

    return Response(getSystemInfo(), mimetype='json')

@app.route('/usagedata',methods=['GET', 'POST'])
def data():              

    return Response(getSystemUsageInfo(), mimetype='json')

@app.route('/processes',methods=['GET', 'POST'])
def dataproc():              

    return Response(getProcesses(), mimetype='json')  

def getProcesses():
    try:
        info={}
        info['ramProcesses']=getListOfProcessSortedByMemory(10)
        info['cpuProcesses']=getListOfProcessSortedByCPU(10)
       

        return json.dumps(info)
    except Exception as e:
        print(e)

## functions used to pack the json 
def getSystemInfo():
    try:
        info={}
        info['platform']=platform.system()
        info['kernel']=platform.release()
        info['platform-version']=platform.version()
        info['architecture']=platform.machine()
        info['phcpu']=psutil.cpu_count(logical=False)
        info['vrcpu']=psutil.cpu_count()
        info['processor']=platform.processor()
        info['ram']=str(round(psutil.virtual_memory().total / (1024.0 **3)))+" GB"
        

        return json.dumps(info)
    except Exception as e:
        print(e)

def getSystemUsageInfo():
    try:
        info={}
        info['CPU']=psutil.cpu_percent()
        info['RAM']=psutil.virtual_memory().percent
        info['temp']=getTemperauresString()   

        

        return json.dumps(info)
        
    except Exception as e:
        print(e)

########## Ps util functions


def getTemperauresString():
    lista = []
    oldentries=[]
    b=""
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
           b="none"
        for name, entries in temps.items():
            
            
            for entry in entries:
                if not entry in oldentries:
                    oldentries.append(entry)
                    b=b+"device: " + str( entry.label or name) + " Current Temperature: " + str(entry.current)+"°C" + " High Value: " + str(entry.high)+"°C" + " Critical Value: " +str(entry.critical)+ "°C" +  "\n"
            
                    a=[]
                    a.append(entry.label or name)
                    a.append(entry.current)
                    a.append(entry.high)
                    a.append(entry.critical)
                    if a not in lista:
                        lista.append(a)
    except Exception as e:
            b="none"
            
    return lista

def getListOfProcessSortedByMemory(numofprocesses):
    '''
    Get list of running process sorted by Memory Usage
    '''
    listOfProcObjects = []
    # Iterate over the list
    for proc in psutil.process_iter():
       try:
           # Fetch process details as dict
           pinfo = proc.as_dict(attrs=['pid', 'name', 'username', 'cpu_percent'])
           pinfo['vms'] = proc.memory_info().vms / (1024 * 1024)
           # Append dict to list
           listOfProcObjects.append(pinfo);
       except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
           pass
    # Sort list of dict by key vms i.e. memory usage
    listOfProcObjects = sorted(listOfProcObjects, key=lambda procObj: procObj['vms'], reverse=True)

    return listOfProcObjects[:numofprocesses]

def getListOfProcessSortedByCPU(numofprocesses):
    '''
    Get list of running process sorted by CPU Usage
    '''
    listOfProcObjects = []
    # Iterate over the list
    for proc in psutil.process_iter():
       try:
           # Fetch process details as dict
           
           pinfo = proc.as_dict(attrs=['pid', 'name', 'username', 'cpu_percent'])
           pinfo['vms'] = proc.memory_info().vms / (1024 * 1024)
           # Append dict to list
           listOfProcObjects.append(pinfo);
       except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
           pass
    # Sort list of dict by key vms i.e. memory usage
    listOfProcObjects = sorted(listOfProcObjects, key=lambda procObj: procObj['cpu_percent'], reverse=True)
    return listOfProcObjects[:numofprocesses]

##server start

if __name__ == '__main__':
   app.run(host='0.0.0.0',debug = False, port=12128)
