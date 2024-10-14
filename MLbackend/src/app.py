from flask import Flask, render_template, request
import subprocess
import os

app = Flask(__name__, template_folder=os.path.abspath('../../webapp/templates'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_analysis', methods=['POST'])
def run_analysis():
    # Get the GitHub PAT and repository URL from the form
    github_pat = request.form['pat']
    repo_url = request.form['repo_url']

    # Run devNetwork.py and wait for it to complete
    command = f"python devNetwork.py -p {github_pat} -r {repo_url}"
    subprocess.run(command, shell=True)

    # After the script completes, read the output.txt file
    output_file_path = '../output/temp_output.txt'
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r') as file:
            output_content = file.read()
    else:
        output_content = "No output generated."

    # Pass the content of output.txt to the template for display
    return render_template('index.html', output=output_content)

if __name__ == '__main__':
    app.run(debug=True)
