# import libraries
import os, time, json, subprocess
from flask import Flask, jsonify, request, make_response

# This needs to become a distributed storage location
externalVolume = '/opt/vcde/'

# Other variables
netWork = 'vcd_frontend'
netWorkJson = 'docker network inspect ' + netWork

# applications
applications = ["firefox", "chrome", "libreoffice", "evolution", "geary", "thunderbird", "nautilus"]
appImage = {}
for i in applications:
    appImage[i] = "rayvtoll/vcd-" + i + ":latest"
app = Flask(__name__)

# applicatie functie
def startApp(dockerRun, requestHost, requestUser, app):
    hostName = requestHost + '-' + app
    dockerCmd = str(dockerRun + ' -h ' + hostName + ' --name ' + hostName + ' -e USER=' + requestUser + " " + appImage[app])
    os.system(dockerCmd)

@app.route('/', methods=['POST'])
def create_container():
    # achterhalen welke host de aanvraag doet
    requestHost = ""
    data = json.loads(subprocess.check_output(netWorkJson, shell=True))
    for i in data[0]['Containers']:
        if data[0]['Containers'][i]['IPv4Address'].split("/")[0] == request.environ['REMOTE_ADDR']:
            requestHost += data[0]['Containers'][i]['Name'] #.replace("-nautilus", "")
    requestUser = requestHost.split("-")[1]

    #controleren of applicatiecontainer al bestaat
    for i in data[0]['Containers']:
        if data[0]['Containers'][i]['Name'] == "vcd-" + requestUser + "-" + request.json.get('app'):
            return jsonify([{"already started" : request.json.get('app')}])
    
    # lijstje met te mounten volumes en ssh-key
    volumeMounts = ""
    volumeMounts += ' -v ' + externalVolume + requestUser + ':/home/' + requestUser
    volumeMounts += ' -v ' + externalVolume + 'Public:/home/' + requestUser + '/Public '
    volumeMounts += ' -v ' + externalVolume + requestUser + '/.ssh/id_rsa.pub:/home/' + requestUser + '/.ssh/authorized_keys:ro '
    dockerRun = "docker run --rm -d --network " + netWork + volumeMounts
    
    # applicatie loop
    for i in applications:
        if request.json.get('app') == i:
            if i == "chrome":
                dockerRun +=  ' --device /dev/dri --security-opt seccomp=/app/chrome.json '
            startApp(dockerRun, requestHost, requestUser, i)
            return jsonify([{"starting" : i}])
    
@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error' : 'Not found'}), 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
