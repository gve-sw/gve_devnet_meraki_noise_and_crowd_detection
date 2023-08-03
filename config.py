# this config file contains multiple variables utilized throughout the functionality of this code

MERAKI_API_KEY = ""
NETWORK_ID = ""

# ------------ Variables for Webex Teams bot notification -------------------------
BOT_ACCESS_TOKEN = ""

# ------------Variables utilized in mvSense code-----------------------------------
MQTT_SERVER = "test.mosquitto.org"

MQTT_PORT = 1883

# Array of valid cameras with MVSense API
COLLECT_CAMERAS_MVSENSE_CAPABLE=["MV12", "MV22", "MV72"]

# message count to trigger an action
MOTION_ALERT_ITERATE_COUNT = 10
# pause time after alert finished triggering
MOTION_ALERT_PAUSE_TIME = 5
# number of messages until action time out
TIMEOUT = 20


