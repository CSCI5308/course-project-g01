from flask import Flask, render_template, request, jsonify
import sys
import os
import subprocess
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from devNetwork import communitySmellsDetector



app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')  

@app.route('/api/v1/smells', methods=['POST'])
def detect_smells():
    repo_url = request.form['repo-url']
    email = request.form['email']
    pat = request.form['access-token']

    senti_strength_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
    # Call the function and save the result
    result = communitySmellsDetector(
         pat,
         repo_url,
         senti_strength_path,  
         output_path,       
         google_api_key= None,
         batch_months = 1,
         start_date= None
     )
    
    # print("Result: ",result)
    return jsonify({
         "status": "success",
         "result": result 
    }), 200 

    # Prepare the command to run in a subprocess
    

if __name__ == '__main__':
    app.run(debug=True)  
