import requests
import os

port = 3000

url = f'http://127.0.0.1:{port}/image'

img = input('Type file path: ')

while True:

    if os.path.isfile(img) == True:
        break

    img = input('Wrong path! Type file path: ')

image_file = {'image': open(img, 'rb')}
r = requests.post(url, files=image_file)

# convert server response into JSON format.
try:
    data = r.json()     
    print(data)                
except requests.exceptions.RequestException:
    print(r.text)