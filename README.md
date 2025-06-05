# torchserve-face-detection

This repository demonstrates deploying a face detection model using TorchServe, along with a PostgreSQL database and API services managed via Docker.

---

## PostgreSQL Setup with Docker

Run PostgreSQL container:
```bash
docker run --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=fotoyu -e POSTGRES_DB=mydb -d postgres
```

##Check Database in Docker

docker exec -it postgres bash
psql -U postgres
\c mydb            # Connect to your database (replace <db name> with mydb)
\d                 # List tables and relations
SELECT * FROM <table_name>;  # Query data from a table

## Docker Network Inspection
docker network inspect bridge
docker inspect <container_name> | findstr IPAddress

## Running the Image POST API
docker build . -t test-server
docker run -t --name publish -p 3000:3000 test-server

docker build . -t test-consume
docker run -t --name consume test-consume

##TorchServe Model Packaging and Deployment

torch-model-archiver \
  --model-name mymodel \
  --version 1.0 \
  --serialized-file mtcnn.pth \
  --model-file model.py \
  --handler my_handler.py \
  --extra-files face_detection.py

torchserve --start --ncs --model-store model_store --models mymodel=face_detect_model.mar

curl localhost:8080/predictions/mymodel -T img1.jpg

## Using Python Requests (in docker)
import requests

image_path = "<image_path>"
result = requests.post(
    "http://host.docker.internal:8080/predictions/mymodel",
    files={'data': open(image_path, 'rb')}
)

print(result.json())


