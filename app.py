from flask import Flask, render_template, request, redirect, flash
from werkzeug.utils import secure_filename
import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from google.oauth2.service_account import Credentials

# Flask app setup
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')  # Default to 'supersecretkey' if not set

# Service account credentials file
SERVICE_ACCOUNT_FILE = 'credentials.json'

# Define the upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# Ensure the UPLOAD_FOLDER exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# PyDrive setup
gauth = GoogleAuth()
drive = None

@app.before_first_request
def setup_drive():
    global drive
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/drive.file'])
    gauth.auth_method = 'service'
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)

# Route for the main page
@app.route('/')
def index():
    return render_template('index.html')

# Route for uploading files
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
        flash('Invalid file extension')
        return redirect(request.url)

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # Upload to Google Drive
    gfile = drive.CreateFile({'title': filename})
    gfile.SetContentFile(file_path)
    gfile.Upload()

    return f'File uploaded successfully: {filename}'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)
