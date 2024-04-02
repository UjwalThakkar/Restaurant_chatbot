from flask import Flask, render_template, request, jsonify
import numpy as np
import pickle
import json
import random
import nltk
from keras.models import load_model
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()

import functions

#chat initialization 
model = load_model("chatbot_model.h5")
intents = json.loads(open("dataset.json").read())



app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# @app.route("/get1", methods=["POST"])
# def chatbot_response():
#     msg = request.form["msg"]
#     if msg.startswith('my name is'):
#         name = msg[11:]
#         ints = predict_class(msg, model)
#         res1 = getResponse(ints, intents)
#         res =res1.replace("{n}",name)
#     elif msg.startswith('hi my name is'):
#         name = msg[14:]
#         ints = predict_class(msg, model)
#         res1 = getResponse(ints, intents)
#         res =res1.replace("{n}",name)
#     else:
#         ints = predict_class(msg, model)
#         res = getResponse(ints, intents)
#     return res

@app.route("/get")
def get_bot_response():
    msg = request.args.get('msg')
    print(msg)
    response = ""
    if msg:
        response = functions.getResponse(msg, model)
        return response
    else:
        return "Missing Data!"


if __name__ == "__main__":
    app.run()


