from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv
import twilio.rest
import os
import pymysql
import jwt

pymysql.install_as_MySQLdb()
load_dotenv()
app = Flask(__name__)
cors = CORS(app,origins=["http://localhost:5173","https://callege-app-8u24x.ondigitalocean.app"])
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['APP_URL'] = os.environ.get('APP_URL')
app.config['weburl'] = os.environ.get('weburl')
app.config['ipaymuurl'] = os.environ.get('ipaymuurl')
app.config['ipaymuva'] = os.environ.get('ipaymuva')
app.config['ipaymukey'] = os.environ.get('ipaymukey')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['TWILIO_ACCOUNT_SID'] = os.environ.get('TWILIO_ACCOUNT_SID')
app.config['TWILIO_API_KEY_SID'] = os.environ.get('TWILIO_API_KEY_SID')
app.config['TWILIO_AUTH_TOKEN'] = os.environ.get('TWILIO_AUTH_TOKEN')
app.config['TWILIO_API_KEY_SECRET'] = os.environ.get('TWILIO_API_KEY_SECRET')
app.config['GOOGLE_OAUTH_REDIRECT'] = os.environ.get('GOOGLE_OAUTH_REDIRECT')
app.config['GOOGLE_OAUTH_SCOPES'] = ["https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile","openid"]

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app,cors_allowed_origins=['http://localhost:5173','https://callege-app-8u24x.ondigitalocean.app'],logger=True,engineio_logger=True)
twillio_client = twilio.rest.Client(app.config['TWILIO_API_KEY_SID'],app.config['TWILIO_API_KEY_SECRET'],app.config['TWILIO_ACCOUNT_SID'])
flow = Flow.from_client_secrets_file(
    'client_secrets.json',
    scopes=app.config['GOOGLE_OAUTH_SCOPES'],
    redirect_uri=app.config['GOOGLE_OAUTH_REDIRECT']
)


from backend import routes