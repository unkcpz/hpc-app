import json
import requests
import os
from urllib.parse import urljoin
from dotenv import load_dotenv

load_dotenv()

from marketplace_standard_app_api.models.message_broker import (
    MessageBrokerRequestModel,
    MessageBrokerResponseModel,
)

from marketplace.message_broker.rpc_server import RpcServer

gateway_client_id = os.environ.get('GATEWAY_CLIENT_ID')
gateway_client_secret = os.environ.get('GATEWAY_CLIENT_SECRET')

HPC_GATEWAY_URL = "http://127.0.0.1:5005/"

def relay(request: MessageBrokerRequestModel):
    """get request from broker, process the request so hpc app can understand it.
    then relay it to hpc app then return (resp, status_code)
    """
    # try:
    #     token = request.headers["authorization"].split(" ")[1]
    #     print(token)
    # except:
    #     return {
    #         "message": "Authentication Token is missing!",
    #         "data": None,
    #         "error": "Unauthorized"
    #     }, 401
    token = 'aoe'
        
    headers = {
        "Accept": "application/json",
        "User-Agent": "RPC broker",
        "Authorization": f"Bearer {token}",
    }
    
    endpoint = request.endpoint
    endpoint = '/broker'    # test
    abs_url = urljoin(HPC_GATEWAY_URL, endpoint)

    # Use GET request method
    # TODO how I know it is GET??
    resp = requests.get(
        abs_url,
        headers=headers,
        verify=None,
    )
    
    return resp.json(), resp.status_code

def hpc_message_relayer(
    request_message: MessageBrokerRequestModel,
) -> MessageBrokerResponseModel:
    
    response, status_code = relay(request_message)
    print(request_message)
    
    response_message = MessageBrokerResponseModel(
        status_code=status_code,
        body=json.dumps(response),
        headers={"Content-Type": "application/json"},
    )
    return response_message

rpc_server = RpcServer(
    host="staging.materials-marketplace.eu",
    application_id=gateway_client_id,
    application_secret=gateway_client_secret,
    message_handler=hpc_message_relayer,
)
rpc_server.consume_messages()