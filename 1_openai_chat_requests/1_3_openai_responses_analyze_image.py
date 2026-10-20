# Analyze an image
from openai import OpenAI
from dotenv import load_dotenv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(override=True)

client = OpenAI()

file = client.files.create(
    # file=open(os.path.join(BASE_DIR, "animals.pdf"), "rb"),
    file=open(os.path.join(BASE_DIR, "cheque.pdf"), "rb"),
    purpose="user_data"
)

response = client.responses.create(
    model="gpt-4o-mini",
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_file",
                    "file_id": file.id,
                },
                {
                    "type": "input_text",
                    # "text": "Which animals are these?",
                    "text": "Extract and list the various parts of the cheque."
                },
            ]
        }
    ]
)

print(response.output_text)