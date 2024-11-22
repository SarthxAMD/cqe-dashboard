# Author      : Lenine Ajagappane <Lenine.Ajagappane@amd.com>
# Description : A Data init class.


class Data:

    def __init__(self, build_tag, comp_name, release_sub_comp, stg_type, build_url, request_date, start_date, code_date, end_date,
                 status, blocker_tick, is_promoted, promoted_main_build, details_report, remarks, commit_info,
                 ticket_fixed, base_commit, promo_details, promo_status, cp_patches, release_commit):
        self.comp_name = comp_name                          # DB index - 0
        self.stg_type = stg_type                            # DB index - 1
        self.start_date = start_date                        # DB index - 2
        self.build_url = build_url                          # DB index - 3
        self.request_date = request_date                    # DB index - 4
        self.code_date = code_date                          # DB index - 5
        self.end_date = end_date                            # DB index - 6
        self.status = status                                # DB index - 7
        self.blocker_tick = blocker_tick                    # DB index - 8
        self.is_promoted = is_promoted                      # DB index - 9
        self.promoted_main_build = promoted_main_build      # DB index - 10
        self.details_report = details_report                # DB index - 11
        self.remarks = remarks                              # DB index - 12
        self.commit_info = commit_info                      # DB index - 13
        self.ticket_fixed = ticket_fixed                    # DB index - 14
        self.base_commit = base_commit                      # DB index - 15
        self.promo_details = promo_details                  # DB index - 16
        self.promo_status = promo_status                    # DB index - 17
        self.release_sub_comp = release_sub_comp            # DB index - 18
        self.cp_patches = cp_patches                        # DB index - 19
        self.release_commit = release_commit                # DB index - 20
        self.build_tag = build_tag                          # DB index - 21
