from flask import Flask, render_template, request, jsonify
import sys
import os
import re
import validators
import json


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
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src","results"))
    
    try:
        # Call the function and save the result
        result = communitySmellsDetector(
            pat,
            repo_url,
            senti_strength_path,  
            output_path,       
            google_api_key= None,
            start_date= None
        )
        print("Results:", result)
        # Check if result contains valid information
        if not result:
            return jsonify({
                "status": "error",
                "message": "No data found, Please try again later"
            }), 404 

        data = {
                    "batch_date": "2024-10-19",
                    "smell_results": [
                        "Result 1",
                        "Result 2",
                        "Result 3",
                        "Result 4",
                        "Result 5",
                        "Result 6",
                        "Result 7",
                        "Result 8",
                        "Result 9",
                        "Result 10",
                        "Result 11",
                        "Result 12",
                        "Result 13",
                        "Result 14",
                        "Result 15",
                        "Result 16",
                        "Result 17",
                        "Result 18",
                        "Result 19",
                        "Result 20"
                    ],
                    "authors": "Author 1, Author 2, Author 3, Author 4, Author 5, Author 6, Author 7, Author 8",
                    "core_devs": "Core Dev 1, Core Dev 2, Core Dev 3",
                    "authorInfoDict": {
                        "Author 1": "Info about Author 1",
                        "Author 2": "Info about Author 2",
                        "Author 3": "Info about Author 3",
                        "Author 4": "Info about Author 4",
                        "Author 5": "Info about Author 5",
                        "Author 6": "Info about Author 6",
                        "Author 7": "Info about Author 7",
                        "Author 8": "Info about Author 8"
                    }
                }

        # Return successful response
        #return render_template('results.html', data=jsonify(json.loads(result)))
        return render_template('results.html', data=data)

        
    except Exception as e:
        # Handle unexpected errors
        return jsonify({
            "status": "error",
            "message": "Something went wrong. Please try again later"
        }), 500  # Internal Server Error
    
if __name__ == '__main__':
    app.run(port=8000,debug=True)  
