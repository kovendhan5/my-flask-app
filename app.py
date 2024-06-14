from flask import Flask, render_template, request, redirect, session, url_for
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from werkzeug.utils import secure_filename
import os
from flask_frozen import Freezer

# Flask app setup
app = Flask(__name__)
app.secret_key = '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'  # Change this to a more secure random key

# OAuth 2.0 configuration
CLIENT_SECRETS_FILE = 'client_secrets.json'
SCOPES = ['https://www.googleapis.com/auth/drive.file']
UPLOAD_FOLDER = 'uploads'  # Folder where uploaded files will be stored
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# Ensure the UPLOAD_FOLDER exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Route for the main page
@app.route('/')
def index():
    return render_template('index.html')

# Route for uploading files
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'credentials' not in session:
        return redirect(url_for('authorize'))

    # Check if the post request has the file part
    if 'file' not in request.files:
        return 'No file part'

    file = request.files['file']

    # If user does not select file, browser also submit an empty part without filename
    if file.filename == '':
        return 'No selected file'

    # Check file extension
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
        return 'Invalid file extension'

    # Save the file to UPLOAD_FOLDER
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

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
    # Retrieve the state from the session and verify it
    state = session['state']
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES, state=state)
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    return redirect(url_for('upload_file'))

# Convert OAuth 2.0 credentials to dictionary
def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

# Initialize Frozen-Flask
freezer = Freezer(app)

if __name__ == '__main__':
    # If running locally, use Flask development server
    app.run(debug=True)
else:
    # If deploying to Frozen-Flask (for GitHub Pages)
    # Generate static files
    freezer.freeze()
