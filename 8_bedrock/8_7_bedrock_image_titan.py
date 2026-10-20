import boto3
import json
import base64
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

client = boto3.client(service_name='bedrock-runtime', region_name="us-west-2")

stability_image_config = json.dumps({
    "taskType": "TEXT_IMAGE",
    "textToImageParams": {
        "text": "an indian school playground in the 1950s",      
    },
    "imageGenerationConfig": {
        "numberOfImages": 1,
        "height": 512,
        "width": 512,
        "cfgScale": 8.0,
    }
})

response = client.invoke_model(
    body=stability_image_config, 
    modelId="amazon.nova-canvas-v1:0", ## Check this later
    accept="application/json", 
    contentType="application/json")

response_body = json.loads(response.get("body").read())
base64_image = response_body.get("images")[0]

base_64_image = base64.b64decode(base64_image)

file_path = os.path.join(BASE_DIR, "bedrock_image_8_7.png")
with open(file_path, "wb") as f:
    f.write(base_64_image)

print(f"Image saved to {file_path}")