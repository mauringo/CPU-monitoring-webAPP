import psutil
def getListOfProcessSortedByMemory():
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
    return listOfProcObjects

def getListOfProcessSortedByCPU():
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
    listOfProcObjects = sorted(listOfProcObjects, key=lambda procObj: procObj['cpu_percent'], reverse=True)
    return listOfProcObjects

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

def main():
   print(getTemperauresString())
    
if __name__ == '__main__':
   main()
