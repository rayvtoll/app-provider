# import libraries
import os
import time
import json
import subprocess
from flask import Flask, jsonify, request, make_response

# This needs to become a distributed storage location
externalVolume = '/opt/vcde/'

# Other variables
netWork = 'vcd_frontend'
directories = ["Downloads", "Documents", "Desktop", "Music", "Pictures", "Public", "Templates", "Videos"]
netWorkJson = 'docker network inspect ' + netWork
keyDir = "/tmp/keys/"
os.system(str("mkdir -p " + keyDir))

# applications
firefox = 'rayvtoll/vcd-firefox'
chrome = 'rayvtoll/vcd-chrome'
libreoffice = 'rayvtoll/vcd-libreoffice'
app = Flask(__name__)

@app.route('/', methods=['POST'])
def create_container():
    volumeMounts = ""
    for i in directories:
        volumeMounts += ' -v ' + externalVolume + request.json.get("user") + '/' + i + ':/home/' + request.json.get("user") + '/' + i + '/ '
    dockerRun = "docker run --rm -d --network " + netWork + volumeMounts

    data = json.loads(subprocess.check_output(netWorkJson, shell=True))
    requestHost = ""
    for i in data[0]['Containers']:
        if data[0]['Containers'][i]['IPv4Address'].split("/")[0] == request.environ['REMOTE_ADDR']:
            requestHost += data[0]['Containers'][i]['Name']
    requestUser = requestHost.split("-")[1]
    key = subprocess.check_output("cat " + keyDir + requestUser + ".key", shell=True).decode('utf-8').replace("\n","")

    if request.json.get('app') == "firefox":
        hostName = requestHost + '-firefox' 
        dockerCmd =  str(dockerRun + ' -e KEY="' + key + '" -h ' + hostName + ' --name ' + hostName + ' -e USER=' + requestUser + " " + firefox)
        exitCode = str(os.system(dockerCmd))
        return jsonify([{"starting" : "firefox"}])

    if request.json.get('app') == "chrome":
        hostName = 'vcd-' + request.json.get('user') + '-chrome'
        dockerCmd =  str(dockerRun + ' --device /dev/dri --security-opt seccomp=/app/chrome.json -e KEY="' + key + '" -h ' + hostName + ' --name ' + hostName + ' -e USER=' + requestUser + " " + chrome)
        exitCode = str(os.system(dockerCmd))
        return jsonify([{"starting" : "chrome"}])

    if request.json.get('app') == "libreoffice":
        hostName = requestHost + '-libreoffice'
        dockerCmd =  str(dockerRun + ' -e KEY="' + key + '" -h ' + hostName + ' --name ' + hostName + ' -e USER=' + requestUser + " " + libreoffice)
        exitCode = str(os.system(dockerCmd))
        return jsonify([{"starting" : "LibreOffice"}])

@app.route('/key', methods=['POST'])
def store_keys():
    netWorkJson = 'docker network inspect ' + netWork
    data = json.loads(subprocess.check_output(netWorkJson, shell=True))
    requestHost = ""
    for i in data[0]['Containers']:
        if data[0]['Containers'][i]['IPv4Address'].split("/")[0] == request.environ['REMOTE_ADDR']:
            requestHost += data[0]['Containers'][i]['Name']
    requestUser = requestHost.split("-")[1]
    addSpaces = str(request.json.get('key').replace("%20", " "))
    command = str("echo '" + addSpaces + "' > /tmp/keys/" + requestUser + ".key")
    return jsonify([{"key": addSpaces,"user": requestUser,"command": command,"exitcode": os.system(command)}])

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error' : 'Not found'}), 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
