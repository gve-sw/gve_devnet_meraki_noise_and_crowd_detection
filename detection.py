'''Copyright (c) 2023 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
           https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.'''

import csv
import time
from subprocess import Popen
from util import Util

class Detection():

    def __init__(self, ALL_CAMERAS_AND_ZONES, MOTION_ALERT_PAUSE_TIME, MOTION_ALERT_ITERATE_COUNT, TIMEOUT):
        self.SOUND_ALERT_DECIBEL_LEVEL = -55
        self.ALL_CAMERAS_AND_ZONES = ALL_CAMERAS_AND_ZONES
        self.CROWD_EVENTS_MESSAGE_RECIPIENT = ''
        self.MOTION_ALERT_PAUSE_TIME = MOTION_ALERT_PAUSE_TIME
        self.MOTION_ALERT_PEOPLE_COUNT_THRESHOLD = 1
        self.MOTION_ALERT_DWELL_TIME_MOTION = 60 
        self.MOTION_ALERT_DWELL_TIME_AUDIO = 60 
        self.MOTION_ALERT_ITERATE_COUNT = MOTION_ALERT_ITERATE_COUNT
        self.TIMEOUT = TIMEOUT


    def update_config_variables(self, SOUND_ALERT_DECIBEL_LEVEL, CROWD_EVENTS_MESSAGE_RECIPIENT, MOTION_ALERT_PEOPLE_COUNT_THRESHOLD, MOTION_ALERT_DWELL_TIME_AUDIO, MOTION_ALERT_DWELL_TIME_MOTION):
        self.reset_detection()
        self.SOUND_ALERT_DECIBEL_LEVEL = SOUND_ALERT_DECIBEL_LEVEL
        self.CROWD_EVENTS_MESSAGE_RECIPIENT = CROWD_EVENTS_MESSAGE_RECIPIENT
        self.MOTION_ALERT_PEOPLE_COUNT_THRESHOLD = MOTION_ALERT_PEOPLE_COUNT_THRESHOLD
        self.MOTION_ALERT_DWELL_TIME_AUDIO = MOTION_ALERT_DWELL_TIME_AUDIO
        self.MOTION_ALERT_DWELL_TIME_MOTION = MOTION_ALERT_DWELL_TIME_MOTION

        print('Updated: ', self.CROWD_EVENTS_MESSAGE_RECIPIENT, ' People Threshold: ', self.MOTION_ALERT_PEOPLE_COUNT_THRESHOLD, 'Dwell Time Motion:', MOTION_ALERT_DWELL_TIME_MOTION, ' Sound Threshold:',  self.SOUND_ALERT_DECIBEL_LEVEL,' Dwell Time Audio:', self.MOTION_ALERT_DWELL_TIME_AUDIO)


    def threshold_exceeded(self, detected_value, threshold_value):#
        return detected_value >= threshold_value


    def activated_monitoring(self, context):#
        return context['_MONITORING_TRIGGERED']


    def increase_monitoring_message_count(self, context):#
        context['_MONITORING_MESSAGE_COUNT'] = context['_MONITORING_MESSAGE_COUNT'] + 1


    def increase_timout_count(self,context):
        context['_TIMEOUT_COUNT'] += 1


    def reset_timeout_count(self,context):
        context['_TIMEOUT_COUNT'] = 0


    def dwell_time_passed(self,context, dwell_time):
        return context['_TIMESTAMP'] - context['_MONITORING_ACTIVATION_TIMESTAMP'] >= dwell_time


    def timeout_expired(self, context, timeout):
        return context['_TIMEOUT_COUNT'] >= timeout


    def monitored_message_count_threshold_passed(self, context, alert_iterative_count):
        return context['_MONITORING_MESSAGE_COUNT'] >= alert_iterative_count


    def reset_context_status_variables(self,context, detection_type):
        print(detection_type, " status variables resetted")
        context['_MONITORING_MESSAGE_COUNT'] = 0
        context['_MONITORING_CURRENT_VALUE'] = 0
        context['_MONITORING_TRIGGERED'] = False
        context['_TIMESTAMP'] = 0
        context['_TIMEOUT_COUNT'] = 0
        context['_MONITORING_ACTIVATION_TIMESTAMP'] = 0


    def reset_detection(self):
        for serial_number in self.ALL_CAMERAS_AND_ZONES:
            noise_context = self.ALL_CAMERAS_AND_ZONES[serial_number]['audio_analytics']
            self.reset_context_status_variables(noise_context, "NOISE")
            for zone_id in self.ALL_CAMERAS_AND_ZONES[serial_number]['zones']:
                crowd_context = self.ALL_CAMERAS_AND_ZONES[serial_number]['zones'][zone_id]
                self.reset_context_status_variables(crowd_context, "CROWD")


    def append_excel_row(self, filename, field_names, row_data):
        print("Write alert data to ", filename)
        with open(filename,'a') as csvfile:
            writer=csv.DictWriter(csvfile,fieldnames=field_names)
            writer.writerow(row_data)


    def save_noise_event(self, camera_name, camera_serial, noise_threshold, timestamp_in, timestamp_out, detected_audio_level):
        filename = 'noiseMvData.csv'
        field_names = ['Camera','Serial','Time In','Time Trigger','Detected Audio Level', 'Noise Threshold']
        row_data = {'Camera':camera_name,'Serial':camera_serial, 'Time In':timestamp_in,'Time Trigger':timestamp_out, 'Detected Audio Level':detected_audio_level  ,'Noise Threshold':noise_threshold}
        self.append_excel_row(filename, field_names, row_data)
 

    def save_crowd_event(self, camera_name, camera_serial, people_count_threshold, zone_label,timestamp_in, timestamp_out, detected_person_count):
        filename = 'crowdMvData.csv'
        field_names = ['Camera','Serial', 'Zone', 'Time In','Time Out','Detected People Count', 'Crowd Threshold']
        row_data = {'Camera':camera_name,'Serial':camera_serial,'Zone':zone_label, 'Time In':timestamp_in,'Time Out':timestamp_out, 'Detected People Count':detected_person_count, 'Crowd Threshold':people_count_threshold}
        self.append_excel_row(filename, field_names, row_data)


    def detection(self, detection_type, context, detected_value, threshold_value, dwell_time, current_timestamp, serial_number):
        
        alert_iterative_count = int(self.MOTION_ALERT_ITERATE_COUNT)
        motion_alert_pause_time = int(self.MOTION_ALERT_PAUSE_TIME)
        message_receipient = self.CROWD_EVENTS_MESSAGE_RECIPIENT
        timeout = int(self.TIMEOUT)

        if self.activated_monitoring(context):

            if self.threshold_exceeded(detected_value, threshold_value):

                self.increase_monitoring_message_count(context)
                self.reset_timeout_count(context)
                print(detection_type,'    - Current: ', detected_value, ' Threshold: ', threshold_value,' Inactive Counter: ', context['_TIMEOUT_COUNT'])
                
                context['_MONITORING_CURRENT_VALUE'] = detected_value
                context['_TIMESTAMP'] = current_timestamp

                if self.dwell_time_passed(context, dwell_time) and self.monitored_message_count_threshold_passed(context, alert_iterative_count):
                    
                    print(detection_type, "Dwell time and min number of messages reached.")
                    
                    iso_timestamp = Util.get_ISO_timestamp(current_timestamp)
                    camera_name = self.ALL_CAMERAS_AND_ZONES[serial_number]['name']
                    timestamp_in = context['_MONITORING_ACTIVATION_TIMESTAMP']
                    timestamp_trigger = context['_TIMESTAMP']

                    if detection_type == "NOISE":
                        message_text=u"At least " + str(threshold_value) + " decibel detected for more than " + str(int(dwell_time/1000)) + " seconds on camera "+ camera_name
                        self.save_noise_event(camera_name, serial_number, threshold_value, timestamp_in, timestamp_trigger, detected_value)

                    elif detection_type == "CROWD": 
                        zone_name = context['label']
                        message_text=u"At least " + str(threshold_value) + " person(s) detected for more than " + str(int(dwell_time/1000)) + " seconds on camera "+ camera_name +" for zone "+ zone_name
                        self.save_crowd_event(camera_name, serial_number, threshold_value, zone_name,  timestamp_in, timestamp_trigger, detected_value)

                    print("---ALERT STORED--- ")

                    if self.CROWD_EVENTS_MESSAGE_RECIPIENT != '':
                        Popen(f'python3 send.py "{message_text}" {message_receipient} {serial_number} {iso_timestamp}', shell=True)
                        print("---MESSAGE ALERT---: ", message_text)

                    self.reset_context_status_variables(context, detection_type)
                    time.sleep(motion_alert_pause_time)
            else:

                self.increase_timout_count(context)
                print('NO ',detection_type,'- Current: ', detected_value, ' Threshold: ', threshold_value, ' Inactive Counter: ', context['_TIMEOUT_COUNT'])

                if self.timeout_expired(context, timeout):
                    
                    print(detection_type, ' alert dismissed due to too long absense of ', detection_type)
                    self.reset_context_status_variables(context, detection_type)

        elif self.threshold_exceeded(detected_value, threshold_value):
            print('Activate ', detection_type, ' monitoring')
            context['_MONITORING_TRIGGERED'] = True
            context['_MONITORING_ACTIVATION_TIMESTAMP'] = current_timestamp


    def detect_ongoing_noise(self, topic, payload, parameters):

        serial_number = parameters[2]
        current_timestamp = payload['ts']
        detected_value = payload['audioLevel']
        threshold_value = int(self.SOUND_ALERT_DECIBEL_LEVEL)
        dwell_time = int(self.MOTION_ALERT_DWELL_TIME_AUDIO)
        detection_type = 'NOISE'
        context = self.ALL_CAMERAS_AND_ZONES[serial_number]['audio_analytics']
        
        self.detection(detection_type, context, detected_value, threshold_value, dwell_time, current_timestamp, serial_number)


    def detect_ongoing_crowd(self, topic, payload, parameters):

        serial_number = parameters[2]
        zone_id = parameters[3]
        current_timestamp = payload['ts']
        detected_value = payload['counts']['person']
        threshold_value = int(self.MOTION_ALERT_PEOPLE_COUNT_THRESHOLD)
        dwell_time = int(self.MOTION_ALERT_DWELL_TIME_MOTION)
        detection_type = 'CROWD'
        context = self.ALL_CAMERAS_AND_ZONES[serial_number]['zones'][zone_id]
        
        self.detection(detection_type, context, detected_value, threshold_value, dwell_time, current_timestamp, serial_number)

