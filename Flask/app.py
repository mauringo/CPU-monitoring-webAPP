from flask import Flask, redirect, render_template, request, session, url_for, Response

import psutil
import json
import platform
import time
import subprocess
import os 
import sys



# stdout is saved


dir_path = os.path.dirname(os.path.realpath(__file__))
print(dir_path+"/uploads")
app = Flask(__name__, static_url_path='')



os.chdir(dir_path)


# Uploads

@app.route('/')
def index():
    
    return render_template('index.html')


@app.route('/staticdata',methods=['GET', 'POST'])
def stream():              

    return Response(getSystemInfo(), mimetype='json')

@app.route('/usagedata',methods=['GET', 'POST'])
def data():              

    return Response(getSystemUsageInfo(), mimetype='json')

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
        lista = []
        oldentries=[]
        b=""
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                info['temp']="none"
                return json.dumps(info)
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
            info['temp']=b
            #print(b) 
            #print (lista)             
            return json.dumps(info)
        except Exception as e:
            info['temp']="none"
            return json.dumps(info)
    except Exception as e:
        print(e)




if __name__ == '__main__':
   app.run(host='0.0.0.0',debug = False, port=12121)
