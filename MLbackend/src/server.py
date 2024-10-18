from flask import Flask, request, jsonify, send_file, render_template
import pandas as pd
import io
from reportlab.pdfgen import canvas
from server_utils import smelldetection1

app = Flask(__name__,template_folder='../../webapp/templates')


@app.route('/analyze_repo', methods=['POST'])
def analyze_repo():
    repo_url = request.form.get('repo_url')
    pat = request.form.get('pat')
    global df
    smell_json, df = smelldetection1(repo_url,pat)
    print(df)
    return jsonify(smell_json)


from reportlab.lib.pagesizes import letter
@app.route('/generate_pdf', methods=['GET'])
def generate_pdf():
    if df is None or df.empty:
        return "DataFrame is empty or not initialized.", 400

    pdf_buffer = io.BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter

    pdf.drawString(100, height - 50, "Community Smell Report")
    pdf.drawString(100, height - 70, "Metric                Value")

    y_position = height - 100
    for index, row in df.iterrows():
        pdf.drawString(100, y_position, f"{row['Metric']: <20} {row['Value']}")
        y_position -= 20
        
        
        if y_position < 40:  
            pdf.showPage()  
            pdf.drawString(100, height - 50, "Community Smell Report")
            pdf.drawString(100, height - 70, "Metric                Value")
            y_position = height - 100  

    pdf.save()
    pdf_buffer.seek(0)

    return send_file(pdf_buffer, as_attachment=True, download_name="smell_report.pdf", mimetype='application/pdf')


# Home route
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
