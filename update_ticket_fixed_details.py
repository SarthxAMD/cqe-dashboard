# Author      : Lenine Ajagappane <Lenine.Ajagappane@amd.com>
# Description : Script to update ticket_fixed details in DB if empty

import argparse
import datetime
import dateutil.relativedelta as rd
import re
from dashboard import Dashboard
from database import Database
from job_utils import JobUtils


class UpdateTicketFixedDetails:

    def __init__(self):
        self.build = JobUtils()
        self.dashboard = Dashboard()
        self.db = Database()

    def update_ticket_fixed_if_empty(self, component):
        to_date = datetime.datetime.now()
        from_date = to_date + rd.relativedelta(months = -1)
        to_date = to_date.date()
        from_date = from_date.date()
        component_list = self.dashboard.comp_names if component == 'all' else [component]
        for comp_name in component_list:
            try:
                # Updating ticket_fixed column for all components if empty for last 30days
                print(f"=============================== {comp_name} - 'ticket_fixed' [{datetime.datetime.now()}] ===========================")
                option = {
                    'comp_name': comp_name,
                    'ticket_fixed': ''
                }
                res, out_data = self.db.get_data_by_two_elements(option, from_date=from_date, to_date=to_date)
                if res != "success":
                    raise NameError("DB failed to retrieve")
                if bool(out_data):
                    for out in out_data:
                        print(f'build_tag: {out[-1]}')
                        if comp_name not in list(self.build.gerrit_projects):
                            ticket_str = 'Not Supported'
                        elif 'Win' in out[0]:
                            ticket_str = 'Not Supported'
                        elif 'Regular Staging' not in out[1]:
                            ticket_str = 'NA'
                        else:
                            last_promoted_build = self.dashboard.get_last_promoted_build(self.db, out[0])
                            print(f'Last_promoted_build: {last_promoted_build}')
                            last_promo_commit = ''
                            if 'Compiler' in comp_name:
                                build_no = re.search('.*/(\d+)/?$', last_promoted_build).group(1)
                                build_tag = f"{comp_name.split('-')[0].lower()}_{build_no}"
                                print(f'Last promoted build_tag: {build_tag}')
                                res, out_data = self.db.get_data_by_element('build_tag', build_tag)
                                if res != "success":
                                    raise NameError("DB failed to retrieve")
                                last_promo_commit = out_data[0][13]
                                print(f'last_promo_commit: {last_promo_commit}')
                            ticket_str = self.build.get_ticket_info_from_gitlog(out, last_promoted_build, last_promo_commit)
                        if ticket_str != '':
                            self.update_entry_in_db(out, ticket_str)
                else:
                    print('No empty ticket_fixed entry in last 30 days.')
            except Exception as e:
                print(e)

    def update_entry_in_db(self, out, ticket_str):
        res = self.db.add_entry(out[-1], 'ticket_fixed', ticket_str)
        if res != "success":
            raise NameError("DB commit failed")
        print(f'Updated the ticket_fixed for {out[-1]} --> {ticket_str}')


if __name__ == "__main__":
    utfd = UpdateTicketFixedDetails()
    parser = argparse.ArgumentParser(description="AutoRerun Tool")
    parser._action_groups.pop()
    optional = parser.add_argument_group('Optional arguments')
    optional.add_argument("--component", default='all', help="Component name")
    args = parser.parse_args()
    utfd.update_ticket_fixed_if_empty(args.component)
