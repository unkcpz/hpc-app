import jwt, os
import io
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask import Response, stream_with_context
from flask import send_file
from firecrest_sdk import Firecrest
import requests
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename

load_dotenv()

WHITE_LIST = ['jusong.yeu@gmail.com']
# Setup the client for the specific account
client = Firecrest(firecrest_url="https://firecrest.cscs.ch/")
ROOT_FOLDER = '/scratch/snx3000/jyu/firecrest/'

ALLOWED_EXTENSIONS = {'txt', 'sh', 'in'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is a secret'
print(SECRET_KEY)

app.config['SECRET_KEY'] = SECRET_KEY
app.config['ROOT_FOLDER'] = ROOT_FOLDER

from models import Jobs, User
from auth_middleware import token_required

def helper_get_db_userid(mp_user):
    pass

def email2repo(email):
    """Since the username allowed space character contained it is not proper to be 
    directly used as repo (folder) name
    this helper function will convert space to underscore"""
    username = email.split('@')[0] # get username of email
    repo = username.replace('.', '_')
    
    return repo
    
@app.route("/")
@token_required
def heartbeat(current_user):
    user = User().get_by_email(current_user['email'])
    if not user:
        resp = {
            'message': 'user not create yet, please register for DB first time.'
        }
        return resp, 401
    else: 
        resp = {
            'message': 'user is available.'
        }
        try:
            fresp = client.heartbeat()
            resp.update(fresp)
        except Exception as e:
            raise e
    
    return resp, 200

@app.route("/userinfo/", methods=["GET"])
@token_required
def get_userinfo(current_user):
    user = User().get_by_email(current_user['email'])
    if user:
        resp = {
            'db_user': user,
            'marketplace_user': current_user,
        }
    else:
        resp = {
            'db_user': 'NOT AVAILABLE',
            'marketplace_user': current_user,
        }
    
    return resp, 200

@app.route("/register/", methods=["GET"])
@token_required
def register(current_user):
    try:
        email = current_user['email']
        name = current_user['name']
        if email in WHITE_LIST:
            try:
                # user name and email validate
                user = User().create(name=name, email=email)
            except Exception as e:
                return {
                    'error': 'failed to create user in DB.'
                }, 500
        else:
            return {
                'error': f'User <{name}> is not allowed to access database.'
            }, 406
            
        # user are created or aready exist (None return from create method)
        if user:
            # create the repository for user to store file
            repo = email2repo(email)
            client.mkdir(target_path=os.path.join(app.config['ROOT_FOLDER'], repo))
            
            # New db user created
            resp = {
                'message': 'New database and repository are created.',
                'data': {
                    'name': name,
                    'email': email,
                    '_id': user['_id']
                }
            } 
            return resp, 200
        else:
             # Already exist in DB
            return {
                'message': 'Already registered in database.'
            }, 200
    except Exception as e:    
        return {
            "error": "Something went wrong",
            "message": str(e)
        }, 500
        
@app.route("/submit/", methods=["POST"])
@token_required
def submit(current_user):
    data = request.json
    path = data.get('path')
    script_path = os.path.join(path, '_submit.sh')
    # TODO: check user has access to the path and the job script exist
    try:
        resp = client.submit(job_script=script_path)
        user = User().get_by_email(current_user['email'])
        userid = user['_id']
        jobid = resp.get('jobid')
        job = Jobs().create(userid=userid, jobid=jobid)
        
        resp['userid'] = job['userid']
        
    except Exception as e:
        return {
            "function": 'ubmit',
            "error": "Something went wrong",
            "message": str(e)
        }, 500
        
    return resp, 200
        
@app.route("/jobs/", methods=["GET"])
@token_required
def list_jobs(current_user):
    user = User().get_by_email(current_user['email'])
    userid = user['_id']
    
    jobs = Jobs().get_by_userid(userid)
    try:
        fresp = client.poll(jobs=jobs)
    except Exception as e:
        raise e
    
    return fresp, 200

@app.route("/download/<resource>", methods=["GET"])
@token_required
def download_remote(current_user, resource):
    """
    Downloads the remote files from the cluster.
    :param path: path string relative to the parent ROOT_PATH=`/scratch/snx3000/jyu/firecrest/`
    :return: file.
    """
    repo = email2repo(current_user['email'])
    
    data = request.json
    filename = data.get('filename')
    source_path = os.path.join(ROOT_FOLDER, repo, resource, filename)
    app.logger.debug(source_path)
    binary_stream = io.BytesIO()
    
    client.simple_download(source_path=source_path, target_path=binary_stream)

    download_name = os.path.basename(filename)
    binary_stream.seek(0) # buffer position from start
    resp = send_file(path_or_file=binary_stream, download_name=download_name)
    
    return resp, 200

@app.route("/upload/<resource>", methods=["PUT"])
@token_required
def upload_remote(current_user, resource):
    """
    Upload the file to the cluster. to folder ROOT_PATH=`/scratch/snx3000/jyu/firecrest/`
    """
    repo = email2repo(current_user['email'])
    
    if 'file' not in request.files:
        flash('No file part')
        return jsonify({
            "message": "No file part",
            "error": str('error'),
            "data": None
        }), 403
        
    file = request.files['file']
    target_path = os.path.join(app.config['ROOT_FOLDER'], repo, resource)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        binary_stream = io.BytesIO(file.read())
        
        resp = client.simple_upload(binary_stream, target_path, filename)
    
        return resp, 200
    
@app.route("/delete/<resource>", methods=["DELETE"])
@token_required
def delete_remote(current_user, resource):
    """
    Downloads the remote files from the cluster.
    :param path: path string relative to the parent ROOT_PATH=`/scratch/snx3000/jyu/firecrest/`
    :return: file.
    """
    repo = email2repo(current_user['email'])
    
    data = request.json
    filename = data.get('filename')
    target_path = os.path.join(ROOT_FOLDER, repo, resource, filename)
    
    client.simple_delete(target_path=target_path)
    
    return '', 204


@app.errorhandler(403)
def forbidden(e):
    return jsonify({
        "message": "Forbidden",
        "error": str(e),
        "data": None
    }), 403

@app.errorhandler(404)
def forbidden(e):
    return jsonify({
        "message": "Endpoint Not Found",
        "error": str(e),
        "data": None
    }), 404


if __name__ == "__main__":
    app.run(debug=True, 
            port=5005, 
            # ssl_context='adhoc'
    )
