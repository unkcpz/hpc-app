from functools import wraps
from flask import request
import requests

USERINFO_URL = "https://www.materials-marketplace.eu/auth/realms/marketplace/protocol/openid-connect/userinfo"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]
        if not token:
            return {
                "message": "Authentication Token is missing!",
                "data": None,
                "error": "Unauthorized"
            }, 401
        try:
            headers = {
                "Accept": "application/json",
                "User-Agent": "HPC-app",
                "Authorization": f"Bearer {token}",
            }

            # Use GET request method
            resp = requests.get(
                USERINFO_URL,
                headers=headers,
                verify=None,
            )

            if resp.status_code == 200:
                current_user = resp.json()
            else:
                current_user = None

            if current_user is None:
                return {
                "message": "Invalid Authentication token!",
                "data": None,
                "error": "Unauthorized"
            }, 401

        except Exception as e:
            return {
                "message": "Something went wrong",
                "data": None,
                "error": str(e)
            }, 500

        return f(current_user, *args, **kwargs)

    return decorated