from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from bson.json_util import dumps
import jwt

from flask_pymongo import PyMongo
from loguru import logger
import time
from functools import wraps


app = Flask(__name__)
mongo = PyMongo()
app.config['MONGO_URI'] = 'mongodb+srv://HritikThapa7:infox123@cluster0.gechm.mongodb.net/infoxdb?retryWrites=true&w=majority'
CORS(app)
mongo.init_app(app)
app.config['SECRET_KEY'] = 'infox9876'


#decorator for token authorization
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message':'Token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = mongo.db.users.find_one({'username': data['username']})
        except:
            return jsonify({'message': 'Token is invalid'}), 401

        return f(current_user, *args, **kwargs)
    
    return decorated

@app.route("/api/register/", methods=['POST'])
def register():
    """Register a user"""

    first_name = request.json.get('firstname')
    last_name = request.json.get('lastname')
    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')

    user_in_db = mongo.db.users.find_one({'username': username}) or mongo.db.users.find_one({'email': email})
    if user_in_db:
        return jsonify({"message": "User with provided username/email already exists, please try with another one."})

    mongo.db.users.insert_one({'first_name': first_name, 'last_name': last_name, 'username': username, 'email': email, 'password': password})
    return jsonify({"message": "User created"})


@app.route("/api/login/", methods=['POST'])
def login():
    """LogIn the user"""

    username = request.json.get('username')
    user_in_db = mongo.db.users.find_one({'username': username})
    logger.info(user_in_db['password'])

    if not user_in_db:
        return make_response('No user with this username', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

    if user_in_db['password'] == request.json.get("password"):
        token = jwt.encode({'username' : user_in_db['username'], 'email' : user_in_db['email']}, app.config['SECRET_KEY'])
        return jsonify({"Token": token.decode('UTF-8')})

    else:
        return make_response('Could not verify!', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})


@app.route("/api/getUser/", methods=["GET"])
@token_required
def get_user(current_user):
    """Get all the embeddings for the QA provided"""

    data = mongo.db.users.find({"username": current_user['username']})
    list_data = list(data)
    json_data = dumps(list_data)
    return jsonify({"User Details": json_data})


@app.route("/api/createEmbeddings/", methods=["POST"])
@token_required
def create_embedding(current_user):
    """Create and save the embeddings for the QA provided"""
    username = current_user['username']
    QA_NAME = request.json.get('qa_name')
    QA = request.json.get("QA")
    time.sleep(5) # sleeps for 5 seconds

    mongo.db.embeddings.insert_one({"username": username, "QA_NAME": QA_NAME, "QA": QA, "QA_embeddings": [[0.5,0.5,1.5],[1.5,1.5,0.5],[2.5,2.5,2.5]]})

    logger.info("Embeddings saved")
    return jsonify({"message": "Embeddings created successfully"})

@app.route("/api/getEmbeddings/<string:qa_name>/", methods=["GET"])
@token_required
def get_embedding(current_user, qa_name):
    """Get all the embeddings for the QA provided"""

    data = mongo.db.embeddings.find({"username": current_user['username'], "QA_NAME": qa_name})
    list_data = list(data)
    json_data = dumps(list_data)
    return jsonify({"Embedding data": json_data})

@app.route("/api/app/<string:username>/<string:qa_name>/", methods=['POST'])
def main(username, qa_name):
    """End2End infox application"""
    
    wav_file = request.json.get("q")

    transcribed_text = wav_file
    data = mongo.db.embeddings.find_one({"username": username, "QA_NAME": qa_name})
    QA = data['QA']
    logger.info(transcribed_text)
    text = QA[transcribed_text]
    return {"output": text}
    

@app.route("/healthz/")
def health():
    """Health check for the api"""

    return "INFOX-api is up and running"
