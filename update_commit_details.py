# Author      : Lenine Ajagappane <Lenine.Ajagappane@amd.com>
# Description : Script to update commit_info, base_commit, promo_details, promo_status details in DB if empty

import datetime
import dateutil.relativedelta as rd
import re
from dashboard import Dashboard
from database import Database
from job_utils import JobUtils


class UpdateCommitDetails:

    def __init__(self):
        self.build = JobUtils()
        self.dashboard = Dashboard()
        self.db = Database()

    def update_commit_if_empty(self):
        to_date = datetime.datetime.now()
        from_date = to_date + rd.relativedelta(months = -1)
        to_date = to_date.date()
        from_date = from_date.date()
        for comp_name in self.dashboard.comp_names:
            if comp_name in list(self.build.comp_manifest_map.keys()):
                try:
                    try:
                        # Updating commit_info column for all components if empty for last 30days
                        print(f"=============================== {comp_name} - 'commit_info' [{datetime.datetime.now()}] ===========================")
                        option = {
                            'comp_name': comp_name,
                            'commit_info': ''
                        }
                        res, out_data = self.db.get_data_by_two_elements(option, from_date=from_date, to_date=to_date)
                        if res != "success":
                            raise NameError("DB failed to retrieve")
                        if bool(out_data):
                            for out in out_data:
                                print(f'build_tag: {out[-1]}')
                                if out[3] != '<a href=""></a>':
                                    build_url = re.findall(r'href=[\'"]?([^\'" >]+)', out[3])[0]
                                    build_url = build_url if build_url.endswith('/') else build_url + '/'
                                    print(f'build_url: {build_url}')
                                    if build_url.startswith('http') or build_url=='':
                                        commit_info = self.build.get_commit_from_build(build_url, out[0])
                                        res2 = self.db.add_entry(out[-1], 'commit_info', commit_info)
                                        if res2 != "success":
                                            raise NameError("DB commit failed")
                                        print(f'Updated the commit_info for {out[-1]} --> {commit_info}')
                        else:
                            print('No empty commit_info entry in last 30 days.')
                    except Exception as e:
                        print(e)

                    try:
                        # Updating base_commit column for all components if empty for last 30days
                        print(f"=============================== {comp_name} - 'base_commit' [{datetime.datetime.now()}] ===========================")
                        option = {
                            'comp_name': comp_name,
                            'base_commit': ''
                        }
                        res, out_data = self.db.get_data_by_two_elements(option, from_date=from_date, to_date=to_date)
                        if res != "success":
                            raise NameError("DB failed to retrieve")
                        if bool(out_data):
                            for out in out_data:
                                print(f'build_tag: {out[-1]}')
                                if out[3] != '<a href=""></a>':
                                    build_url = re.findall(r'href=[\'"]?([^\'" >]+)', out[3])[0]
                                    build_url = build_url if build_url.endswith('/') else build_url + '/'
                                    print(f'build_url: {build_url}')
                                    if build_url.startswith('http') or build_url=='':
                                        base_commit = self.build.get_commit_from_base_build(build_url, out[0])
                                        res = self.db.add_entry(out[-1], 'base_commit', base_commit)
                                        if res != "success":
                                            raise NameError("DB commit failed")
                                        print(f'Updated the base_commit for {out[-1]} --> {base_commit}')
                        else:
                            print('No empty base_commit entry in last 30 days.')
                    except Exception as e:
                        print(e)

                    try:
                        # Updating cp_patches column for all components if empty for last 30days
                        print(f"=============================== {comp_name} - 'cp_patches' [{datetime.datetime.now()}] ===========================")
                        option = {
                            'comp_name': comp_name,
                            'cp_patches': ''
                        }
                        res, out_data = self.db.get_data_by_two_elements(option, from_date=from_date, to_date=to_date)
                        if res != "success":
                            raise NameError("DB failed to retrieve")
                        if bool(out_data):
                            for out in out_data:
                                print(f'build_tag: {out[-1]}')
                                if out[3] != '<a href=""></a>':
                                    build_url = re.findall(r'href=[\'"]?([^\'" >]+)', out[3])[0]
                                    build_url = build_url if build_url.endswith('/') else build_url + '/'
                                    print(f'build_url: {build_url}')
                                    cp_patches = self.build.get_cherrypick_patches_from_build(build_url)
                                    if cp_patches != '':
                                        res2 = self.db.add_entry(out[-1], 'cp_patches', cp_patches)
                                        if res2 != "success":
                                            raise NameError("DB commit failed")
                                        print(f'Updated the cp_patches for {out[-1]} --> {cp_patches}')
                        else:
                            print('No empty cp_patches entry in last 30 days.')
                    except Exception as e:
                        print(e)

                    try:
                        # Updating promo_details column for all components if empty for last 30days
                        if comp_name != 'Release-Staging':
                            print(f"=============================== {comp_name} - 'promo_details' [{datetime.datetime.now()}] ===========================")
                            option = {
                                'comp_name': comp_name,
                                'is_promoted': 'Yes',
                                'promo_details': ''
                            }
                            res, out_data = self.db.get_data_by_three_elements(option, from_date=from_date, to_date=to_date)
                            if res != "success":
                                raise NameError("DB failed to retrieve")
                            if bool(out_data):
                                for out in out_data:
                                    print(f'build_tag: {out[-1]}')
                                    if out[3] != '<a href=""></a>':
                                        build_url = re.findall(r'href=[\'"]?([^\'" >]+)', out[3])[0]
                                        build_url = build_url if build_url.endswith('/') else build_url + '/'
                                        print(f'build_url: {build_url}')
                                        if build_url.startswith('http') or build_url=='':
                                            promo_commit = self.build.get_promoted_build_commits(out, out[0])
                                            res = self.db.add_entry(out[-1], 'promo_details', promo_commit)
                                            if res != "success":
                                                raise NameError("DB commit failed")
                                            print(f'Updated the promo_details for {out[-1]} --> {promo_commit}')
                            else:
                                print('No empty promo_details entry in last 30 days.')
                    except Exception as e:
                        print(e)

                    try:
                        # Updating promo_status column for Mathlibs if empty for last 30days (non promoted builds)
                        if comp_name == 'Mathlibs':
                            print(f"=============================== {comp_name} - 'promo_status - is_promoted:No' [{datetime.datetime.now()}] ===========================")
                            option = {
                                'comp_name': 'Mathlibs',
                                'is_promoted': 'No',
                                'promo_status': ''
                            }
                            res, out_data = self.db.get_data_by_three_elements(option, from_date=from_date, to_date=to_date)
                            if res != "success":
                                raise NameError("DB failed to retrieve")
                            if bool(out_data):
                                for out in out_data:
                                    print(f'build_tag: {out[-1]}')
                                    if out[3] != '<a href=""></a>':
                                        build_url = re.findall(r'href=[\'"]?([^\'" >]+)', out[3])[0]
                                        build_url = build_url if build_url.endswith('/') else build_url + '/'
                                        print(f'build_url: {build_url}')
                                        if build_url.startswith('http') or build_url=='':
                                            promo_status = self.build.get_promoted_status_info(out, False)
                                            res = self.db.add_entry(out[-1], 'promo_status', promo_status)
                                            if res != "success":
                                                raise NameError("DB commit failed")
                                            print(f'Updated the promo_status for {out[-1]} --> {promo_status}')
                            else:
                                print('No empty promo_status entry in last 30 days.')
                    except Exception as e:
                        print(e)

                    try:
                        # Updating promo_status column for Mathlibs if empty for last 30days (promoted builds)
                        if comp_name == 'Mathlibs':
                            print(f"=============================== {comp_name} - 'promo_status - is_promoted:Yes' [{datetime.datetime.now()}] ===========================")
                            option = {
                                'comp_name': 'Mathlibs',
                                'is_promoted': 'Yes',
                                'promo_status': ''
                            }
                            res, out_data = self.db.get_data_by_three_elements(option, from_date=from_date, to_date=to_date)
                            if res != "success":
                                raise NameError("DB failed to retrieve")
                            if bool(out_data):
                                for out in out_data:
                                    print(f'build_tag: {out[-1]}')
                                    if out[3] != '<a href=""></a>':
                                        build_url = re.findall(r'href=[\'"]?([^\'" >]+)', out[3])[0]
                                        build_url = build_url if build_url.endswith('/') else build_url + '/'
                                        print(f'build_url: {build_url}')
                                        if build_url.startswith('http') or build_url=='':
                                            promo_status = self.build.get_promoted_status_info(out, False)
                                            res = self.db.add_entry(out[-1], 'promo_status', promo_status)
                                            if res != "success":
                                                raise NameError("DB commit failed")
                                            print(f"Updated the promo_status with 'False' for {out[-1]} --> {promo_status}")
                                    option = {
                                        'comp_name': 'Mathlibs',
                                        'is_promoted': 'Yes',
                                        'build_tag': out[-1]
                                    }
                                    res, out_data = self.db.get_data_by_three_elements(option, from_date=from_date, to_date=to_date)
                                    if res != "success":
                                        raise NameError("DB failed to retrieve")
                                    if bool(out_data):
                                        for out in out_data:
                                            if out[3] != '<a href=""></a>':
                                                build_url = re.findall(r'href=[\'"]?([^\'" >]+)', out[3])[0]
                                                build_url = build_url if build_url.endswith('/') else build_url + '/'
                                                print(f'build_url: {build_url}')
                                                if build_url.startswith('http') or build_url=='':
                                                    promo_status2 = self.build.get_promoted_status_info(out, True)
                                                    res2 = self.db.add_entry(out[-1], 'promo_status', promo_status2)
                                                    if res2 != "success":
                                                        raise NameError("DB commit failed")
                                                    print(f"Updated the promo_status with 'True' for {out[-1]} --> {promo_status2}")
                            else:
                                print('No empty promo_status entry in last 30 days.')
                    except Exception as e:
                        print(e)

                    try:
                        if comp_name == 'Release-Staging':
                            # Updating release_commit column for all components if empty for last 30days
                            print(f"=============================== {comp_name} - 'release_commit' [{datetime.datetime.now()}] ===========================")
                            option = {
                                'comp_name': comp_name,
                                'release_commit': ''
                            }
                            res, out_data = self.db.get_data_by_two_elements(option, from_date=from_date, to_date=to_date)
                            if res != "success":
                                raise NameError("DB failed to retrieve")
                            if bool(out_data):
                                for out in out_data:
                                    print(f'build_tag: {out[-1]}')
                                    if out[3] != '<a href=""></a>':
                                        build_url = re.findall(r'href=[\'"]?([^\'" >]+)', out[3])[0]
                                        build_url = build_url if build_url.endswith('/') else build_url + '/'
                                        print(f'build_url: {build_url}')
                                        if build_url.startswith('http') or build_url=='':
                                            release_commit = self.build.get_commit_diff_for_release_stg(out[13], out[15])
                                            res2 = self.db.add_entry(out[-1], 'release_commit', release_commit)
                                            if res2 != "success":
                                                raise NameError("DB commit failed")
                                            print(f'Updated the release_commit for {out[-1]} --> {release_commit}')
                            else:
                                print('No empty release_commit entry in last 30 days.')
                    except Exception as e:
                        print(e)
                except Exception as e:
                    print(e)
            else:
                continue
            

if __name__ == "__main__":
    ucd = UpdateCommitDetails()
    ucd.update_commit_if_empty()
