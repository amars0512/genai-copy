# pip install flask pypdf python-dotenv openai

from flask import Flask, request, render_template_string
from openai import OpenAI
from dotenv import load_dotenv
from pypdf import PdfReader
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(override=True)

app = Flask(__name__)

client = OpenAI()

# --- Step 1: Read Buffett PDF into a single string ---
reader = PdfReader(os.path.join(BASE_DIR, "Warren_Buffett.pdf"))
buffett = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        buffett += text

# --- Step 2: Define chat function ---
def chat_with_buffett(message):
    """
    Chat with Buffett knowledge base using OpenAI Responses API.
    message: user input
    """
    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            # Pass only the first 4k of Buffett words, ~ 1000 tokens
            # Avoids overloading: Earlier models supported just 4k tokens, GPT-4o-mini supports ~128k
            {"role": "system", "content": f"You are a helpful assistant. You can answer based on the following text:\n\n{buffett[:4000]} or from the Internet."},
            {"role": "user", "content": message},
        ]
    )
    return response.output_text

# --------------------------------------------------
# HTML
# --------------------------------------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Ask about Warren Buffett</title>
<style>
body{font-family:Arial;width:800px;margin:auto;margin-top:40px}
textarea{width:100%;height:80px}
.answer{margin-top:20px;padding:15px;border:1px solid gray;background:#f2f2f2;white-space:pre-wrap}
</style>
</head>
<body>

<h2>Ask about Warren Buffett</h2>

<form method="post">

<textarea
name="question"
placeholder="Ask a question about Buffett..."></textarea>

<br><br>

<input type="submit" value="Ask">

</form>

{% if question %}

<h3>Your Question</h3>
<p>{{question}}</p>

<h3>Answer</h3>

<div class="answer">
{{answer}}
</div>

{% endif %}

</body>
</html>
"""

# --------------------------------------------------
# Flask Route
# --------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def home():

    question = ""
    answer = ""

    if request.method == "POST":

        question = request.form["question"]

        answer = chat_with_buffett(question)

    return render_template_string(
        HTML,
        question=question,
        answer=answer
    )

# --------------------------------------------------
# Main
# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
