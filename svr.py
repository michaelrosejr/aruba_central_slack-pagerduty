from flask import Flask, request, abort
import requests
import json

app = Flask(__name__)

ROUTING_KEY = "***NEED TO SETUP***"

SLACK_URL = "***NEED TO SETUP***"

#
# Test Central Alert Calls (JSON)
#

# central_data = {
#     "alert_type": "GATEWAY_DISCONNECTED",
#     "description": "Gateway with serial CP0018220, MAC address 20:4c:03:03:ac:40 and IP address 10.0.3.129 reconnected",
#     "timestamp": 1553720636,
#     "webhook": "102e988f-f37b-4729-9993-acf96e8543b6",
#     "setting_id": "2001175-303",
#     "state": "Open",
#     "nid": 303,
#     "details": {
#         "params": ["CP0018220", "20:4c:03:03:ac:40", "10.0.3.129", "mroseAC:40"],
#         "conn_status": "reconnected",
#         "time": "2019-03-27 20:47:13 UTC",
#     },
#     "operation": "update",
#     "device_id": "CP0018220",
#     "id": "AWnA6CYJWQhAWjnY_-ck",
#     "severity": "Major",
# }
ap_close = {'alert_type': 'AP disconnected', 'description': 'AP with Name AP1-1FL-Office and MAC address 90:4c:81:c1:55:3f reconnected', 'timestamp': 1553753129, 'webhook': '78e44ae9-0446-4a12-b4ee-bla32sdbla', 'setting_id': '5001338-4', 'state': 'Close', 'nid': 4, 'details': {'params': ['AP1-1FL-Office', '90:4c:81:c1:55:3f'], 'conn_status': 'reconnected', 'time': '2019-03-27 23:40:47 UTC'}, 'operation': 'update', 'device_id': 'GGGG33331', 'id': 'AWnBhw2_J0p1EKfgpYGM', 'severity': 'Critical'}
ap_down = {"alert_type": "AP disconnected", "description": "AP with Name AP1-1FL-Office and MAC address 90:4c:81:c1:55:3f disconnected, Group:917, Site:SammamishOffice", "timestamp": 1553760927, "webhook": "78e44ae9-0446-4a12-b4ee-bla32sdbla", "setting_id": "5001338-4", "state": "Open", "nid": 4, "details": {"_rule_number": "0", "group": "2", "labels": "6", "conn_status": "disconnected", "params": ["AP1-1FL-Office", "90:4c:81:c1:55:3f"], "time": "2019-03-28 08:15:27 UTC"}, "operation": "create", "device_id": "GGGG33331", "id": "AWnDXj-PwwyPCYMZt3eK", "severity": "Critical"}
ap_up = {"alert_type": "AP disconnected", "description": "AP with Name AP1-1FL-Office and MAC address 90:4c:81:c1:55:3f reconnected", "timestamp": 1553756167, "webhook": "78e44ae9-0446-4a12-b4ee-bla32sdbla", "setting_id": "5001338-4", "state": "Close", "nid": 4, "details": {"params": ["AP1-1FL-Office", "90:4c:81:c1:62:82"], "conn_status": "reconnected", "time": "2019-03-28 06:41:53 UTC"}, "operation": "update", "device_id": "GGGG33331", "id": "AWnDCJQcYnT0waZXsRQa", "severity": "Critical"}
#
# End Test Calls
#

def pd_event_action(state):
    # Converts Central Alert state to PagerDuty event action
    # Open = trigger
    # Close = resolve
    if state == "Open":
        event_action = "trigger"
    elif state == "Close":
        event_action = "resolve"
    else:
        event_action = ""
    return(event_action)

def SendToPagerDuty(ca):
    # Send events to PagerDuty Events API
    # ca Central Alert

    header = {"Content-Type": "application/json"}

    event_action = pd_event_action(ca["state"])

    payload = {
        "payload": {
            "summary": "Aruba Central Alert ",
            "source": ca["details"]["params"][0],
            "severity": "critical",
            "custom_details": {
                "device_type": ca["alert_type"],
                "serial": ca["details"]["params"][0],
                "mac_address": ca["details"]["params"][1]
            },
        },
        "links": [
            {
                "href": "https://portal-prod2.central.arubanetworks.com/global_login/login",
                "text": "Link to Aruba Central",
            }
        ],
        "routing_key": ROUTING_KEY,
        "event_action": event_action,
        "client": "Aruba Central Webhook",
        "client_url": "https://www.arubanetworks.com",
        "dedup_key": ca["id"]
    }

    pd_url = "https://events.pagerduty.com/v2/enqueue"

    response = requests.post(pd_url, data=json.dumps(payload), headers=header)

    if response.json()["status"] == "success":
        print(
            "Incident created with with dedup key (also known as incident / alert key) of "
            + '"'
            + response.json()["dedup_key"]
            + '"'
        )
    else:
        print(response.text)  # print error message if not successful

def SendToSlack(ca, state):
    # Send events to Slack Events API
    # ca Central Alert

    if state == "Open":
        borderline = "#36a64f"
        arrow = ":greenup:"
    elif state == "Close":
        borderline = "#ff0000"
        arrow = ":reddown:"

    header = {"Content-Type": "application/json"}

    payload = {
        "text": "*Alert Type:* " + ca["alert_type"] + " - *" + ca["device_id"] + "*\n"
        + "*Description:* " + ca["description"] + "\n"
        + "*Connection Status:* " + ca["details"]["conn_status"] + " - " + ca["state"] + "\n"
        + "*AP Name:* " + ca["details"]["params"][0] + "\n"
        + "*MAC Address:* " + ca["details"]["params"][1] + "\n"
        + "*Serial Number:* " + ca["device_id"] + "\n",
        "username": "ArubaCentralAlert",
        "mrkdwn": "true"
    }
    

    response = requests.post(SLACK_URL, data=json.dumps(payload), headers=header)

    return("none")

 

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        return_data = request.json
        # Log request to console
        print(return_data)

        state = return_data["state"]

        # Testing
        # SendToSlack(ap_up, state)
        # SendToPagerDuty(central_data)

        # 
        # Production Slack
        SendToSlack(return_data, state)

        #
        # Production Pager Duty
        SendToPagerDuty(return_data)

        return "", 200
    else:
        abort(400)


if __name__ == "__main__":
    app.run()
