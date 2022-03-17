import logging
from PIL import Image
import os

from flask import Flask, request, jsonify, abort

app = Flask(__name__)          
app.logger.setLevel(logging.DEBUG)
  
  
@app.route("/image", methods=["POST", "GET"])
def process_image():

    if request.method == 'POST':
        file = request.files['image']
        # Read the image via file.stream
        print(file)
        img = Image.open(file.stream)

        directory = 'images'

        if os.path.exists(directory) == False:
            os.mkdir(directory)

        img_name =  'new_image.jpg'
        img.save(f"{directory}/{img_name}")

        return jsonify({'msg': 'success', 'size': [img.width, img.height]})


  
def run_server_api():
    app.run(debug=True ,host='0.0.0.0')
  
  
if __name__ == "__main__":     
    run_server_api()