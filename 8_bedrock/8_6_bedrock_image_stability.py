import boto3
import json
import base64
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

client = boto3.client(service_name='bedrock-runtime', region_name="us-west-2")

stability_image_config = json.dumps({
    "prompt": "a typical busy day in an indian city market, make it funny as well",
})

response = client.invoke_model(
    body=stability_image_config, 
    modelId="stability.stable-image-core-v1:1", 
    accept="application/json", 
    contentType="application/json")

response_body = json.loads(response.get("body").read())
#base64_image = response_body.get("images")
base64_image = response_body.get("images")[0]

base_64_image = base64.b64decode(base64_image)

file_path = os.path.join(BASE_DIR, "bedrock_image_8_6.png")
with open(file_path, "wb") as f:
    f.write(base_64_image)