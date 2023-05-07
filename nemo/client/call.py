import json
import requests
import time
from datetime import datetime as dt


def wait_for_server(server_address):
    print(dt.now(), 'waiting for server..')
    r = ''
    while r == '':
        try:
            r = requests.get(server_address+'/test').text
        except Exception as e:
            time.sleep(1)
    print(r)
    print(dt.now(), 'server is ready')


def main():
    port = '10005'
    server_address = 'http://localhost:'+port

    wait_for_server(server_address)

    data = {'text':"Hello! Is it a test message? Thank you."}

    request_str = json.dumps(data)
    response = requests.post(server_address+'/inference', json=request_str)
    print(response)

    # Save response as audio file
    with open("audio.wav", "wb") as f:
        f.write(response.content)


if __name__ == '__main__':
    main()
