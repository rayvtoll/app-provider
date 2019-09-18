# import libraries
import os, time, json, subprocess, logging
from flask import Flask, jsonify, request, make_response

# This needs to become a distributed storage location
externalVolume = '/opt/vcde/'

# Other variables
netWork = 'vcd_frontend'
netWorkJson = 'docker network inspect ' + netWork

# applications
applications = ["gimp", "firefox", "chrome", "libreoffice", "evolution", "geary", "thunderbird", "nautilus"]
appImage = {}
for i in applications:
    appImage[i] = "rayvtoll/vcd-" + i + ":latest"
app = Flask(__name__)

# van source IP naar hostnaam
def request_host(request, data):
    for i in data:
        if data[i]['IPv4Address'].split("/")[0] == request:
            return data[i]['Name'] #.replace("-nautilus", "")

# API
@app.route('/', methods=['POST'])
def create_container():
    requestedApp = request.json.get('app')
    if not requestedApp in applications:
        return jsonify([{"requested app" : "not available"}])

    # achterhalen welke host de aanvraag doet
    data = json.loads(subprocess.check_output(netWorkJson, shell=True))[0]['Containers']
    requestHost = request_host(request.environ['REMOTE_ADDR'], data)
    requestUser = requestHost.split("-")[1]
    hostName = requestHost + "-" + requestedApp

    #controleren of applicatiecontainer al bestaat
    if hostName in str(data):
        return jsonify([{"already started" : requestedApp}])

    # lijstje met te mounten volumes en ssh-key
    volumeMounts = ""
    volumeMounts += ' -v ' + externalVolume + requestUser + ':/home/' + requestUser
    volumeMounts += ' -v ' + externalVolume + 'Public:/home/' + requestUser + '/Public '
    volumeMounts += ' -v ' + externalVolume + requestUser + '/.ssh/id_rsa.pub:/home/' + requestUser + '/.ssh/authorized_keys:ro '
    dockerRun = "docker run --rm -d --network " + netWork + volumeMounts
    if requestedApp == "chrome":
        dockerRun +=  ' --device /dev/dri --security-opt seccomp=/app/chrome.json '
    if requestedApp == "chrome" or requestedApp == "firefox" or requestedApp == "gimp":
        dockerRun += ' --shm-size=2g '
    dockerCmd = str(dockerRun + ' -h ' + hostName + ' --name ' + hostName + ' -e USER=' + requestUser + " " + appImage[requestedApp])
    os.system(dockerCmd)
    return jsonify([{"starting" : requestedApp}])
    
@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error' : 'Not found'}), 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
