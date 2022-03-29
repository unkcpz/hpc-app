from firecrest import ClientCredentialsAuthorization
from firecrest import Firecrest as CscsFirecrest
import requests
import io
import os
from contextlib import nullcontext
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
        :param job_script: on the machine it has to be the absolute path
        :type job_script: string of path
        :calls: POST `/compute/jobs/path`
                GET `/tasks/{taskid}`
        :rtype: dictionary
        """
        # TODO check path is abs path else raise
        return super().submit(machine=self._MACHINE, job_script=job_script, local_file=False)
    
    def simple_download(self, source_path, target_path):
        """Blocking call to download a small file.
        The maximun size of file that is allowed can be found from the parameters() call.
        :param source_path: the absolute source path
        :type source_path: string
        :param target_path: binary stream
        :type target_path: binary stream
        :calls: GET `/utilities/download`
        :rtype: None
        """
        
        url = f"{self._firecrest_url}/utilities/download"
        headers = {
            "Authorization": f"Bearer {self._authorization.get_access_token()}",
            "X-Machine-Name": self._MACHINE,
        }
        params = {"sourcePath": source_path}
        resp = requests.get(
            url=url, headers=headers, params=params, verify=self._verify
        )
        # print(resp.content)
        self._json_response([resp], 200)
        context = nullcontext(target_path)

        with context as f:
            f.write(resp.content)
            
    def simple_upload(self, source_path, target_path, filename):
        """Blocking call to upload a small file.
        The file that will be uploaded will have the same name as the source_path.
        The maximum size of file that is allowed can be found from the parameters() call.
        :param source_path: binary stream
        :type source_path: binary stream
        :param target_path: the absolute target path of the directory where the file will be uploaded
        :type target_path: string
        :calls: POST `/utilities/upload`
        :rtype: None
        """

        url = f"{self._firecrest_url}/utilities/upload"
        headers = {
            "Authorization": f"Bearer {self._authorization.get_access_token()}",
            "X-Machine-Name": self._MACHINE,
        }
        context = nullcontext(source_path)

        with context as f:
            data = {"targetPath": target_path}
            files = {"file": (filename, f)}
            resp = requests.post(
                url=url, headers=headers, data=data, files=files, verify=self._verify
            )

        return self._json_response([resp], 201)
    
    def simple_delete(self, target_path):
        """Blocking call to delete a small file.
        :param target_path: the absolute target path
        :type target_path: string
        :calls: DELETE `/utilities/rm`
        :rtype: None
        """

        url = f"{self._firecrest_url}/utilities/rm"
        headers = {
            "Authorization": f"Bearer {self._authorization.get_access_token()}",
            "X-Machine-Name": self._MACHINE,
        }
        data = {"targetPath": target_path}
        resp = requests.delete(url=url, headers=headers, data=data, verify=self._verify)
        
        self._json_response([resp], 204)
            
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