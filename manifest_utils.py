# Author       : Lenine Ajagappane (Lenine.Ajagappane@amd.com)
# Description  : Manifest parser

import logging
import os
import requests
import xmltodict


class ManifestUtils:

    def __init__(self):
        pass

    def get_commit_from_manifest(self, build_url, comp_project):
        try:
            manifest_url = os.path.join(build_url, 'artifact/manifest.xml')
            response = requests.get(manifest_url)
            data = xmltodict.parse(response.content)
            if not 'Error 404 Not Found' in str(data):
                manifest_info = self.extract_manifest_details(data, comp_project)
                return ','.join(manifest_info)
            return None
        except Exception as e:
            raise ValueError("Exception in get_commit_from_manifest: {}".format(e))

    def extract_manifest_details(self, manifest_dict, comp_project):
        manifest_info = []
        try:
            if manifest_dict:
                for component in manifest_dict["manifest"]["project"]:
                    component_path, component_branch, component_remote = 'None', 'None', 'None'
                    try:
                        component_name = component['@name']
                        if '-internal' in component_name and component_name not in ['rocprofiler-register-internal', 'rocprofiler-sdk-internal']:
                            component_name = component_name.split('-')[0]
                        component_commit = component['@revision']
                        if '@path' in component:
                            component_path = component['@path']
                        if '@upstream' in component:
                            component_branch = component['@upstream']
                        if '@remote' in component:
                            component_remote = component['@remote']
                        for project in comp_project:
                            if component_name == 'lightning/ec/llvm-project' and component_path == 'external/llvm-project-alt/llvm-project':
                                break
                            if project == 'None':
                                manifest_info.extend(['name', component_name, component_path, component_branch, component_commit, component_remote])
                            else:
                                if project == component_name:
                                    manifest_info.extend(['name', component_name, component_path, component_branch, component_commit, component_remote])
                    except KeyError:
                        #logging.error("Key Error in {}".format(component))
                        continue
        except Exception as e:
            print("Exception while extracting manifest details: {}".format(e))
        finally:
            return manifest_info

