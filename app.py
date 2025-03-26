#app.py
import os
import json
from flask import Flask, render_template, request, jsonify
from flask_session import Session
from modules.chatbot import ask_chatbot

# تنظیمات Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# مسیرها
@app.route("/")
def index():
    return render_template("chat.html")

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.form['user_input']
    response = ask_chatbot(user_input)
    return jsonify({"response": response})

@app.route('/chat')
def chat():
    return render_template('chat.html')


if __name__ == "__main__":
    app.run(debug=True)