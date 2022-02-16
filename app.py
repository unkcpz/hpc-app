import jwt, os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from firecrest_sdk import Firecrest

load_dotenv()

WHITE_LIST = ['jusong.yeu@gmail.com']
# Setup the client for the specific account
client = Firecrest(firecrest_url="https://firecrest.cscs.ch/")

app = Flask(__name__)
SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is a secret'
print(SECRET_KEY)
app.config['SECRET_KEY'] = SECRET_KEY

from models import Jobs, User
from auth_middleware import token_required

def helper_get_db_userid(mp_user):
    pass
    
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
            # New db user created
            resp = {
                'message': 'New DB user created.',
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
def block_submit(current_user):
    job_tmpl = """#!/bin/bash

#SBATCH --job-name={job_name}
#SBATCH --ntasks={ntasks}
#SBATCH --time={time}

{exec_line}
"""
    data = request.json
    job_script = job_tmpl.format(
        job_name=data.get('job_name'), 
        ntasks=data.get('ntasks'), 
        time=data.get('time'),
        exec_line=data.get('exec_line'),
    )
    try:
        resp = client.submit(job_script=job_script)
        # resp = {
        #     'content': job_script,
        # }
        
        #### resp example
        # {
        #     "job_data_err": "",
        #     "job_data_out": "",
        #     "job_file": "/scratch/snx3000/jyu/firecrest/3b5c96f13565b5fecb6d700fe7d4f524/file",
        #     "job_file_err": "/scratch/snx3000/jyu/firecrest/3b5c96f13565b5fecb6d700fe7d4f524/slurm-36734653.out",
        #     "job_file_out": "/scratch/snx3000/jyu/firecrest/3b5c96f13565b5fecb6d700fe7d4f524/slurm-36734653.out",
        #     "jobid": 36734653,
        #     "result": "Job submitted"
        # }
        user = User().get_by_email(current_user['email'])
        userid = user['_id']
        jobid = resp.get('jobid')
        job = Jobs().create(userid=userid, jobid=jobid)
        
        resp['userid'] = job['userid']
        
    except Exception as e:
        return {
            "function": 'block_submit',
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
            ssl_context='adhoc'
    )
