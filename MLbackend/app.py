from flask import Flask, render_template, request, jsonify
import sys
import os
import re
import validators


sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from devNetwork import communitySmellsDetector



app = Flask(__name__)

class InvalidInputError(Exception):
    pass

def validate_repo_url(url: str) -> None:

    if not url or not validators.url(url):
        raise InvalidInputError("Invalid repository URL format.")

def validate_email(email: str) -> None:

    if not email or not validators.email(email):
        raise InvalidInputError("Invalid email format.")

def validate_pat(token: str) -> None:

    if not re.match(r'^[a-zA-Z0-9-_]+$', token):
        raise ValueError("Invalid PAT format.")



@app.route('/')
def home():
    return render_template('index.html')  

@app.route('/api/v1/smells', methods=['POST'])
def detect_smells():
    repo_url = request.form['repo-url']
    email = request.form['email']
    pat = request.form['access-token']


    # Validate inputs
    try:
        validate_repo_url(repo_url)
        validate_email(email)
        validate_pat(pat)

    except InvalidInputError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

    senti_strength_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
    
    try:
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
        # Check if result contains valid information
        if not result:
            return jsonify({
                "status": "error",
                "message": "No data found, Please try again later"
            }), 404 

        # Return successful response
        return jsonify({
            "status": "success",
            "result": result 
        }), 200
   
    except Exception as e:
        # Handle unexpected errors
        return jsonify({
            "status": "error",
            "message": "Something went wrong. Please try again later"
        }), 500  # Internal Server Error
    
if __name__ == '__main__':
    app.run(debug=True)  
