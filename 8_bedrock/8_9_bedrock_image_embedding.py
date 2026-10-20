import boto3
import json
import base64
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

client = boto3.client(service_name='bedrock-runtime', region_name="us-west-2")

images = [
    os.path.join(BASE_DIR, "images", "alex.jpg"),
    os.path.join(BASE_DIR, "images", "hinton_train.jpg"),
    os.path.join(BASE_DIR, "images", "ilya.png"),
]

# ---------------------------------------------
# Replacement for "similarity" package function
# ---------------------------------------------
def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def getImagesEmbedding(imagePath: str):
    with open(imagePath, "rb") as f:
        base_image = base64.b64encode(f.read()).decode("utf-8")

    response = client.invoke_model(
        body=json.dumps({
            "inputImage": base_image,
        }),
        modelId='amazon.titan-embed-image-v1',
        accept='application/json',
        contentType='application/json'
    )

    response_body = json.loads(response.get('body').read())
    return response_body.get('embedding')


# ------------------------
# Get embeddings for images
# ------------------------
imagesWithEmbeddings = []
for image in images:
    imagesWithEmbeddings.append({
        'path': image,
        'embedding': getImagesEmbedding(image)
    })

# -------------------------------
# Get embedding for test image
# -------------------------------
test_image = os.path.join(BASE_DIR, "images", "hinton_test.jpg")
test_image_embedding = getImagesEmbedding(test_image)

# ------------------------
# Compute similarities
# ------------------------
similarities = []
for image in imagesWithEmbeddings:
    similarities.append({
        'path': image['path'],
        'similarity': cosine_similarity(image['embedding'], test_image_embedding)
    })

similarities.sort(key=lambda x: x['similarity'], reverse=True)

# ------------------------
# Print results
# ------------------------
print(f"Similarities of '{test_image}' with:")
for similarity in similarities:
    print(f"  '{similarity['path']}': {similarity['similarity']:.2f}")
