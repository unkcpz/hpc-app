from firecrest import ClientCredentialsAuthorization
from firecrest import Firecrest as CscsFirecrest
import itertools
import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration parameters for the Authorization Object
client_id = os.environ.get('FIRECREST_CLIENT_ID')
client_secret = os.environ.get('FIRECREST_CLIENT_SECRET')
token_uri = "https://auth.cscs.ch/auth/realms/cscs/protocol/openid-connect/token"

# Create an authorization account object with Client Credentials authorization grant
keycloak = ClientCredentialsAuthorization(
    client_id, client_secret, token_uri, debug=False
)


class MyKeycloakCCAccount:
    def __init__(self):
        pass

    @keycloak.account_login
    def get_access_token(self):
        return keycloak.get_access_token()

class Firecrest(CscsFirecrest):
    
    _MACHINE = 'daint'
    _SYSTEM = 'daint'
    
    def __init__(self, firecrest_url, verify=None, sa_role="firecrest-sa"):
        super().__init__(firecrest_url, authorization=MyKeycloakCCAccount())
    
    def heartbeat(self):
        """Returns information about a system as the heartbeat check.
        
        Returns the name, description, and status.
        :param system_name: the system name
        :type system_name: string
        :calls: GET `/status/systems/{system_name}`
        :rtype: list of dictionaries (one for each system)
        """
               
        return super().system(self._SYSTEM)
    
        
    # def submit(self, job_script, local_file=True):
    #     """Submits a batch script to SLURM on the target system
    #     :param job_script: the path of the script (if it's local it can be relative path, if it is on the machine it has to be the absolute path)
    #     :type job_script: string
    #     :param local_file: batch file can be local (default) or on the machine's filesystem
    #     :type local_file: boolean, optional
    #     :calls: POST `/compute/jobs/upload` or POST `/compute/jobs/path`
    #             GET `/tasks/{taskid}`
    #     :rtype: dictionary
    #     """
    #     self._current_method_requests = []
    #     submit_resp = self._submit_request(self._MACHINE, job_script, local_file)
    #     task_id = submit_resp["task_id"]
        
    #     res = self._poll_tasks(
    #         task_id, "200", itertools.cycle([1, 5, 10])
    #     )
    #     job_id = res['jobid']
        
    #     # store `job_id` in the DB with the user name
        
    #     return res
        
    def poll(self, jobs=[], start_time=None, end_time=None):
        """Retrieves information about submitted jobs.
        This call uses the `sacct` command.
        :param jobs: list of the IDs of the jobs (default [])
        :type jobs: list of strings/integers, optional
        :param start_time: Start time (and/or date) of job's query. Allowed formats are HH:MM[:SS] [AM|PM] MMDD[YY] or MM/DD[/YY] or MM.DD[.YY] MM/DD[/YY]-HH:MM[:SS] YYYY-MM-DD[THH:MM[:SS]]
        :type start_time: string, optional
        :param end_time: End time (and/or date) of job's query. Allowed formats are HH:MM[:SS] [AM|PM] MMDD[YY] or MM/DD[/YY] or MM.DD[.YY] MM/DD[/YY]-HH:MM[:SS] YYYY-MM-DD[THH:MM[:SS]]
        :type end_time: string, optional
        :calls: GET `/compute/acct`
                GET `/tasks/{taskid}`
        :rtype: list of job info dict
        """
        job_list = super().poll(self._MACHINE, jobs=jobs)
        
        ret = dict()
        for job in job_list:
            del job['user']
            ret[f'{job["jobid"]}'] = job
        
        return ret