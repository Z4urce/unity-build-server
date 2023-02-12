import json
import requests

def send_message(webhook_url, message):
    request_data = {'text': message}
    response = requests.post(
        webhook_url, data=json.dumps(request_data),
        headers={'Content-Type': 'application/json'}
        )
    if response.status_code != 200:
        raise ValueError(
            'Request to webhook returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )
