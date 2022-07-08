import json
import requests
from urllib.parse import urljoin

from marketplace_standard_app_api.models.message_broker import (
    MessageBrokerRequestModel,
    MessageBrokerResponseModel,
)

from marketplace.message_broker.rpc_server import RpcServer

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
    # print("Routing to endpoint %r..." % request_message.endpoint)
    # payload = json.loads(request_message.body) if request_message.body else {}
    # print(payload)
    # print(request_message)
    # result = len(payload)
    # response = {"numberOfKeysInPayload": str(result)}
    # print("Done!")
    
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
    application_id="dc67d85e-7945-49fa-bf85-3159a8358f85",
    application_secret="2366c94a-1361-4c85-9016-e16b1fe7dfa1",
    message_handler=hpc_message_relayer,
)
rpc_server.consume_messages()