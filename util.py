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

from datetime import datetime
import csv

class Util():

    @staticmethod
    def get_ISO_timestamp(timestamp):
        try:
            datetime_timestamp = datetime.utcfromtimestamp(timestamp/ 1e3)
            iso_timestamp = datetime_timestamp.isoformat() + "Z"
            return iso_timestamp
        except Exception as ex:
            print("Timestamp calc failed due to: \n {0}".format(ex))

    @staticmethod
    def seconds_to_human_readable_time(seconds):
        return datetime.fromtimestamp(float(seconds)/1000).strftime('%m-%d,%H:%M:%S')

    @staticmethod
    def csv_to_json(filename, detection_type):
        json_data = []
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                link = "/getsnapshot?serial="+row['Serial']+"&timestamp="+row['Time In']
                if detection_type == "NOISE":
                    json_data.append({'Camera':row['Camera'],'Serial':row['Serial'],'detected_audio_level':row['Detected Audio Level'],'noise_threshold':row['Noise Threshold'], 'timeIn':Util.seconds_to_human_readable_time(row['Time In']),'time_trigger':Util.seconds_to_human_readable_time(row['Time Trigger']),'link':link})
                elif detection_type == "CROWD":
                    json_data.append({'Camera':row['Camera'],'Serial':row['Serial'],'Zone':row['Zone'],'timeIn':Util.seconds_to_human_readable_time(row['Time In']), 'timeOut':Util.seconds_to_human_readable_time(row['Time Out']), 'count':row['Detected People Count'], 'threshold':row['Crowd Threshold'], 'link':link})
        return json_data