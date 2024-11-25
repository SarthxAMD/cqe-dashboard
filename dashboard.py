# Author      : Lenine Ajagappane <Lenine.Ajagappane@amd.com>
# Description : Main App class which generate Dashboard using streamlit & sqlite.

from data import Data
from database import Database
import pandas as pd
import os
import re
import streamlit as st
from streamlit_theme import st_theme
import datetime
from threading import Thread
from streamlit.runtime.scriptrunner import add_script_run_ctx
import dateutil.relativedelta as rd
from job_utils import JobUtils
from localStyles import sticky_style,sticky_style_dark
from template import StyleTemplate
from streamlit_navigation_bar import st_navbar
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader


class Dashboard:

    comp_to_jira = {
        'Compiler-ROCm':'stg_cpl_',
        'Compiler-GFX-Linux':'stg_cpl_gfx_',
        'Compiler-GFX-Win':'stg_cpl_gfx_win_',
        'Debugger':'stg_debugger_',
        'HIP-ROCm':'stg_hip_',
        'LRT-GFX-Linux':'stg_hip_gfx_',
        'LRT-GFX-Win':'stg_hip_gfx_win_',
        'Mathlibs':'stg_mathlibs_',
        'Mathlibs-Win':'stg_mathlibs_win_',
        'MIOpen':'stg_miopen_',
        'Profiler':'stg_profiler_',
        'RCCL':'stg_rccl_',
        'ROCr':'stg_rocr_',
        'Release-Staging':'stg_release_'
    }
    link_config = {
        'Staging Build URL': st.column_config.LinkColumn(),
        'Promoted Mainline Build URL': st.column_config.LinkColumn(),
        'Detailed Report URL': st.column_config.LinkColumn(),
        'Issues Found': st.column_config.LinkColumn(),
        'Tickets Fixed': st.column_config.LinkColumn()
    }
    header_to_db = {
        'Build Tag':'build_tag',
        'Component':'comp_name',
        'Staging Type':'stg_type',
        'Staging Build URL':'build_url',
        'Planned/Requested Date':'request_date',
        'Cycle Start Date':'start_date',
        'Code-base date':'code_date',
        'Cycle End/ETA':'end_date',
        'Staging Verdict':'status',
        'Issues Found':'blocker_tick',
        'Build Promoted':'is_promoted',
        'Promoted Mainline Build URL':'promoted_main_build',
        'Detailed Report URL':'details_report',
        'Remarks':'remarks',
        'Commit Info':'commit_info',            # Staging build commit details
        'Tickets Fixed':'ticket_fixed',         # Ticket details fetched from git log of staging build & last promoted staging commit
        'Base Commit Info':'base_commit',       # Base build commit details
        'Promoted Details':'promo_details',     # Mainline promoted build commit details
        'Promoted Status':'promo_status',       # Mainline promoted commit status
        'Sub Components':'release_sub_comp',    # Applicable for Release staging
        'Cherrypick Patches':'cp_patches',      # Cherry-pick patches used in Staging build
        'Release Commit Info':'release_commit'  # Release staging commit diff saved here
    }
    table_header = ('Component', 'Staging Type', 'Cycle Start Date', 'Staging Build URL', 'Planned/Requested Date',
                    'Codebase Date', 'Cycle End/ETA', 'Staging Verdict', 'Issues Found', 'Build Promoted',
                    'Promoted Mainline Build URL', 'Detailed Report URL', 'Remarks', 'Commit Info', 'Tickets Fixed',
                    'Base Commit Info', 'Promoted Details', 'Promoted Status', 'Sub Components', 'Cherrypick Patches',
                    'Release Commit Info', 'Build Tag')
    db_entry = ('comp_name', 'stg_type', 'start_date', 'build_url', 'request_date', 'code_date', 'end_date',
                'status', 'blocker_tick', 'is_promoted', 'promoted_main_build', 'details_report', 'remarks',
                'commit_info', 'ticket_fixed', 'base_commit', 'promo_details', 'promo_status', 'release_sub_comp', 'cp_patches',
                'release_commit', 'build_tag')
    comp_names = ('Compiler-ROCm', 'Compiler-GFX-Linux', 'Compiler-GFX-Win', 'Debugger', 'HIP-ROCm', 'LRT-GFX-Linux',
                  'LRT-GFX-Win', 'Mathlibs', 'Mathlibs-Win', 'MIOpen', 'Profiler', 'RCCL', 'ROCr', 'Release-Staging')
    release_sub_comps = ['Compiler', 'HIP', 'Debugger', 'Profiler', 'ROCr', 'Mathlibs', 'MIGraphX', 'MIOpen', 'RCCL',
                         'ROCm-SMI', 'RVS', 'Build-infra', 'Packaging', 'Others']

    def __init__(self):
        template = StyleTemplate()
        template.set_page_config()
        config_file = os.path.join(os.path.dirname(__file__), 'config.yaml')
        with open(config_file) as f:
            self.login_config = yaml.load(f,Loader=SafeLoader)
        #page_header = ['Component Staging', 'Full Summary', 'In-Progress Staging', 'Promoted Builds', 'Admin Page']
        page_header = ['Component Staging', 'Full Summary', 'Promoted Builds', 'Admin Page', 'Staging Schedule', 'Build', 'Test']
        self.page = st_navbar(page_header,
                            logo_path=template.nav_logo_path,
                            selected='Component Staging',
                            logo_page='Component Staging',
                            styles=template.nav_styles,
                            options=template.nav_options,)
        self.build = JobUtils()
        self.themeMode=st_theme()
        # initially st_theme() returns None
        if self.themeMode:
            self.themeMode = self.themeMode['base']
        else:
            self.themeMode = "light"

    def main(self):
        stg_type = ('Regular Staging', 'Mainline Cherry-pick', 'Staging Cherry-pick', 'Release Cherry-pick', 'Private/Special Branch Staging')
        verdict_opt = ('GO', 'CONDITIONAL-GO', 'NO-GO', 'ABORTED', 'NOT-STARTED', 'NOT-PLANNED', 'IN-PROGRESS', 'OTHERS')
        db = Database()
        db.create_table()
        db_size = db.db_size()
        authenticator = stauth.Authenticate(
            self.login_config['credentials'],
            self.login_config['cookie']['name'],
            self.login_config['cookie']['key'],
            self.login_config['cookie']['expiry_days'],
        )
        #st.write('<style>div.block-container{padding-top:1vh;}</style>', unsafe_allow_html=True)
        #st.header('CQE Staging Dashboard')
        #tab1, tab2, tab3, tab4, tab5 = st.tabs(page_header)
        # Component-wise Data
        if self.page == "Component Staging":
        #with tab1:
            #st.subheader("Component details", divider='rainbow')
            option = {}
            if db_size > 0:
                left_column, right_column = st.columns(2)
                with left_column:
                    option['comp_name'] = st.selectbox('**Select Component**', self.comp_names)
                    stg_type_inp = self.generate_new_stg_type(option['comp_name'], stg_type)
                with right_column:
                    to_date = datetime.datetime.now()
                    from_date = to_date + rd.relativedelta(months = -1)
                    to_date=to_date.date()
                    from_date=from_date.date()
                    modification_container = st.container()
                    filters={
                        'comp_name':option['comp_name']
                    }
                    columns_vals={
                        'Staging Type':stg_type_inp,
                        'Staging Verdict':verdict_opt,
                        'Build Promoted':["Yes","No"]
                    }
                    with modification_container:
                        column_list=['Staging Type', 'Cycle Start Date', 'Staging Build URL', 'Cycle End/ETA', 'Staging Verdict', 'Build Promoted', 'Tickets Fixed',
                                     'Promoted Mainline Build URL', 'Detailed Report URL', 'Cherrypick Patches', 'Remarks']
                        to_filter_columns = st.multiselect("**Filter On**", column_list)
                for column in to_filter_columns:
                    right, left = st.columns((20, 1))
                    left.write("⤶")
                    # immutable columns
                    if column in ['Staging Type', 'Staging Verdict', 'Build Promoted']:
                        temp=right.multiselect(f"Values for {column}",columns_vals[column])
                        if len(temp)>0:
                            filters[self.header_to_db[column]]=temp
                    # substring matching columns
                    elif column in ['Staging Build URL', 'Tickets Fixed', 'Promoted Mainline Build URL', 'Detailed Report URL', 'Cherrypick Patches', 'Remarks']:
                        temp=right.text_input(f"Substring in {column}")
                        if temp!="":
                            filters[self.header_to_db[column]]=temp
                    # date
                    elif column in ['Cycle Start Date', 'Cycle End/ETA']:
                        temp=list(right.date_input(f"**{column} Range** 📅", (from_date, to_date), key=f"{column}_filter"))
                        if len(temp)==1:
                            temp.append(temp[0])
                        filters[self.header_to_db[column]]=temp
                if 'end_date' not in filters and 'start_date' not in filters:
                    filters['start_date']=[from_date,to_date]
                st.caption("By default, last 30 days of data will be shown below. For more data, please use 'Cycle Start Date' filter option.")
                try:
                    res, out_data = db.get_data_by_filters(filters)
                    if res!='success':
                        raise NameError("DB retrieve failed..")
                    self.display_df(out_data,self.table_header,option['comp_name'],'Component Staging')
                    self.print_build_scheduler_info(option['comp_name'])
                except Exception as e:
                    st.warning(e)
                    st.warning('Something went wrong! Try Again.', icon="⚠️")
            else:
                st.info('Database is Empty.', icon="ℹ️")
        # Full Summary
        if self.page == 'Full Summary':
        #with tab2:
            #st.subheader("Full Summary", divider='rainbow')
            st.caption('Last 10 entries of each components are listed here.')
            if self.themeMode=="light":
                st.markdown(f'''<a href=#Compiler-ROCm_summary><button style="{sticky_style}">&#8593;</button></a>''',unsafe_allow_html=True)
            else:
                st.markdown(f'''<a href=#Compiler-ROCm_summary><button style="{sticky_style_dark}">&#8593;</button></a>''',unsafe_allow_html=True)
            if db_size > 0:
                buttons = []
                for comp in self.comp_names:
                    if self.themeMode=="light":
                        buttons.append(f'''<a href=#{comp}_summary><button style="background-color:#E8E8E8; border:1px solid #BEE1E2; font-size:12px; margin:2px 1px; cursor:pointer; padding: 5px 24px; border-radius:4px; width:165px;">{comp}</button></a>''')
                    else:
                        buttons.append(f'''<a href=#{comp}_summary><button style="background-color:rgb(19, 23, 32); border:1px solid #BEE1E2; font-size:12px; margin:2px 1px; cursor:pointer; padding: 5px 24px; border-radius:4px; width:165px;">{comp}</button></a>''')
                st.markdown(''.join(buttons), unsafe_allow_html=True)
                for comp in self.comp_names:
                    st.markdown("")
                    st.subheader(comp,anchor=f"{comp}_summary")
                    try:
                        res, out_data = db.get_data_by_component_limit(comp)
                        if res!="success":
                            raise NameError("DB failed to retrieve")
                        latest_promoted_build = self.get_last_promoted_build(db, comp)
                        if latest_promoted_build:
                            hyperlink_text=self.link_convert("staging",latest_promoted_build)
                            st.markdown(f"Last promoted build: [{hyperlink_text}](%s)" % latest_promoted_build)
                        else:
                            st.markdown(f"Last promoted build: NA")
                        self.display_df(out_data,self.table_header,comp,'full-summary')
                    except Exception as e:
                        st.warning(f"Something went wrong Error\:{e}", icon="⚠️")
            else:
                st.info('Database is Empty.', icon="ℹ️")

        # In-progress Staging Summary
        if self.page == 'In-Progress Staging':
        #with tab3:
            #st.subheader("In-progress staging cycle details", divider='rainbow')
            st.caption('Showing current in-progress cycle details of all components.')
            if self.themeMode=="light":
                st.markdown(f'''<a href=#in-progress-staging-cycle-details><button style="{sticky_style}">&#8593;</button></a>''',unsafe_allow_html=True)
            else:
                st.markdown(f'''<a href=#in-progress-staging-cycle-details><button style="{sticky_style_dark}">&#8593;</button></a>''',unsafe_allow_html=True)
            if db_size > 0:
                buttons = []
                for comp in self.comp_names:
                    try:
                        option = {
                            'comp_name': comp,
                            'status': 'IN-PROGRESS'
                        }
                        res, out_data = db.get_data_by_two_elements(option)
                        if res!="success":
                            raise NameError("DB failed to retrieve")
                        if out_data:
                            st.subheader(comp)
                            self.display_df(out_data,self.table_header,option['comp_name'],'in-progress')
                    except Exception as e:
                        st.warning(f"Something went wrong Error\:{e}", icon="⚠️")
            else:
                st.info('Database is Empty.', icon="ℹ️")

        # Promoted builds details for all components
        if self.page == 'Promoted Builds':
        #with tab4:
            #st.subheader("Promoted Builds details", divider='rainbow')
            st.caption('Last 10 entries of promoted staging build details of each components are listed here.')
            comp_names_promoted=[v for v in self.comp_names if v!="Release-Staging"]
            if self.themeMode=="light":
                st.markdown(f'''<a href=#Compiler-ROCm_promoted><button style="{sticky_style}">&#8593;</button></a>''',unsafe_allow_html=True)
            else:
                st.markdown(f'''<a href=#Compiler-ROCm_promoted><button style="{sticky_style_dark}">&#8593;</button></a>''',unsafe_allow_html=True)
            if db_size > 0:
                buttons = []
                for comp in comp_names_promoted:
                    if self.themeMode=="light":
                        buttons.append(f'''<a href=#{comp}_promoted><button style="background-color:#E8E8E8; border:1px solid #BEE1E2; font-size:12px; margin:2px 1px; cursor:pointer; padding: 5px 24px; border-radius:4px; width:165px;">{comp}</button></a>''')
                    else:
                        buttons.append(f'''<a href=#{comp}_promoted><button style="background-color:rgb(19, 23, 32); border:1px solid #BEE1E2; font-size:12px; margin:2px 1px; cursor:pointer; padding: 5px 24px; border-radius:4px; width:165px;">{comp}</button></a>''')
                st.markdown(''.join(buttons), unsafe_allow_html=True)
                for comp in comp_names_promoted:
                    try:
                        option = {
                            'comp_name': comp,
                            'is_promoted': 'Yes'
                        }
                        res, out_data = db.get_data_by_two_elements(option)
                        if res!="success":
                            raise NameError("DB failed to retrieve")
                        st.subheader(comp,anchor=f"{comp}_promoted")
                        if out_data:
                            out_data=[ele for ele in out_data if "Regular Staging" in ele[1]]
                        self.display_df(out_data,self.table_header,option['comp_name'],'promoted-builds')
                    except Exception as e:
                        st.warning(f"Something went wrong Error\:{e}", icon="⚠️")
            else:
                st.info('Database is Empty.', icon="ℹ️")

        # Admin Page
        if self.page == 'Admin Page':
        #with tab5:
            #st.subheader("Admin Page", divider='rainbow')
            name, authentication_status, username = authenticator.login()
            if authentication_status==True:
                authenticator.logout()
                st.caption('To add new entry, modify or delete the existing entry in DB.')
                if 'newEntry' not in st.session_state:
                    st.session_state.newEntry=False
                if 'modify' not in st.session_state:
                    st.session_state.modify=False
                if 'isSaved' not in st.session_state:
                    st.session_state.isSaved=False
                def clickButton(k):
                    if k=="newEntry":
                        if st.session_state.modify:
                            st.session_state.modify=not st.session_state.modify
                        st.session_state.newEntry=not st.session_state.newEntry
                    elif k=="modify":
                        if st.session_state.newEntry:
                            st.session_state.newEntry=not st.session_state.newEntry
                        st.session_state.modify=not st.session_state.modify
                if not st.session_state.newEntry:
                    st.button("Add new entry", on_click=clickButton, args=['newEntry'])
                if not st.session_state.modify:
                    st.button("Modify/Delete", on_click=clickButton, args=['modify'])
                if st.session_state.newEntry:
                    st.write('''<p style="font-size:20px;"><b>Add new entry</b></p>''', unsafe_allow_html=True)
                    build_tag = ''
                    input = {}
                    input['comp_name'] = st.selectbox('**Select Staging Component**', ('--select--',) + self.comp_names)
                    input['release_sub_comp'] = ''
                    if input['comp_name'] == 'Release-Staging':
                        input['release_sub_comp'] = st.multiselect("Enter Release Sub-components", self.release_sub_comps, self.release_sub_comps[0])
                    stg_type_inp = self.generate_new_stg_type(input['comp_name'], stg_type)
                    input['stg_type'] = st.selectbox('**Select Staging Type**', ('--select--',) + stg_type_inp)
                    input['build_url'] = st.text_input('**Staging Build URL** 🔗', '')
                    build_url_inp = input['build_url']
                    input['request_date'] = st.date_input('**Requested Date** 📅', "today")
                    input['start_date'] = st.date_input('**Cycle Start Date** 📅', "today")
                    input['code_date'] = st.date_input('**Codebase Date** 📅', "today")
                    input['end_date'] = st.date_input('**Cycle End/ETA** 📅', "today")
                    input['status'] = st.selectbox('**Staging Verdict**', ('--select--',) + verdict_opt)
                    input['blocker_tick'] = st.text_area('**Issues Found**', '')
                    input['is_promoted'] = st.selectbox('**Build Promoted (Yes/No)**', ('--select--', 'Yes', 'No'))
                    input['mainline_url'] = st.text_input('**Promoted Mainline Build URL** 🔗', '')
                    input['details_report'] = st.text_input('**Detailed Report URL** 🔗', '')
                    input['remarks'] = st.text_area('**Remarks**', '')
                    self.check_valid_url_inputs(input['build_url'])
                    self.check_valid_selectbox_inputs(input)
                    st.markdown("####")
                    if st.button('**Save** ⏬', use_container_width=True):
                        try:
                            # Stop DB upload if valid input's are not provided
                            status = self.check_valid_url_inputs(input['build_url'])
                            if not status:
                                st.error('Provide valid build URL..', icon="⛔")
                                return
                            status = self.check_valid_selectbox_inputs(input)
                            if not status:
                                st.error('Select valid input from dropdown list..', icon="⛔")
                                return
                            build_no = re.search('.*/(\d+)/?$', input['build_url']).group(1)
                            build_tag = f"{input['comp_name'].lower()}_{build_no}"
                            if 'Weekly' in input['stg_type']:
                                build_tag = f"{input['comp_name'].lower()}_{build_no}_weekly"
                            input['build_url'] = f"""<a href="{input['build_url']}">{input['build_url']}</a>"""
                            input['mainline_url'] = f"""<a href="{input['mainline_url']}">{input['mainline_url']}</a>"""
                            input['details_report'] = f"""<a href="{input['details_report']}">{input['details_report']}</a>"""
                            input['commit_info'] = ''
                            input['ticket_fixed'] = ''
                            input['base_commit'] = ''
                            input['promo_details'] = ''
                            input['promo_status'] = ''
                            input['cp_patches'] = ''
                            input['release_commit'] = ''
                            if input['comp_name'] in self.build.comp_manifest_map.keys():
                                input['commit_info'] = self.build.get_commit_from_build(build_url_inp, input['comp_name'])
                                input['base_commit'] = self.build.get_commit_from_base_build(build_url_inp, input['comp_name'])
                                input['cp_patches'] = self.build.get_cherrypick_patches_from_build(build_url_inp)
                            if input['comp_name'] == 'Mathlibs':
                                input['promo_status'] = self.upload_commit_status_info(db, False, build_tag, list(input.values()))
                            if input['comp_name'] == 'Release-Staging':
                                input['release_commit'] = self.build.get_commit_diff_for_release_stg(input['commit_info'], input['base_commit'])
                            st.markdown("####")
                            data = Data(*[build_tag] + list(input.values()))
                            res = db.insert_data(data)
                            if input['comp_name'] in self.build.comp_manifest_map.keys() and input['comp_name'] != 'Release-Staging':
                                t = Thread(target=self.fetch_ticket_info_from_gitlog, args=(build_tag, db))
                                add_script_run_ctx(t)
                                t.start()
                            if res != "success":
                                raise NameError("DB insert failed..")
                            st.session_state.isSaved=True
                            st.rerun()
                        except UnboundLocalError as e:
                            st.warning(e)
                            st.warning('Check build URL input.', icon="⚠️")
                        except AttributeError as e:
                            st.warning(e)
                            st.warning('Check build URL input.', icon="⚠️")
                        except Exception as e:
                            st.warning(e)
                            st.warning('Something went wrong! Try Again.', icon="⚠️")
                    st.markdown("####")
                    st.info(f"Available data in Database: {db_size}", icon="💾")
                    if "isSaved" in st.session_state:
                        if st.session_state.isSaved:
                            st.toast("DB Insert Successful",icon="✅")
                            st.session_state.isSaved=False
                if st.session_state.modify:
                    st.write('''<p style="font-size:20px;"><b>Modify/Delete</b></p>''', unsafe_allow_html=True)
                    df_column_config={
                        'Cycle End/ETA': st.column_config.DateColumn(format="YYYY-MM-DD"),
                        'Staging Verdict': st.column_config.SelectboxColumn(required=True,options=verdict_opt),
                        'Build Promoted': st.column_config.SelectboxColumn(required=True,options=['Yes','No'])
                    }
                    disabledList=['Build Tag','Component','Staging Type','Staging Build URL','Planned/Requested Date','Cycle Start Date','Codebase Date']
                    if db_size > 0:
                        try:
                            option = st.selectbox('**Select Component**', self.comp_names, key="modifySelect")
                            to_date = datetime.datetime.now()  
                            from_date = to_date + rd.relativedelta(months = -1)
                            dateRange = st.date_input(
                                '**Date Range** 📅',
                                (from_date, to_date),
                                key='modify_date_key'
                            )
                            if len(dateRange)==1:
                                to_date = from_date = dateRange[0]
                            else:
                                from_date = dateRange[0]
                                to_date = dateRange[1]
                            st.markdown("#####")
                            res, out_data = db.get_data_by_element('comp_name', option, from_date, to_date)
                            if res!='success':
                                raise NameError("DB retrieve failed..")
                            df = pd.DataFrame(list(out_data), columns=self.table_header)
                            if option != 'Release-Staging':
                                df.pop('Sub Components')
                            df['Cycle End/ETA']=pd.to_datetime(df['Cycle End/ETA'])
                            for index,row in df.iterrows():
                                df.at[index,'Staging Build URL']=row['Staging Build URL'].split("\"")[1]
                                df.at[index,'Promoted Mainline Build URL']=row['Promoted Mainline Build URL'].split("\"")[1]
                                df.at[index,'Detailed Report URL']=row['Detailed Report URL'].split("\"")[1]
                            result=st.data_editor(df,column_config=df_column_config,disabled=disabledList,num_rows='dynamic',hide_index=True)
                            if st.button('**Save** ⏬', use_container_width=True):
                                result['Cycle End/ETA']=result['Cycle End/ETA'].astype(str)
                                df['Cycle End/ETA']=df['Cycle End/ETA'].astype(str)
                                self.modify_db(result,df,db)
                                st.session_state.isSaved=True
                                st.rerun()
                            st.markdown('##')
                            if "isSaved" in st.session_state:
                                if st.session_state.isSaved:
                                    st.toast("Changes saved",icon="✅")
                                    st.session_state.isSaved=False
                            self.upload_promoted_commit_info(db)
                            self.upload_commit_status_info(db)
                        except Exception as e:
                            st.warning(f"Something went wrong Error\:{e}", icon="⚠️")
                    else:
                        st.info('Database is Empty.', icon="ℹ️") 
            elif authentication_status is False:
                st.error('Username/password is incorrect')
            elif authentication_status is None:
                st.warning('Please enter your username and password')

        if self.page == 'Staging Schedule':
            comp_names = ['Compiler-ROCm', 'Compiler-GFX-Linux', 'HIP-ROCm', 'LRT-GFX-Linux', 'Mathlibs', 'MIOpen', 'RCCL',
                          'Debugger', 'Profiler', 'ROCr']
            for comp in comp_names:
                st.markdown(f"**{comp}:**")
                self.print_build_scheduler_info(comp, True)

    def print_build_scheduler_info(self, comp_name, skip_print=False):
        if comp_name != 'Release-Staging' and 'Win' not in comp_name:
            if not skip_print:
                st.markdown("**Staging Schedule:**")
            table_header_list = ['Staging Type', 'Build Start time (EST)', 'Staging Start time (EST)', 'Cycle ETA (EST)']
            list_data = [['1', '2', '3']]
            comp_map = {
                'Compiler-ROCm': [
                    ['Compiler Daily Cycle 1', 'Wednesday 09:30 PM', 'Friday 07:30 AM', 'Tuesday 07:30 AM'],
                    ['Compiler Daily Cycle 2', 'Saturday 09:30 PM', 'Monday 07:30 AM', 'Thursday 07:30 AM'],
                    ['Compiler Weekly', 'Choose Daily build', 'Friday 07:30 AM', 'Next Thursday 07:30 AM'],
                    ['Mainline Cherry-pick', 'On-demand', 'Triggered after build completed', 'After 2 days']
                ],
                'Compiler-GFX-Linux': [
                    ['Compiler Daily Cycle 1', 'Wednesday 09:30 PM', 'Friday 07:30 AM', 'Tuesday 07:30 AM'],
                    ['Compiler Daily Cycle 2', 'Saturday 09:30 PM', 'Monday 07:30 AM', 'Thursday 07:30 AM'],
                    ['Compiler Weekly', 'Choose Daily build', 'Friday 07:30 AM', 'Next Thursday 07:30 AM'],
                    ['Mainline Cherry-pick', 'On-demand', 'Triggered after build completed', 'After 2 days']
                ],
                'HIP-ROCm': [
                    ['HIP Daily Cycle 1', 'Friday 02:30 AM', 'Monday 02:30 AM', 'Wednesday 07:30 AM'],
                    ['HIP Daily Cycle 2', 'Monday 02:30 AM', 'Wednesday 02:30 AM', 'Friday 07:30 AM'],
                    ['HIP Daily Cycle 3', 'Wednesday 02:30 AM', 'Friday 02:30 AM', 'Monday 07:30 AM'],
                    ['HIP Weekly', 'Choose Daily build', 'Friday 02:30 AM', 'Thursday 07:30 AM'],
                    ['PSDB Stress Testing', 'Wednesday 02:30 AM', 'Friday 02:30 AM', 'Thursday 07:30 AM']
                ],
                'LRT-GFX-Linux': [
                    ['HIP Daily Cycle 1', 'Friday 02:30 AM', 'Monday 02:30 AM', 'Wednesday 07:30 AM'],
                    ['HIP Daily Cycle 2', 'Monday 02:30 AM', 'Wednesday 02:30 AM', 'Friday 07:30 AM'],
                    ['HIP Daily Cycle 3', 'Wednesday 02:30 AM', 'Friday 02:30 AM', 'Monday 07:30 AM'],
                    ['HIP Weekly', 'Choose Daily build', 'Friday 02:30 AM', 'Thursday 07:30 AM'],
                    ['PSDB Stress Testing', 'Wednesday 02:30 AM', 'Friday 02:30 AM', 'Thursday 07:30 AM']
                ],
                'Mathlibs': [
                    ['Mathlibs Cycle 1', 'Tuesday 11:00 AM', 'Wednesday 12:00 PM', 'Friday 07:30 AM'],
                    ['Mathlibs Cycle 2', 'Friday 11:00 AM', 'Saturday 2:00 PM', 'Tuesday 07:30 AM']
                ],
                'MIOpen': [
                    ['MIOpen Cycle', 'On-demand', 'Triggered after build completed', 'After 3 days']
                ],
                'Debugger': [
                    ['Debugger Cycle', 'Sunday 09:00 AM', 'Monday 10:00 AM', 'Wednesday 07:30 PM']
                ],
                'Profiler': [
                    ['Profiler Cycle', 'Sunday 09:00 AM', 'Monday 10:00 AM', 'Thursday 07:30 AM']
                ],
                'RCCL': [
                    ['RCCL Cycle', 'Friday 11:00 AM', 'Saturday 2:00 PM', 'Tuesday 07:30 AM']
                ],
                'ROCr': [
                    ['ROCr-Runtime Cycle 1', 'Monday 08:30 AM', 'Tuesday 02:30 PM', 'Wednesday 07:30 AM'],
                    ['ROCr-Runtime Cycle 2', 'Thursday 08:30 AM', 'Friday 02:30 PM', 'Tuesday 07:30 AM']
                ]
            }
            df = pd.DataFrame(list(comp_map[comp_name]), columns=table_header_list)
            temp_config = {
                'Staging Type': st.column_config.Column(width='medium'),
                'Build Start time (EST)': st.column_config.Column(width='medium'),
                'Staging Start time (EST)': st.column_config.Column(width='medium'),
                'Cycle ETA': st.column_config.Column(width='medium')
            }
            st.dataframe(df, column_config=temp_config, hide_index=True)

    def modify_db(self,result,df,db):
        # list of deleted 'Build Tag' rows
        deleted=[]
        # list of modified rows 
        modified=[]
        try:
            for index,row in df.iterrows():
                if not row['Build Tag'] in result['Build Tag'].tolist():
                    deleted.append(row['Build Tag'])
                    continue
                diff=row.compare(result.loc[result['Build Tag']==row['Build Tag']].iloc[0])
                if not diff.empty:
                    temp_dict={self.header_to_db['Build Tag']:row['Build Tag']}
                    for i,v in diff.iterrows():
                        if i=="Promoted Mainline Build URL" or i=="Detailed Report URL":
                            if not self.build.is_url(v.iloc[1]):
                                raise NameError("Invaid URL")
                            v.iloc[1]=f"""<a href="{v.iloc[1]}">{v.iloc[1]}</a>"""
                        temp_dict[self.header_to_db[i]]=v.iloc[1]
                    modified.append(temp_dict)
            res=db.update_db(deleted,modified)
            if res!="success":
                raise NameError("DB commit failed")
        except Exception as e:
            st.warning(f"Something went wrong Error\:{e}", icon="⚠️")

    def get_last_promoted_build(self, db, comp):
        option = {
            'comp_name': comp,
            'is_promoted': 'Yes'
        }
        _,last_promoted_build = db.get_data_by_two_elements(option)
        last_promoted_build = [ele for ele in last_promoted_build if "Regular Staging" in ele[1]]
        if last_promoted_build:
            last_promoted_build = last_promoted_build[0][3].split("\"")[1]
            last_promoted_build = last_promoted_build[:-1] if last_promoted_build[-1] == '/' else last_promoted_build
        return last_promoted_build

    def upload_promoted_commit_info(self, db):
        # Currently this feature is supported only for Mathlibs
        try:
            comp_name = 'Mathlibs'
            option = {
                'comp_name': comp_name,
                'is_promoted': 'Yes'
            }
            res, out_data = db.get_data_by_two_elements(option)
            if res != "success":
                raise NameError("DB failed to retrieve")
            for out in out_data:
                promo_commit = self.build.get_promoted_build_commits(out, comp_name)
                res2 = db.add_entry(out[-1], 'promo_details', promo_commit)
                if res2 != "success":
                    raise NameError("DB commit failed")
        except Exception as e:
            st.warning(f"Something went wrong Error\:{e}", icon="⚠️")

    def upload_commit_status_info(self, db, is_promo=True, build_tag='', input=[]):
        # Currently this feature is supported only for Mathlibs
        try:
            if not is_promo:
                option = {
                    'comp_name': input[0],
                    'build_tag': build_tag
                }
                return self.build.get_promoted_status_info(input, is_promo)
            else:
                option = {
                    'comp_name': 'Mathlibs',
                    'is_promoted': 'Yes'
                }
                res, out_data = db.get_data_by_two_elements(option)
                if res != "success":
                    raise NameError("DB failed to retrieve")
                for out in out_data:
                    diff_str = self.build.get_promoted_status_info(out, is_promo)
                    res2 = db.add_entry(out[-1], 'promo_status', diff_str)
                    if res2 != "success":
                        raise NameError("DB commit failed")
        except Exception as e:
            st.warning(f"Something went wrong Error\:{e}", icon="⚠️")

    def fetch_ticket_info_from_gitlog(self, build_tag, db):
        try:
            res, out_data = db.get_data_by_element('build_tag', build_tag)
            if res != "success":
                raise NameError("DB failed to retrieve")
            for out in out_data:
                if out[0] not in list(self.build.gerrit_projects):
                    ticket_str = 'Not Supported'
                elif 'Win' in out[0]:
                    ticket_str = 'Not Supported'
                elif 'Regular Staging' not in out[1]:
                    ticket_str = 'NA'
                else:
                    last_promoted_build = self.get_last_promoted_build(db, out[0])
                    ticket_str = self.build.get_ticket_info_from_gitlog(out, last_promoted_build)
                if ticket_str != '':
                    res2 = db.add_entry(out[-1], 'ticket_fixed', ticket_str)
                    if res2 != "success":
                        raise NameError("DB commit failed")
        except Exception as e:
            st.warning(f"Something went wrong Error\:{e}", icon="⚠️")

    def link_convert(self, type, val):
        if("http" in str(val)):
            val=str(val)
            if val[-1]=='/':
                val=val[:-1]
            if type=="staging":
                try:
                    if "rt" in val.split('-'):
                        return f"rt-win/{val.split('/')[-1]}"
                    elif re.search("rel.*component-staging",val):
                        return f"release-staging/{val.split('/')[-1]}"
                    elif "cpl" in val.split('-'):
                        return f"cpl-win/{val.split('/')[-1]}"
                    elif "afar" in val.split('-'):
                        return f"afar-profiler/{val.split('/')[-1]}"
                    elif "compute-psdb-no-npi" in val:
                        return f"compute-psdb/{val.split('/')[-1]}"
                    elif val.split('-')[-1]:
                        return val.split('-')[-1]
                except Exception as e:
                    st.warning(f"Something went wrong Error\:{e}", icon="⚠️") 
            elif type=="promoted":
                try:
                    if "compute-rocm-dkms-no-npi-hipclang" in val.split('/'):
                        return f"mainline/{val.split('/')[-1]}"
                    elif "rel" in val.split('-'):
                        return f"release/{val.split('/')[-1]}"
                except Exception as e:
                    st.warning(f"Something went wrong Error\:{e}", icon="⚠️")
        return val

    def generate_new_stg_type(self, comp_name, stg_type):
        if 'Compiler' in comp_name or 'HIP' in comp_name or 'LRT' in comp_name:
            new_type = []
            stg_type1 = tuple([s_type + ' - Daily' for s_type in stg_type])
            stg_type2 = tuple([s_type + ' - Weekly' for s_type in stg_type])
            a = [new_type.extend([i,j]) for i, j in zip(stg_type1, stg_type2)]
            if 'HIP' in comp_name or 'LRT' in comp_name:
                new_type.append('Catch2 Stress Testing')
            return tuple(new_type)
        elif 'Debugger' in comp_name or 'Profiler' in comp_name:
            stg_type = stg_type + ('AFAR',)
            stg_type = stg_type + ('ASAN',)
            return stg_type
        elif 'Release-Staging' in comp_name:
            stg_type = tuple([s_type for s_type in stg_type if s_type not in ('Regular Staging', 'Mainline cherry-pick', 'Staging cherry-pick', 'Private/Special branch staging')])
            return stg_type
        else:
            return stg_type

    def check_valid_selectbox_inputs(self, input={}):
        for key,val in input.items():
            if val == r'--select--':
                st.info(f"{key}: Select valid input from dropdown list.")
                return False
        return True

    def check_valid_url_inputs(self, inp):
        if inp.startswith('http') and bool(re.search('.*/(\d+)/?$', inp)):
            return True
        st.info('Provide valid build URL.')
        return False

    # preprocess data from db, format it and display it
    def display_df(self,out_data,table_header,comp,tab_name):
        out_data=[list(ele) for ele in out_data] 
        for i,v in enumerate(out_data):
            out_data[i].insert(0,i+1)
        table_header_list=list(table_header)
        table_header_list.insert(0,"Index")
        df = pd.DataFrame(list(out_data), columns=table_header_list)
        # remove columns from ui and perform a deep copy before to save information regarding commit info, promoted status, etc.
        og_df=df.copy()
        df.pop('Commit Info')
        df.pop('Base Commit Info')
        df.pop('Promoted Details')
        df.pop('Promoted Status')
        df.pop('Cherrypick Patches')
        df.pop('Release Commit Info')
        for index,row in df.iterrows():
            df.at[index,'Staging Build URL']=row['Staging Build URL'].split("\"")[1]
            df.at[index,'Promoted Mainline Build URL']=row['Promoted Mainline Build URL'].split("\"")[1]
            df.at[index,'Detailed Report URL']=row['Detailed Report URL'].split("\"")[1]
            # remove trailing / from url if present and extract build_no
            temp_build_no=str(df.at[index,'Staging Build URL'])[:-1].split('/')[-1] if str(df.at[index,'Staging Build URL'])[-1]=='/' else str(df.at[index,'Staging Build URL']).split('/')[-1]
            # inject component type and build no into url
            df.at[index,'Issues Found']=f"https://ontrack-internal.amd.com/issues/?filter=-4&jql=%22Build%20Where%20Found%22%20~%20%22{self.comp_to_jira[comp]+str(temp_build_no)}%22%20ORDER%20BY%20priority%20DESC"
            if str(df.at[index,'Tickets Fixed']) != '' and str(df.at[index,'Tickets Fixed']) != 'NA' and str(df.at[index,'Tickets Fixed']) != 'None' and str(df.at[index,'Tickets Fixed']) != 'Not Supported':
                tick_str = '%2C'.join(str(df.at[index,'Tickets Fixed']).split(','))
                df.at[index,'Tickets Fixed']=f"https://ontrack-internal.amd.com/issues/?jql=key%20in%20({tick_str})"
            else:
                df.at[index,'Tickets Fixed'] = str(df.at[index,'Tickets Fixed'])
        temp_link_config=dict(self.link_config)
        # format dataframe columns with links to hyperlinks
        temp_link_config['Commit Details']=st.column_config.CheckboxColumn()
        if tab_name == 'Component Staging':
            if comp == "Release-Staging":
                df.pop('Planned/Requested Date')
                df.pop('Codebase Date')
                df.pop('Staging Type')
                df.rename({'Promoted Mainline Build URL':'Promoted Release Build URL'},axis=1,inplace=True)
                df.insert(12,'Promoted Release Build URL',df.pop('Promoted Release Build URL'))
                temp_link_config['Promoted Release Build URL']=temp_link_config.pop('Promoted Mainline Build URL')
                temp_link_config['Sub Components'] = st.column_config.ListColumn(width='medium')
                df.insert(8,'Commit Details',pd.Series([False for _ in range(len(df))],dtype=bool),True)
                df.insert(9,'Tickets Fixed',df.pop('Tickets Fixed'))
                df.insert(10,'Remarks',df.pop('Remarks'))
                df.insert(2,'Sub Components',df.pop('Sub Components'))
            else:
                df.pop('Sub Components')
                df.insert(11,'Commit Details',pd.Series([False for _ in range(len(df))],dtype=bool),True)
                df.insert(12,'Tickets Fixed',df.pop('Tickets Fixed'))
                df.insert(14,'Planned/Requested Date',df.pop('Planned/Requested Date'))
                df.insert(14,'Codebase Date',df.pop('Codebase Date'))
        else:
            # if component type if release staging then remove some columns, rename promoted url column and reorder staging type column
            if comp == "Release-Staging":
                df.pop('Planned/Requested Date')
                df.pop('Codebase Date')
                df.pop('Staging Type')
                df.rename({'Promoted Mainline Build URL':'Promoted Release Build URL'},axis=1,inplace=True)
                df.insert(11,'Promoted Release Build URL',df.pop('Promoted Release Build URL'))
                temp_link_config['Promoted Release Build URL']=temp_link_config.pop('Promoted Mainline Build URL')
                temp_link_config['Sub Components'] = st.column_config.ListColumn(width='medium')
                df.insert(8,'Tickets Fixed',df.pop('Tickets Fixed'))
                df.insert(9,'Remarks',df.pop('Remarks'))
                df.insert(2,'Sub Components',df.pop('Sub Components'))
                #df.insert(df.shape[1]-1,'Staging Type',df.pop('Staging Type'))
            else:
                df.pop('Sub Components')
                df.insert(13,'Tickets Fixed',df.pop('Tickets Fixed'))
                df.insert(13,'Planned/Requested Date',df.pop('Planned/Requested Date'))
                df.insert(13,'Codebase Date',df.pop('Codebase Date'))
        styled_df=self.format_df(df,comp)
        if tab_name=='Component Staging':
            disabled_column_names=list(df.keys())
            disabled_column_names.remove('Commit Details')
            selected_rows=st.data_editor(styled_df,
                                       column_config=temp_link_config,
                                       disabled=disabled_column_names,
                                       hide_index=True)
            selected_rows=selected_rows.loc[selected_rows['Commit Details']==True]
            if len(selected_rows):
                # Toast message whenever user selects another row
                # st.toast(f"Scroll down to view detailed info")
                column_head = ['ProjectName','ProjectPath','BranchName','CommitId']
                if comp == "Mathlibs":
                    for i in selected_rows.index:
                        det_list=self.build.format_manifest_data(str(og_df.at[i,'Promoted Status']))
                        if bool(det_list):
                            column_head = ['Component', 'StagingCommit', 'StagingBranch', 'StagingRemoteName', 'StagingRequest?', 'Promoted?']
                            st.markdown(f"**Detailed Info for:** [{self.link_convert('staging',selected_rows.at[i,'Staging Build URL'])}]({selected_rows.at[i,'Staging Build URL']})")
                            detailed_df=pd.DataFrame(det_list,columns=column_head)
                            def highlight_bool(col):
                                if col=='Yes':
                                    return 'color: #20bd49'
                                elif col=='No':
                                    return 'color: red'
                            st.dataframe(detailed_df.style.applymap(highlight_bool,subset=["StagingRequest?","Promoted?"]),hide_index=True)
                elif comp == "Release-Staging":
                    for i in selected_rows.index:
                        det_list=self.build.format_manifest_data(str(og_df.at[i,'Release Commit Info']), skip_remote=True)
                        if bool(det_list):
                            st.markdown(f"**Detailed Info for:** [{self.link_convert('staging',selected_rows.at[i,'Staging Build URL'])}]({selected_rows.at[i,'Staging Build URL']})")
                            detailed_df=pd.DataFrame(det_list,columns=column_head)
                            st.dataframe(detailed_df,hide_index=True)
                else:
                    for i in selected_rows.index:
                        det_list=self.build.format_manifest_data(str(og_df.at[i,'Commit Info']), skip_remote=True)
                        st.markdown(f"**Detailed Info for:** [{self.link_convert('staging',selected_rows.at[i,'Staging Build URL'])}]({selected_rows.at[i,'Staging Build URL']})")
                        detailed_df=pd.DataFrame(det_list,columns=column_head)
                        st.dataframe(detailed_df,hide_index=True)
                if str(og_df.at[i,'Cherrypick Patches']) != '' and str(og_df.at[i,'Cherrypick Patches']) != 'None':
                    st.markdown(f"**Cherry-Pick patches for:** [{self.link_convert('staging',selected_rows.at[i,'Staging Build URL'])}]({selected_rows.at[i,'Staging Build URL']})")
                    for patch in og_df.at[i,'Cherrypick Patches'].split('\n'):
                        st.markdown(patch)
                st.markdown('')
        else:
            st.dataframe(styled_df,
                         column_config=temp_link_config,
                         hide_index=True)

    def format_df(self,df,comp):
        styledDf=df.style
        # need another function returning lambda as lambda only uses latest value of variable
        def lambdaFunc(val):
            return lambda x: val if "http" in x else ""
        def format_ticket_fixed(val):
            return lambda x: val if "http" in x else 'NA' if x == 'NA' else 'None' if x == 'None' else 'Not Supported' if x == 'Not Supported' else ''
        for i,row in df.iterrows():
            buildNo=str(row['Staging Build URL'])[:-1].split('/')[-1] if str(row['Staging Build URL'])[-1]=='/' else str(row['Staging Build URL']).split('/')[-1]
            styledDf._display_funcs[(i,df.columns.get_loc('Staging Build URL'))]=lambda x: self.link_convert("staging",x)
            if comp=='Release-Staging':
                styledDf._display_funcs[(i,df.columns.get_loc('Promoted Release Build URL'))]=lambda x: self.link_convert("promoted",x)
            else:    
                styledDf._display_funcs[(i,df.columns.get_loc('Promoted Mainline Build URL'))]=lambda x: self.link_convert("promoted",x)
            styledDf._display_funcs[(i,df.columns.get_loc('Detailed Report URL'))]=lambdaFunc(f"{buildNo}_Report")
            styledDf._display_funcs[(i,df.columns.get_loc('Issues Found'))]=lambdaFunc(f"{self.comp_to_jira[comp]+str(buildNo)}")
            styledDf._display_funcs[(i,df.columns.get_loc('Tickets Fixed'))] = format_ticket_fixed(f"{buildNo}_tickets")
            #styledDf._display_funcs[(i,df.columns.get_loc('Tickets Fixed'))]=lambdaFunc(f"{buildNo}_tickets")
        def format_column(val):
            # green color
            if val=='GO' or val=='CONDITIONAL-GO':
                return 'color: #20bd49'
            # dark yellow color
            elif val=='IN-PROGRESS':
                return 'color: #fdb904'
        styledDf=styledDf.applymap(format_column,subset=['Staging Verdict'])
        return styledDf


if __name__ == "__main__":
    app = Dashboard()
    app.main()
