"""
Copyright (c) 2023 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

from flask import Flask, render_template, request, json

import os
import paho.mqtt.client as mqtt

from config import COLLECT_CAMERAS_MVSENSE_CAPABLE, MQTT_SERVER,MQTT_PORT,MOTION_ALERT_ITERATE_COUNT,MOTION_ALERT_PAUSE_TIME,TIMEOUT
from meraki_api import *
from util import Util
from detection import Detection


app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    global mqtt_topics

    print("MQTT connected with result code " + str(rc))
    print("MQTT topics: ", mqtt_topics)

    for topic in mqtt_topics:
        client.subscribe(topic)


def on_message(client, userdata, msg):

    global detectionHandler

    payload = json.loads(msg.payload.decode("utf-8"))
    parameters = msg.topic.split("/")
    message_type = parameters[3]

    if message_type == 'audio_analytics':
        detectionHandler.detect_ongoing_noise(msg.topic, payload, parameters)
    elif message_type != '0' and message_type != 'raw_detections' and message_type != 'light' and message_type != 'audio_detections':
        detectionHandler.detect_ongoing_crowd(msg.topic, payload, parameters)


@app.route('/',methods=['GET','POST'])
def index():

    global detectionHandler, settings

    if request.method == 'POST':
        input_receipient = request.form.get("input-receipient")
        input_person_count = int(request.form.get("input-person-count"))
        input_crowd_dwell_time = int(request.form.get("input-crowd-dwell-time"))
        input_noise_threshold = int(request.form.get("input-noise-threshold"))
        input_noise_dwell_time = int(request.form.get("input-noise-dwell-time"))
        
        settings = {'input_receipient': input_receipient, 'input_person_count':input_person_count, 'input_crowd_dwell_time':input_crowd_dwell_time, 'input_noise_threshold':input_noise_threshold, 'input_noise_dwell_time':input_noise_dwell_time}
        detectionHandler.update_config_variables(input_noise_threshold, input_receipient, input_person_count, input_noise_dwell_time*1000, input_crowd_dwell_time*1000)
        detection_stop()

    return render_template("settings.html", settings=settings)
    

@app.route('/start_mvsense')
def startMVSense():
    global client
    try:
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(MQTT_SERVER, MQTT_PORT, 60)
        client.loop_start()
    except Exception as ex:
        print("[MQTT]failed to connect or receive msg from mqtt, due to: \n {0}".format(ex))
    return 'ok'


@app.route('/stop_mvsense')
def stopMVSense():
    detection_stop()
    return 'ok'


def detection_stop():
    global client, detection
    try:
        client.loop_stop()
        detectionHandler.reset_detection()
    except Exception as ex:
        print("[MQTT]failed to stop, due to: \n {0}".format(ex))    


@app.route('/history',methods=['GET','POST'])
def history():
    motion_data = Util.csv_to_json("crowdMvData.csv", "CROWD")
    noise_data = Util.csv_to_json("noiseMvData.csv", "NOISE")
    return render_template("history.html",motion_data=motion_data, noise_data=noise_data)


@app.route('/getsnapshot',methods=['GET'])
def getsnapshot():
    serial = request.args['serial']
    timestamp = float(request.args['timestamp'])
    ISO_timestamp=Util.get_ISO_timestamp(timestamp)
    screenshot_URL_data = get_camera_screenshot(serial, ISO_timestamp)

    if screenshot_URL_data == 'link error':
        return "There is no snapshot!"
    else:
        screenshot_URL = json.loads(screenshot_URL_data)["url"]
        wait_time = 7000
        wait_time_in_seconds = wait_time / 1000
        return render_template("redirect.html", seconds=wait_time_in_seconds, screenshot_URL=screenshot_URL, wait_time=wait_time)


def create_camera_and_status_dict():

    mqtt_topics = [] 
    camera_data_and_status = {}

    initial_status={'_MONITORING_TRIGGERED': False,
                    '_MONITORING_MESSAGE_COUNT':0,
                    '_MONITORING_CURRENT_VALUE':0,
                    '_TIMESTAMP':0,
                    '_TIMEOUT_COUNT':0,
                    '_MONITORING_ACTIVATION_TIMESTAMP':0}

    devices_data = get_devices()

    if devices_data != 'link error':
        
        for device in json.loads(devices_data):
            the_model = device["model"]

            if the_model[:4] not in COLLECT_CAMERAS_MVSENSE_CAPABLE:
                continue

            #Base structure
            if "name" in device.keys():
                device_name = device["name"]
            else:
                device_name = "Camera "+ device["serial"]

            camera_data_and_status[device["serial"]]={'name': device_name,
                                                        'zones': {},
                                                        'audio_analytics': {}}

            #Zone/Motion structure
            zonesdetaildata = get_camera_zones(device["serial"])

            if zonesdetaildata == 'link error':
                continue

            MVZonesDetails = json.loads(zonesdetaildata)
            theZoneDetailsDict={}

            for zoneDetails in  MVZonesDetails:
                if zoneDetails["zoneId"]!='0':
                    
                    theZoneDetailsDict[zoneDetails["zoneId"]]={'label':zoneDetails["label"]}
                    theZoneDetailsDict[zoneDetails["zoneId"]].update(initial_status)                                         
                    mqtt_topics.append("/merakimv/" + device["serial"] + "/" + zoneDetails["zoneId"])
            
            camera_data_and_status[device["serial"]]['zones'] = theZoneDetailsDict

            #Audio structure           
            mqtt_topics.append("/merakimv/" + device["serial"] + "/audio_analytics")
            camera_data_and_status[device["serial"]]['audio_analytics'] = initial_status

    return camera_data_and_status, mqtt_topics


if __name__ == "__main__":
    
    settings = {'input_receipient': '', 'input_person_count':'', 'input_crowd_dwell_time':'', 'input_noise_threshold':'', 'input_noise_dwell_time':''}
    camera_data_and_status, mqtt_topics = create_camera_and_status_dict()
    detectionHandler = Detection(camera_data_and_status, MOTION_ALERT_PAUSE_TIME, MOTION_ALERT_ITERATE_COUNT, TIMEOUT)

    app.run(host='0.0.0.0', port=5001, debug=True)
