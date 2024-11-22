# Author      : Lenine Ajagappane <Lenine.Ajagappane@amd.com>
# Description : Utils to perform job/build related operation.

import os
import re
import requests
import subprocess
import xmltodict
from manifest_utils import ManifestUtils


class JobUtils:

    comp_manifest_map = {
        'Compiler-ROCm':'Compiler',
        'Compiler-GFX-Linux':'Compiler',
        'Debugger':'Debugger',
        'HIP-ROCm':'HIP',
        'LRT-GFX-Linux':'HIP',
        'Profiler':'Profiler',
        'Mathlibs':'Mathlibs',
        'ROCr':'ROCr',
        'MIOpen':'MIOpen',
        'RCCL':'RCCL',
        'Release-Staging':'Release-Staging'
    }
    manifest_info = {
        'Compiler': ['lightning/ec/llvm-project', 'compute/ec/flang', 'compute/ec/aomp', 'compute/ec/aomp-extras', 'compute/ec/hipify'],
        'HIP': ['compute/ec/hip', 'compute/ec/hip-examples', 'compute/ec/hip-tests', 'compute/ec/clr', 'compute/ec/hipother',
                'compute/ec/OpenCL-CLHPP', 'compute/ec/OpenCL-CTS', 'compute/ec/OpenCL-Headers', 'compute/ec/OpenCL-ICD-Loader'],
        'Debugger': ['compute/ec/rocm-gdb', 'compute/ec/rocm-dbgapi', 'DevTools/ec/rocr_debug_agent'],
        'Profiler': ['compute/ec/rocprofiler', 'compute/ec/roctracer', 'hsa/ec/aqlprofile', 'rocprofiler-register-internal', 'rocprofiler-sdk-internal', 'omniperf', 'omnitrace'],
        'ROCr': ['hsa/ec/hsa-runtime', 'compute/ec/libhsakmt', 'hsa/ec/rocr-runtime'],
        'Mathlibs': ['rocBLAS', 'rocFFT', 'rocSPARSE', 'rocALUTION', 'rocSOLVER', 'rocPRIM', 'rocRAND', 'hipBLASLt', 'hipBLAS',
                        'hipFFT', 'hipCUB', 'rocThrust', 'hipSOLVER', 'hipSPARSE', 'hipSPARSELt', 'hipRAND', 'hipFORT', 'hipTensor',
                        'Tensile', 'rocDecode', 'rocPyDecode', 'rccl', 'rocWMMA', 'rocm-cmake'],
        'MIOpen': ['MIOpen', 'composable_kernel'],
        'RCCL': ['rccl'],
        'Release-Staging': ['None']
    }
    # For capturing ticket_fixed details
    gerrit_projects = [
        'Compiler-ROCm',
        'Compiler-GFX-Linux',
        'Debugger',
        'HIP-ROCm',
        'LRT-GFX-Linux',
        'Profiler',
        'ROCr'
    ]

    def __init__(self):
        self.manifest = ManifestUtils()

    def get_commit_from_build(self, build_url, comp_name):
        if comp_name in list(self.comp_manifest_map.keys()):
            return self.manifest.get_commit_from_manifest(build_url, self.manifest_info[self.comp_manifest_map[comp_name]])
        return None

    def get_commit_from_base_build(self, build_url, comp_name):
        if comp_name in list(self.comp_manifest_map.keys()) and 'psdb' not in build_url:
            base_build_url = self.get_mainline_base_build_url(build_url)
            return self.manifest.get_commit_from_manifest(base_build_url, self.manifest_info[self.comp_manifest_map[comp_name]])
        return None

    def get_cherrypick_patches_from_build(self, build_url):
        cp_patches = ''
        try:
            if self.is_url(build_url):
                params = self.get_jenkins_parameter(build_url)
                if params is None:
                    cp_patches = ''
                else:
                    if bool(params['ENABLE_CHERRY_PICK_PRS']):
                        cp_patches = params['CHERRY_PICK_PRS']
                    else:
                        cp_patches = None
        except Exception as e:
            print(e)
        finally:
            return cp_patches

    def get_promoted_build_commits(self, data, comp_name):
        promo_commit = ''
        if data[10] != '<a href=""></a>':
            promo_build = re.findall(r'href=[\'"]?([^\'" >]+)', data[10])[0]
            promo_build = promo_build if promo_build.endswith('/') else promo_build + '/'
            if self.is_url(promo_build):
                if comp_name in self.comp_manifest_map.keys():
                    promo_commit = self.get_commit_from_build(promo_build, comp_name)
        return promo_commit

    def get_commit_diff_for_release_stg(self, stg_commit_str, base_commit_str):
        # [ProjectName, ProjectPath', BranchName, CommitId, RemoteName]
        diff = []
        diff_str = ''
        stg_commit = self.format_manifest_data(stg_commit_str)        # [ProjectName, ProjectPath', BranchName, CommitId, RemoteName]
        base_commit = self.format_manifest_data(base_commit_str)      # [ProjectName, ProjectPath', BranchName, CommitId, RemoteName]
        for stg in stg_commit:
            for base in base_commit:
                if stg[0] == base[0]:
                    if stg[3] == base[3]:
                        break
                    diff.append(f"name,{stg[0]},{stg[1]},{stg[2]},{stg[3]},{stg[4]}")
                    break
        diff_str = ','.join(diff)
        return diff_str

    def get_promoted_status_info(self, data, is_promo=False):
        # ['Component', 'StagingCommit', 'StagingBranch', 'StagingRemoteName', 'StagingRequest?', 'Promoted?']
        diff = []
        diff_str = ''
        stg_commit = self.format_manifest_data(data[13])       # [ProjectName, ProjectPath', BranchName, CommitId, RemoteName]
        base_commit = self.format_manifest_data(data[15])      # [ProjectName, ProjectPath', BranchName, CommitId, RemoteName]
        promoted_commit = None
        if not is_promo:
            for stg in stg_commit:
                for base in base_commit:
                    promo_status = '-'
                    stg_request = 'Yes'
                    if stg[0] == base[0]:
                        if stg[3] == base[3]:
                            stg_request = 'No'
                            promo_status = 'NA'
                        diff.append(f"name,{stg[0]},{stg[3]},{stg[2]},{stg[4]},{stg_request},{promo_status}")
                        break
        else:
            promoted_commit = self.format_manifest_data(data[16])  # [ProjectName, ProjectPath', BranchName, CommitId, RemoteName]
            commit_status = self.format_manifest_data(data[17])  # ['Component', 'StagingCommit', 'StagingBranch', 'StagingRemoteName', 'StagingRequest?', 'Promoted?']
            for stg in commit_status:
                for base in base_commit:
                    for promo in promoted_commit:
                        promo_status = 'No'
                        if stg[0] == base[0] == promo[0]:
                            if stg[1] == base[3]:
                                promo_status = 'NA'
                            elif base[3] == promo[3]:
                                promo_status = 'No'
                            elif (stg[1] != base[3]) and (stg[1] != promo[3]):
                                promo_status = 'No'
                            elif (stg[1] != base[3]) and (stg[1] == promo[3]):
                                promo_status = 'Yes'
                            diff.append(f"name,{stg[0]},{stg[1]},{stg[2]},{stg[3]},{stg[4]},{promo_status}")
                            break
        diff_str = ','.join(diff)
        return diff_str

    def get_ticket_info_from_gitlog(self, data, last_promoted_build, promoted_build_commit=''):
        # Fetching last promoted staging build's commit details
        if promoted_build_commit != '':
            last_promo_commit = self.format_manifest_data(promoted_build_commit)
        else:
            last_promo_commit = self.format_manifest_data(self.get_commit_from_build(last_promoted_build, data[0]))
        if data[13] != '' and data[13] != None and data[13] != 'None':
            stg_commit = self.format_manifest_data(data[13])
            # Pull latest sources
            repo_path = self.repo_sync(data[0])
            tick_list = []
            for stg in stg_commit:
                for last in last_promo_commit:
                    if stg[0] == last[0]:
                        commit_dict = {}
                        if stg[3] == last[3]: # if both staging & last promoted commit is same
                            break
                        elif ('Compiler' not in data[0] and stg[2] != last[2]): # if both staging & last promoted branch is different
                            break
                        else:
                            commit_dict['project'] = stg[0]
                            commit_dict['path'] = stg[1]
                            commit_dict['stg_branch'] = stg[2]
                            commit_dict['stg_commit'] = stg[3]
                            commit_dict['promo_commit'] = last[3]
                        ticlist = self.fetch_ticket_from_gitlog(repo_path, commit_dict)
                        tick_list.extend(ticlist)
            tick_list = list(set(tick_list))
            print(f'Final No. of ticket in {data[-1]}: {len(tick_list)}')
            if not bool(tick_list):
                tick_list = ['None']
            elif 'FAIL' in tick_list:
                tick_list = []
            return ','.join(tick_list)
        else:
            return 'NA'

    def repo_sync(self, comp_name):
        try:
            retry = 0
            repo_name = 'rocm_repo' if not 'Compiler' in comp_name else 'rocm_repo_compiler'
            repo_path = os.path.join(os.path.dirname(__file__), f'../{repo_name}')
            if not os.path.exists(repo_path):
                os.makedirs(repo_path)
            os.chdir(repo_path)
            init_cmd = 'repo init -u ssh://gerritgit/compute/ec/manifest.git -b lajagapp/cqe-staging -m cqe-dashboard-compute.xml --reference=/jenkins/reference-repo'
            sync_cmd = 'repo sync --force-sync'
            p_status = self.run_bash_cmd(f'{init_cmd} && {sync_cmd}')
            if p_status != 0:
                retry += 1
                if retry > 5:
                    return
                self.run_bash_cmd(f'sudo rm -rf * .* && {init_cmd} && repo forall --jobs=16 -c "git reset --hard" && {sync_cmd}')
        except Exception as e:
            print(e)
        finally:
            return repo_path

    def fetch_ticket_from_gitlog(self, repo_path, commit_dict):
        try:
            retry = 0
            comp_path = f"{repo_path}/{commit_dict['path']}"
            print(f'Fetching details in "{comp_path}"..')
            file = open(f'{repo_path}/.repo/manifests/cqe-dashboard-compute.xml')
            content = file.read()
            repo_data = xmltodict.parse(content)
            repo_manifest = self.manifest.extract_manifest_details(repo_data, [commit_dict['project']])
            os.chdir(comp_path)
            checkout_cmd = f"git checkout {commit_dict['stg_branch']} && git pull"
            print(checkout_cmd)
            p_status = self.run_bash_cmd(checkout_cmd)
            if p_status != 0:
                retry += 1
                if retry > 5:
                    return
                checkout_cmd2 = f"git pull origin {repo_manifest[4]} && git checkout {commit_dict['stg_branch']} && git pull"
                self.run_bash_cmd(checkout_cmd2)
            cmd = f"git log {commit_dict['stg_commit']}...{commit_dict['promo_commit']} --grep SWDEV"
            print(cmd)
            out = self.run_bash_cmd_return(cmd)
            ticlist = re.findall(r"SWDEV-\d{6}", out)
            print(f"No. of ticket in {commit_dict['project']}: {len(ticlist)}")
            return ticlist
        except Exception as e:
            print(e)
            return ['FAIL']

    def format_manifest_data(self, manifest_str, skip_remote=False):
        vals = manifest_str.split('name')[1:]
        vals = [str(i).split(',') for i in vals]
        for ele in vals:
            ele[:] = [x for x in ele if x]
        if skip_remote:
            vals = [i[:-1] for i in vals if skip_remote]
        return vals

    def is_url(self, inp):
        if inp.startswith('http') or inp=='':
            return True
        return False

    def get_mainline_base_build_url(self, build_url):
        base_build_url = None
        try:
            while True:
                text = self.get_request_response(build_url)
                text = text.replace('last promoted IV build for compute-rocm-dkms-no-npi-hipclang', 'specified build')
                text = text.replace('last successful build for compute-rocm-dkms-no-npi-hipclang', 'specified build')
                if bool(re.search(f'Based on specified build: <a href="(\S+)"', text)):
                    url = re.search(f'Based on specified build: <a href="(\S+)"', text).group(1)
                    base_build_url = self.get_mainline_base_build_url(url)
                    break
                else:
                    base_build_url = build_url
                    break
        except Exception as e:
            print(e)
        finally:
            return base_build_url

    def get_jenkins_parameter(self, build_url):
        parameter = {}
        for retry in range(5):
            try:
                resp = requests.get(f'{build_url}/api/json?pretty=true&&tree=actions[parameters[name,value]]')
                if resp.status_code not in (200, ):
                    print('Failed to Fetch Build Details')
                    return None
                for data in resp.json()['actions']:
                    for key,val in data.items():
                        if key == 'parameters':
                            for val1 in val:
                                parameter[val1['name']] = val1['value']
                return parameter
            except Exception as e:
                print(e)
                continue

    def get_request_response(self, build_url):
        for retry in range(5):
            try:
                resp = requests.get(build_url)
                assert resp.status_code in (200, ), 'Failed to Fetch Build Details'
                return resp.text
            except Exception as e:
                print(e)
                continue

    def run_bash_cmd(self, command):
        bash_stdout = None
        bash_stderr = None
        p = subprocess.Popen(command, stdout=bash_stdout, stderr=bash_stderr, shell=True)
        (output, err) = p.communicate()
        p_status = p.wait()
        if bash_stdout is not None:
            output = output.decode('utf-8')
        return p_status

    def run_bash_cmd_return(self, command):
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        (output, err) = p.communicate()
        return output.strip()
