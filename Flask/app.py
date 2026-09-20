from flask import Flask, Response, jsonify, request
import secrets
from accelerators import TelemetryCache
from nvtop_stream import stream_nvtop

import psutil
import json
import platform
import subprocess
import os 
import shutil
import threading
import time
import re
from devices import discover_nvme, discover_npus, discover_usb


##settings 

dir_path = os.path.dirname(os.path.realpath(__file__))
print(dir_path)
app = Flask(__name__, static_url_path='')



os.chdir(dir_path)

PERMISSION_INTERFACES = {
    'network': 'Allow network access for the dashboard service.',
    'network-control': 'Allow network configuration access if required by device tools.',
    'network-bind': 'Allow the service to listen on port 12121.',
    'network-observe': 'Read network device and traffic information.',
    'gsettings': 'Read desktop settings used by the launcher environment.',
    'camera': 'Read camera devices for v4l2 discovery.',
    'hardware-observe': 'Read hardware and accelerator information.',
    'opengl': 'Read GPU devices for the embedded nvtop monitor.',
    'system-observe': 'Read system and process information.',
    'process-control': 'Allow the process Stop action.',
    'raw-usb': 'Read USB device information.',
    'mount-observe': 'Read mounted storage information.',
    'udisks2': 'Access storage information through UDisks.',
}
MONITOR_COMMANDS = ['lsblk', 'ifconfig', 'lsusb', 'lspci', 'v4l2-ctl']
ACCELERATOR_CACHE = TelemetryCache()
PROCESS_CACHE_LOCK = threading.Lock()
PROCESS_CACHE = {'ramProcesses': [], 'cpuProcesses': []}

########## serving functions

@app.route('/')
def index():
    
    return app.send_static_file('index.html')

@app.route('/systemdevices')
def systemdevices():
    
    return app.send_static_file('systemdevices.html')

@app.route('/accelerators')
def accelerators():
    return app.send_static_file('accelerators.html')

