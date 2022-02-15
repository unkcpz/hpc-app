import jwt, os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from save_image import save_pic
from validate import validate_book, validate_user
from firecrest_sdk import Firecrest

load_dotenv()

WHITE_LIST = ['jusong.yeu@gmail.com']
# Setup the client for the specific account
client = Firecrest(firecrest_url="https://firecrest.cscs.ch/")

app = Flask(__name__)
SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is a secret'
print(SECRET_KEY)
app.config['SECRET_KEY'] = SECRET_KEY

from models import Books, User
from auth_middleware import token_required

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

@app.route("/jobs/", methods=["GET"])
@token_required
def get_jobs(current_user):
    try:
        fresp = client.poll(jobs=[])
    except Exception as e:
        raise e
    
    return fresp, 200

@app.route("/userinfo_test/", methods=["GET"])
@token_required
def get_userinfo(current_user):
    return current_user, 200

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

# @app.route("/books/", methods=["POST"])
# @token_required
# def add_book(current_user):
#     try:
#         book = dict(request.form)
#         if not book:
#             return {
#                 "message": "Invalid data, you need to give the book title, cover image, author id,",
#                 "data": None,
#                 "error": "Bad Request"
#             }, 400
#         if not request.files["cover_image"]:
#             return {
#                 "message": "cover image is required",
#                 "data": None
#             }, 400

#         book["image_url"] = request.host_url+"static/books/"+save_pic(request.files["cover_image"])
#         is_validated = validate_book(**book)
#         if is_validated is not True:
#             return {
#                 "message": "Invalid data",
#                 "data": None,
#                 "error": is_validated
#             }, 400
#         book = Books().create(**book, user_id=current_user["_id"])
#         if not book:
#             return {
#                 "message": "The book has been created by user",
#                 "data": None,
#                 "error": "Conflict"
#             }, 400
#         return jsonify({
#             "message": "successfully created a new book",
#             "data": book
#         }), 201
#     except Exception as e:
#         return jsonify({
#             "message": "failed to create a new book",
#             "error": str(e),
#             "data": None
#         }), 500

# @app.route("/books/", methods=["GET"])
# @token_required
# def get_books(current_user):
#     try:
#         books = Books().get_by_user_id(current_user["_id"])
#         return jsonify({
#             "message": "successfully retrieved all books",
#             "data": books
#         })
#     except Exception as e:
#         return jsonify({
#             "message": "failed to retrieve all books",
#             "error": str(e),
#             "data": None
#         }), 500

# @app.route("/books/<book_id>", methods=["GET"])
# @token_required
# def get_book(book_id):
#     try:
#         book = Books().get_by_id(book_id)
#         if not book:
#             return {
#                 "message": "Book not found",
#                 "data": None,
#                 "error": "Not Found"
#             }, 404
#         return jsonify({
#             "message": "successfully retrieved a book",
#             "data": book
#         })
#     except Exception as e:
#         return jsonify({
#             "message": "Something went wrong",
#             "error": str(e),
#             "data": None
#         }), 500

# @app.route("/books/<book_id>", methods=["PUT"])
# @token_required
# def update_book(current_user, book_id):
#     try:
#         book = Books().get_by_id(book_id)
#         if not book or book["user_id"] != current_user["_id"]:
#             return {
#                 "message": "Book not found for user",
#                 "data": None,
#                 "error": "Not found"
#             }, 404
#         book = request.form
#         if book.get('cover_image'):
#             book["image_url"] = request.host_url+"static/books/"+save_pic(request.files["cover_image"])
#         book = Books().update(book_id, **book)
#         return jsonify({
#             "message": "successfully updated a book",
#             "data": book
#         }), 201
#     except Exception as e:
#         return jsonify({
#             "message": "failed to update a book",
#             "error": str(e),
#             "data": None
#         }), 400

# @app.route("/books/<book_id>", methods=["DELETE"])
# @token_required
# def delete_book(current_user, book_id):
#     try:
#         book = Books().get_by_id(book_id)
#         if not book or book["user_id"] != current_user["_id"]:
#             return {
#                 "message": "Book not found for user",
#                 "data": None,
#                 "error": "Not found"
#             }, 404
#         Books().delete(book_id)
#         return jsonify({
#             "message": "successfully deleted a book",
#             "data": None
#         }), 204
#     except Exception as e:
#         return jsonify({
#             "message": "failed to delete a book",
#             "error": str(e),
#             "data": None
#         }), 400

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
