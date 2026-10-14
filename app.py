from datetime import datetime
import os
import re
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# Securely fetching Groq API Key from environment variables
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# Phone ke liye Siri-style Web Interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sera Cloud Assistant</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .orb { width: 130px; height: 130px; background: linear-gradient(135deg, #6366f1, #a855f7); border-radius: 50%; box-shadow: 0 0 40px rgba(99,102,241,0.6); animation: pulse 2s infinite; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 40px; }
        @keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(99,102,241, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 25px rgba(99,102,241, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(99,102,241, 0); } }
        h2 { margin-top: 30px; font-weight: 400; color: #cbd5e1; font-size: 18px; }
        #output { margin-top: 20px; padding: 15px; background: #1e293b; border-radius: 10px; width: 85%; max-width: 400px; text-align: center; min-height: 60px; font-size: 16px; line-height: 1.5; }
    </style>
</head>
<body>
    <div class="orb" onclick="startListening()">🎙️</div>
    <h2 id="status">Tap karke kuch bole...</h2>
    <div id="output">Sera cloud par ready hai!</div>

    <script>
        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'en-IN';

        function startListening() {
            document.getElementById("status").innerText = "Sera sun rahi hai...";
            recognition.start();
        }

        recognition.onresult = async function(event) {
            const text = event.results[0][0].transcript;
            document.getElementById("status").innerText = "Aapne kaha: " + text;
            document.getElementById("output").innerText = "Soch rahi hoon...";
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({prompt: text})
                });
                const data = await response.json();
                document.getElementById("output").innerText = data.reply;
                document.getElementById("status").innerText = "Tap karke dobara bole...";

                let speech = new SpeechSynthesisUtterance(data.reply);
                speech.lang = 'hi-IN';
                window.speechSynthesis.speak(speech);
            } catch (err) {
                document.getElementById("output").innerText = "Connection error ho gaya!";
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_prompt = data.get("prompt", "")

    if any(k in user_prompt.lower() for k in ["time", "samay", "baje"]):
        reply = f"Abhi samay {datetime.now().strftime('%I:%M %p')} ho raha hai dost!"
    elif any(k in user_prompt.lower() for k in ["date", "tareekh", "din"]):
        reply = f"Aaj ki date {datetime.now().strftime('%d %B %Y')} hai dost!"
    else:
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-specdec",
                messages=[
                    {"role": "system", "content": "You are Sera, a warm AI companion. Answer thoroughly in clear conversational Hinglish without symbols, markdown, or bullet points."},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6,
                max_tokens=600,
            )
            reply = completion.choices[0].message.content
            reply = re.sub(r'[*#_~()`"\[\]\{\}>]', '', reply).strip()
        except Exception as e:
            reply = "Arey yaar, server me thoda issue aa gaya hai."

    return jsonify({"reply": reply})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)