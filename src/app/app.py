from flask import Flask, jsonify, Response 
from dotenv import load_dotenv
import json
import os

# Create app
app = Flask('Trading_Advisor') 

# Specify result of GET request
@app.route('/advice', methods=['GET'])  
def give_advice() -> Response:
    
    load_dotenv(dotenv_path="../../.env")
    DATAPATH = os.getenv("DATAPATH")

    with open(f"{DATAPATH}/advice.json", 'r') as json_file:
        data = json.load(json_file)

    return jsonify(data) # Flask route should always return a Flask repsonse object

if __name__ == '__main__':
    app.run()