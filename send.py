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

from config import BOT_ACCESS_TOKEN
from meraki_api import *
import sys
from requests_toolbelt.multipart.encoder import MultipartEncoder

def generate_latest_snapshot(serial, session=None):
    headers = {'X-Cisco-Meraki-API-Key': MERAKI_API_KEY, 'Content-Type': 'application/json'}
    url = f'https://api.meraki.com/api/v0/networks/{NETWORK_ID}/cameras/{serial}/snapshot'

    if not session:
        session = requests.Session()

    response = session.post(url,headers=headers)

    if response.ok:
        snapshot_link = response.json()['url']
        return snapshot_link
    else:
        return None


def download_file_from_url(session, file_name, file_url):

    for attempt in range(30):
        response = session.get(file_url, stream=True)
        if response.ok:
            print(f'Retried {attempt} times until successfully retrieved {file_url}')
            temp_file = f'/tmp/{file_name}.jpg'
            with open(temp_file, 'wb') as f:
                for chunk in response:
                    f.write(chunk)
            return temp_file

    print(f'Unsuccessful in 30 attempts retrieving {file_url}')
    return None


def send_snapshot_file(session, headers, payload, message, file_path, file_type='image/png'):

    if 'roomId' in payload:
        payload = {'roomId': payload['roomId']}

    payload['markdown'] = message
    payload['files'] = (file_path, open(file_path, 'rb'), file_type)
    data = MultipartEncoder(payload)

    session.post('https://api.ciscospark.com/v1/messages', data=data,
                      headers={'Authorization': headers['authorization'],
                               'Content-Type': data.content_type})


def post_alert_message(session, headers, payload, message):

    payload['markdown'] = message
    session.post('https://api.ciscospark.com/v1/messages/',
                 headers=headers,
                 json=payload)


if __name__ == '__main__':

    theText = sys.argv[1]
    destination_email = sys.argv[2]
    serial_number = sys.argv[3]
    timestamp = sys.argv[4]

    session = requests.Session()

    headers = {
        'content-type': 'application/json; charset=utf-8',
        'authorization': f'Bearer {BOT_ACCESS_TOKEN}'
    }
    payload = {
        'toPersonEmail': destination_email,
    }

    print("About to generate snapshot with serial ",serial_number,' and session ',session)
    the_screenshot_URL=generate_latest_snapshot(serial_number, session)

    if the_screenshot_URL:
        temp_file = download_file_from_url(session, serial_number, the_screenshot_URL)
        if temp_file:
            send_snapshot_file(session, headers, payload, theText, temp_file, file_type='image/jpg')
        else:
            theText += ' (snapshot unsuccessfully retrieved)'
            post_alert_message(session, headers, payload, theText)
    else:
        theText += ' (snapshot unsuccessfully requested)'
        post_alert_message(session, headers, payload, theText)