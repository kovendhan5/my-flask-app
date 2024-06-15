from flask import Flask, render_template, request, redirect, session, url_for, flash
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from werkzeug.utils import secure_filename
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Flask app setup
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')  # Default to 'supersecretkey' if not set

# OAuth 2.0 configuration
CLIENT_SECRETS_FILE = 'client_secrets.json'
SCOPES = ['https://www.googleapis.com/auth/drive.file']
UPLOAD_FOLDER = 'uploads'  # Folder where uploaded files will be stored
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# Ensure the UPLOAD_FOLDER exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# PyDrive setup
gauth = GoogleAuth()
drive = None

@app.before_first_request
def setup_drive():
    global drive
    gauth.LoadCredentialsFile("credentials.json")
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
        gauth.SaveCredentialsFile("credentials.json")
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    drive = GoogleDrive(gauth)

# Route for the main page
@app.route('/')
def index():
    return render_template('index.html')

# Route for uploading files
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'credentials' not in session:
        return redirect(url_for('authorize'))

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

# Authorization route
@app.route('/authorize')
def authorize():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    flow.redirect_uri = url_for('oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    session['state'] = state
    return redirect(authorization_url)

# OAuth2 callback route
@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES, state=state)
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    return redirect(url_for('index'))

# Convert OAuth 2.0 credentials to dictionary
def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