@app.route('/nvtop/stream')
def nvtop_stream():
    if request.headers.get('Sec-Fetch-Site') == 'cross-site':
        return jsonify(error='Open the terminal from this dashboard.'), 403
    columns = request.args.get('columns', default=120, type=int)
    columns = max(80, min(160, columns))
    return Response(stream_nvtop(columns=columns), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no'})

@app.route('/acceleratordata')
def accelerator_data():
    response = jsonify(ACCELERATOR_CACHE.get())
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/permissions')
def permissions():
    return Response(json.dumps(getPermissionReport()), mimetype='json')

@app.route('/staticdata',methods=['GET', 'POST'])
def stream():              

    return Response(getSystemInfo(), mimetype='json')

@app.route('/usagedata',methods=['GET', 'POST'])
def data():              

    return Response(getSystemUsageInfo(), mimetype='json')

@app.route('/processes',methods=['GET', 'POST'])
def dataproc():              

    return Response(getProcesses(), mimetype='json')  

@app.route('/processes/<int:pid>/terminate', methods=['POST'])
def terminate_process(pid):
    token = os.environ.get('MONITOR_CONTROL_TOKEN', '')
    if not token:
        return jsonify(ok=False, error='Process control is disabled. Configure MONITOR_CONTROL_TOKEN to enable it.'), 403
    if not secrets.compare_digest(request.headers.get('Authorization', '').encode('utf-8'), ('Bearer ' + token).encode('utf-8')):
        return jsonify(ok=False, error='A valid process-control token is required.'), 403
    if pid <= 1 or pid == os.getpid():
        return Response(json.dumps({'ok': False, 'error': 'This process cannot be stopped from the dashboard.'}), status=400, mimetype='json')
    try:
        process = psutil.Process(pid)
        process.terminate()
        return Response(json.dumps({'ok': True, 'pid': pid}), mimetype='json')
    except psutil.NoSuchProcess:
        return Response(json.dumps({'ok': False, 'error': 'Process no longer exists.'}), status=404, mimetype='json')
    except (psutil.AccessDenied, PermissionError):
        return Response(json.dumps({'ok': False, 'error': 'Permission denied.'}), status=403, mimetype='json')
    except psutil.Error as error:
        return Response(json.dumps({'ok': False, 'error': str(error)}), status=400, mimetype='json')

def getProcesses():
    with PROCESS_CACHE_LOCK:
        return json.dumps(PROCESS_CACHE)

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
        info['perCpu']=psutil.cpu_percent(percpu=True)
        info['RAM']=psutil.virtual_memory().percent
        info['network']=getNetworkUsage()
        info['disk']=getDiskUsage()
        info['temp']=getTemperauresString()   

        

        return json.dumps(info)
        
    except Exception as e:
        print(e)

def getNetworkUsage():
    counters = psutil.net_io_counters()
    return {'sent': counters.bytes_sent, 'received': counters.bytes_recv, 'interfaces': getNetworkInterfaces()}

def getNetworkInterfaces():
    try:
        result = subprocess.run(['ifconfig', '-a'], capture_output=True, text=True, timeout=3, check=True)
    except (OSError, subprocess.SubprocessError):
        return []
    interfaces = []
    current = None
    for line in result.stdout.splitlines():
        header = re.match(r'^([A-Za-z0-9_.:-]+):?\s+flags=', line)
        if header:
            if current:
                interfaces.append(current)
            current = {'name': header.group(1), 'addresses': []}
            continue
        if current:
            address = re.search(r'\binet6?\s+([^\s]+)', line)
            if address and address.group(1) not in current['addresses']:
                current['addresses'].append(address.group(1))
    if current:
        interfaces.append(current)
    return interfaces

def getPermissionReport():
    snap_name = os.environ.get('SNAP_NAME', 'cpu-monitoring-webapp')
    interfaces = {}
    for name, purpose in PERMISSION_INTERFACES.items():
        try:
            result = subprocess.run(['snapctl', 'is-connected', name], capture_output=True, text=True, timeout=2)
            connected = result.returncode == 0
            interfaces[name] = {'connected': connected, 'purpose': purpose, 'command': f'sudo snap connect {snap_name}:{name}'}
        except (OSError, subprocess.SubprocessError):
            interfaces[name] = {'connected': None, 'purpose': purpose, 'command': f'sudo snap connect {snap_name}:{name}'}
    commands = {name: shutil.which(name) is not None for name in MONITOR_COMMANDS}
    try:
        confinement = subprocess.run(['snapctl', 'confinement'], capture_output=True, text=True, timeout=2, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        confinement = 'unknown'
    return {
        'snap': snap_name,
        'confinement': confinement,
        'interfaces': interfaces,
        'commands': commands,
        'connectAll': ' ; '.join(item['command'] for item in interfaces.values()),
        'devmode': f'sudo snap install {snap_name} --devmode',
    }

def getDiskUsage():
    try:
        result = subprocess.run(
            ['lsblk', '-J', '-b', '--tree', '-o', 'NAME,TYPE,SIZE,MODEL,MOUNTPOINT,FSTYPE,FSAVAIL,FSUSE%'],
            capture_output=True, text=True, timeout=3, check=True,
        )
        disks = []
        for device in json.loads(result.stdout).get('blockdevices', []):
            if device.get('type') != 'disk' or device.get('name', '').startswith('loop'):
                continue
            filesystems = []
            collect_filesystems(device, filesystems)
            disks.append({
                'name': device.get('name'),
                'model': (device.get('model') or '').strip(),
                'size': device.get('size'),
                'mountpoint': device.get('mountpoint'),
                'filesystem': device.get('fstype'),
                'filesystems': filesystems,
            })
        mounted = getMountedFilesystems()
        for filesystem in mounted:
            matching = next((disk for disk in disks if re.match(r'^' + re.escape(disk['name']) + r'(p?\d+)$', filesystem['name'])), None)
            if matching:
                if not any(item['name'] == filesystem['name'] for item in matching['filesystems']):
                    matching['filesystems'].append(filesystem)
            elif not filesystem['name'].startswith('loop'):
                disks.append({'name': filesystem['name'], 'model': '', 'size': filesystem['size'], 'mountpoint': filesystem['mountpoint'], 'filesystem': filesystem['filesystem'], 'filesystems': [filesystem]})
        return {'disks': disks}
    except (OSError, subprocess.SubprocessError, ValueError, TypeError, json.JSONDecodeError):
        return {'disks': []}

def collect_filesystems(device, filesystems):
    mountpoint = device.get('mountpoint')
    filesystem = {
            'name': device.get('name'),
            'mountpoint': mountpoint,
            'filesystem': device.get('fstype'),
            'available': device.get('fsavail'),
            'usedPercent': device.get('fsuse%'),
        }
    if mountpoint:
        try:
            usage = psutil.disk_usage(mountpoint)
            filesystem['available'] = usage.free
            filesystem['usedPercent'] = f'{usage.percent:.1f}%'
        except (OSError, PermissionError):
            pass
    if filesystem['filesystem'] or filesystem['mountpoint']:
        filesystems.append(filesystem)
    for child in device.get('children') or []:
        collect_filesystems(child, filesystems)

def getMountedFilesystems():
    filesystems = []
    try:
        partitions = psutil.disk_partitions(all=False)
    except (OSError, PermissionError):
        return filesystems
    for partition in partitions:
        device_name = os.path.basename(partition.device)
        if not device_name or device_name.startswith('loop'):
            continue
        try:
            usage = psutil.disk_usage(partition.mountpoint)
        except (OSError, PermissionError):
            continue
        filesystems.append({
            'name': device_name,
            'size': usage.total,
            'mountpoint': partition.mountpoint,
            'filesystem': partition.fstype,
            'available': usage.free,
            'usedPercent': f'{usage.percent:.1f}%',
        })
    return filesystems

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
           pinfo['rss'] = proc.memory_info().rss / (1024 * 1024)
           # Append dict to list
           listOfProcObjects.append(pinfo);
       except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
           pass
    # Sort process records by usage
    listOfProcObjects = sorted(listOfProcObjects, key=lambda procObj: procObj['rss'], reverse=True)

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
           pinfo['rss'] = proc.memory_info().rss / (1024 * 1024)
           # Append dict to list
           listOfProcObjects.append(pinfo);
       except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
           pass
    # Sort process records by usage
    listOfProcObjects = sorted(listOfProcObjects, key=lambda procObj: procObj['cpu_percent'], reverse=True)
    return listOfProcObjects[:numofprocesses]

def refreshProcessCache():
    processes = []
    for proc in psutil.process_iter():
        try:
            info = proc.as_dict(attrs=['pid', 'name', 'username', 'cpu_percent'])
            info['rss'] = proc.memory_info().rss / (1024 * 1024)
            processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    snapshot = {
        'ramProcesses': sorted(processes, key=lambda item: item['rss'], reverse=True)[:10],
        'cpuProcesses': sorted(processes, key=lambda item: item['cpu_percent'], reverse=True)[:10],
    }
    with PROCESS_CACHE_LOCK:
        PROCESS_CACHE.update(snapshot)

def processSampler():
    while True:
        refreshProcessCache()
        time.sleep(3)

## libraries wrappers 

def ListSubprogram(CMD):
    try:
        result = subprocess.run(CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3, check=True)
        listgross=result.stdout.decode("utf-8").replace('\t','').split('\n')
        realilist = [string for string in listgross if string != ""]
    
        return(realilist)
    except:
        pass

def ListSubprogramPlain(CMD):
    result = subprocess.run(CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3, check=True)
    listgross=result.stdout.decode("utf-8").replace('\t','').split('\n')
    realilist = [string for string in listgross if string != ""]
    print(result.stdout)


###
@app.route('/listDevices',methods=['GET', 'POST'])
def listDevices(): 
    info={}             
    try:
        info={}
        info['lsusb']=ListSubprogram(['lsusb']) or discover_usb()
        info['lspci']=ListSubprogram(['lspci'])
       # info['hci']=ListSubprogram(['hciconfig'])
        info['uname']=ListSubprogram(['uname','-a'])
        info['uptime']=ListSubprogram(['uptime'])
        info['cameras']=ListSubprogram(['v4l2-ctl','--list-devices'])
        info['nvme']=discover_nvme()
        info['npus']=discover_npus()
        return json.dumps(info)
    except:
        pass

   

@app.route('/lsusb',methods=['GET', 'POST'])
def lsusb():              

    return Response(getSystemUsageInfo(), mimetype='json')





##server start
BOOT_PERMISSION_REPORT = getPermissionReport()
print('Snap permission check:', json.dumps(BOOT_PERMISSION_REPORT))
threading.Thread(target=processSampler, name='process-sampler', daemon=True).start()

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=12121, threads=8)
