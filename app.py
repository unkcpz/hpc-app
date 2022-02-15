import jwt, os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from save_image import save_pic
from validate import validate_book, validate_user, validate_email_and_password
from firecrest_sdk import Firecrest

load_dotenv()

WHITE_LIST = ['unkcpz', 'unkcpz1']
# Setup the client for the specific account
client = Firecrest(firecrest_url="https://firecrest.cscs.ch/")
    
# submit(client, './run_demo.sh')
# poll(client, jobs=[])
# print(client.heartbeat())

app = Flask(__name__)
SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is a secret'
print(SECRET_KEY)
app.config['SECRET_KEY'] = SECRET_KEY

from models import Books, User
from auth_middleware import test_token_required, mp_token_required

token_required = test_token_required

@app.route("/")
@mp_token_required
def heartbeat(current_user):
    user = User().get_by_email(current_user['email'])
    if not user:
        resp = {
            'message': 'user not create yet, please login for first time.'
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
@mp_token_required
def get_userinfo(current_user):
    
    return current_user, 200

@app.route("/users/", methods=["POST"])
def add_user():
    try:
        user = request.json
        if not user:
            return {
                "message": "Please provide user details",
                "data": None,
                "error": "Bad request"
            }, 400
        is_validated = validate_user(**user)
        if is_validated is not True:
            return dict(message='Invalid data', data=None, error=is_validated), 400
        if user.get('name') not in WHITE_LIST:
            return dict(message=f'Only users {WHITE_LIST} allowed.', data=None), 400
        user = User().create(**user)
        if not user:
            return {
                "message": "User already exists",
                "error": "Conflict",
                "data": None
            }, 409
        return {
            "message": "Successfully created new user",
            "data": user
        }, 201
    except Exception as e:
        return {
            "message": "Something went wrong",
            "error": str(e),
            "data": None
        }, 500

@app.route("/login/", methods=["POST"])
def login():
    """This api used only in test mode, the token will given for 
    test_token_required auth"""
    try:
        data = request.json
        if not data:
            return {
                "message": "Please provide user details",
                "data": None,
                "error": "Bad request"
            }, 400
        # validate input
        is_validated = validate_email_and_password(data.get('email'), data.get('password'))
        if is_validated is not True:
            return dict(message='Invalid data', data=None, error=is_validated), 400
        user = User().login(
            data["email"],
            data["password"]
        )
        if user:
            try:
                # token should expire after 24 hrs
                user["token"] = jwt.encode(
                    {"user_id": user["_id"]},
                    app.config["SECRET_KEY"],
                    algorithm="HS256"
                )
                return {
                    "message": "Successfully fetched auth token",
                    "data": user
                }
            except Exception as e:
                return {
                    "error": "Something went wrong",
                    "message": str(e)
                }, 500
        return {
            "message": "Error fetching auth token!, invalid email or password",
            "data": None,
            "error": "Unauthorized"
        }, 404
    except Exception as e:
        return {
                "message": "Something went wrong!",
                "error": str(e),
                "data": None
        }, 500


# @app.route("/users/", methods=["GET"])
# @token_required
# def get_current_user(current_user):
#     return jsonify({
#         "message": "successfully retrieved user profile",
#         "data": current_user
#     })

# @app.route("/users/", methods=["PUT"])
# @token_required
# def update_user(current_user):
#     try:
#         user = request.json
#         if user.get("name"):
#             user = User().update(current_user["_id"], user["name"])
#             return jsonify({
#                 "message": "successfully updated account",
#                 "data": user
#             }), 201
#         return {
#             "message": "Invalid data, you can only update your account name!",
#             "data": None,
#             "error": "Bad Request"
#         }, 400
#     except Exception as e:
#         return jsonify({
#             "message": "failed to update account",
#             "error": str(e),
#             "data": None
#         }), 400

# @app.route("/users/", methods=["DELETE"])
# @token_required
# def disable_user(current_user):
#     try:
#         User().disable_account(current_user["_id"])
#         return jsonify({
#             "message": "successfully disabled acount",
#             "data": None
#         }), 204
#     except Exception as e:
#         return jsonify({
#             "message": "failed to disable account",
#             "error": str(e),
#             "data": None
#         }), 400

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
