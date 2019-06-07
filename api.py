# This needs to become a distributed storage location
externalVolume = '/opt/vcde/'

# Other variables
netWork = 'vcd_frontend'

# applications
browser = 'rayvtoll/vcd-firefox'
libreoffice = 'rayvtoll/vcd-libreoffice'

# import libraries
import os
import time
import subprocess
from flask import Flask, jsonify, request, make_response

# declaring additional variables
app = Flask(__name__)
keyDir = "/tmp/keys/"
os.system(str("mkdir -p " + keyDir))

@app.route('/', methods=['GET'])
def list_containers():
    dockerPs = str('docker ps --format "{{ json .}}" | jq --slurp .')
    return subprocess.check_output(dockerPs, shell=True)

@app.route('/', methods=['POST'])
def create_container():
    dockerPs = 'docker ps --filter name=vcd-' + request.json.get('user') + '-* --format "{{ json .}}" | jq --slurp .'
    print(dockerPs)
    if request.json.get('app') == "browser":
        openApps = str(subprocess.check_output(dockerPs, shell=True))
        print(openApps)
        if "browser" in openApps:
            os.system("docker container rm -f vcd-" + request.json.get('user') + "-browser")
        key = subprocess.check_output("cat " + keyDir + request.json.get('user') + ".key", shell=True).decode('utf-8').replace("\n","")
        dockerRun =  str('docker run --rm -e KEY="' + key + '" --name vcd-' + request.json.get('user') + '-browser -d --network ' + netWork + ' -e USER=' + request.json.get("user") + ' -v ' + externalVolume + request.json.get("user") + '/Downloads:/home/' + request.json.get("user") + '/Downloads/ ' + browser)
        exitCode = str(os.system(dockerRun))
        return jsonify([{"starting" : "browser"}])

    if request.json.get('app') == "libreoffice":
        openApps = str(subprocess.check_output(dockerPs, shell=True))
        print(openApps)
        if "libreoffice" in openApps:
            os.system("docker container rm -f vcd-" + request.json.get('user') + "-libreoffice")
        key = subprocess.check_output("cat " + keyDir + request.json.get('user') + ".key", shell=True).decode('utf-8').replace("\n","")
        dockerRun =  str('docker run --rm -e KEY="' + key + '" --name vcd-' + request.json.get('user') + '-libreoffice -d --network ' + netWork + ' -e USER=' + request.json.get("user") + ' -v ' + externalVolume + request.json.get("user") + '/Documents:/home/' + request.json.get("user") + '/Documents/ ' + libreoffice)
        exitCode = str(os.system(dockerRun))
        return jsonify([{"starting" : "LibreOffice"}])

@app.route('/key', methods=['POST'])
def store_keys():
    addSpaces = str(request.json.get('key').replace("%20", " "))
    command = str("echo '" + addSpaces + "' > /tmp/keys/" + request.json.get('user') + ".key")
    return jsonify([{"key": request.json.get('key'),"addSpaces": addSpaces,"user": request.json.get('user'),"command": command,"exitcode": os.system(command)}])

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error' : 'Not found'}), 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
