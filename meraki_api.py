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

import requests
from config import NETWORK_ID, MERAKI_API_KEY


def http_request(method, url, headers, payload):
    
    resp = requests.request(method, url, headers=headers, data=payload)

    if int(resp.status_code / 100) == 2:
        return(resp.text)
    return('link error')
 

def get_camera_zones(serial_number):

    method = "GET"
    url = "https://api.meraki.com/api/v0/devices/"+serial_number+"/camera/analytics/zones"
    headers = {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }

    return http_request(method, url, headers, "")


def get_camera_screenshot(serial_number,timestamp=None):

    method = "POST"
    url = "https://api.meraki.com/api/v0/networks/"+NETWORK_ID+"/cameras/"+serial_number+"/snapshot"
    headers = {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "cache-control": "no-cache",
    }
    
    if timestamp:
        url = url +"?timestamp=" + timestamp
        
    return http_request(method, url, headers, "")


def get_devices():

    method = "GET"
    url = "https://api.meraki.com/api/v0/networks/"+NETWORK_ID+"/devices/"
    headers = {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }
    return http_request(method, url, headers, "")



