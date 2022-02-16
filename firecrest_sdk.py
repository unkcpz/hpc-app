from firecrest import ClientCredentialsAuthorization
from firecrest import Firecrest as CscsFirecrest
import requests
import io
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
    
    def submit(self, job_script):
        """Submits a batch script to SLURM on the target system
        :param job_script: the content of the script (if it's local it can be relative path, if it is on the machine it has to be the absolute path)
        :type job_script: string
        :calls: POST `/compute/jobs/upload` or POST `/compute/jobs/path`
                GET `/tasks/{taskid}`
        :rtype: dictionary
        """
        return super().submit(machine=self._MACHINE, job_script=job_script, local_file=True)
        
    # Compute
    def _submit_request(self, machine, job_script: str, local_file):
        """Override so job_script can be a string"""
        headers = {
            "Authorization": f"Bearer {self._authorization.get_access_token()}",
            "X-Machine-Name": machine,
        }
        if local_file:
            url = f"{self._firecrest_url}/compute/jobs/upload"
            files = {"file": io.StringIO(job_script)}
            resp = requests.post(
                url=url, headers=headers, files=files, verify=self._verify
            )
        else:
            url = f"{self._firecrest_url}/compute/jobs/path"
            data = {"targetPath": job_script}
            resp = requests.post(
                url=url, headers=headers, data=data, verify=self._verify
            )

        self._current_method_requests.append(resp)
        return self._json_response(self._current_method_requests, 201)
    
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