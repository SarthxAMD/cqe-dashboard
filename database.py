# Author      : Lenine Ajagappane <Lenine.Ajagappane@amd.com>
# Description : sqlite3 database class.

import os
import sqlite3


class Database(object):

    __DB_LOCATION = os.path.join(os.path.dirname(__file__), 'staging_data_db.sqlite')

    def __init__(self):
        """Initialize db class variables"""
        if self.get_sqlite3_thread_safety() == 3:
            check_same_thread = False
        else:
            check_same_thread = True
        self.__connection = sqlite3.connect(Database.__DB_LOCATION, check_same_thread=check_same_thread)
        self.__cur = self.__connection.cursor()

    def get_sqlite3_thread_safety(self):
        # Mape value from SQLite's THREADSAFE to Python's DBAPI 2.0
        # threadsafety attribute.
        sqlite_threadsafe2python_dbapi = {0: 0, 2: 1, 1: 3}
        conn = sqlite3.connect(Database.__DB_LOCATION)
        threadsafety = conn.execute(
            """
            select * from pragma_compile_options
            where compile_options like 'THREADSAFE=%'
            """
        ).fetchone()[0]
        conn.close()
        threadsafety_value = int(threadsafety.split("=")[1])
        return sqlite_threadsafe2python_dbapi[threadsafety_value]

    def __del__(self):
        self.__connection.commit()
        self.__connection.close()

    def execute(self, new_data, values={}):
        """execute a row of data to current cursor"""
        try:
            self.__cur.execute(new_data, values)
            self.__connection.commit()
            return 1
        except Exception as e:
            return 0

    def executemany(self, many_new_data):
        """add many new data to database in one go"""
        self.create_table()
        self.__cur.executemany('REPLACE INTO jobs VALUES(?, ?, ?, ?)', many_new_data)
        self.__connection.commit()

    def create_table(self):
        """create a database table if it does not exist already"""
        self.__cur.execute("""CREATE TABLE if not exists data_mgr (build_tag varchar(20) not null,
                            comp_name varchar(20) not null,
                            stg_type varchar(50) not null,
                            build_url varchar(255) not null,
                            request_date varchar(50) not null,
                            start_date varchar(50) not null,
                            code_date varchar(50) not null,
                            end_date varchar(50) not null,
                            status varchar(20) not null,
                            blocker_tick varchar(255) not null,
                            is_promoted varchar(20) not null,
                            promoted_main_build varchar(100) not null,
                            details_report varchar(256) not null,
                            remarks varchar(256) not null,
                            commit_info varchar(256) not null,
                            ticket_fixed varchar(256) not null,
                            base_commit varchar(256) not null,
                            promo_details varchar(256) not null,
                            promo_status varchar(256) not null,
                            release_sub_comp varchar(256) not null,
                            cp_patches varchar(256) not null,
                            release_commit varchar(256) not null,
                        primary key(build_tag)
                        );""")
        self.__connection.commit()

    def update_db(self, deleted, modified):
        if len(deleted) > 0:
            res=1
            for ele in deleted:
                with self.__connection:
                    res=res*self.execute("DELETE from data_mgr WHERE build_tag = :tag", {'tag':ele})
            if res:
                return "success"
            return "failed"
        if len(modified) > 0:
            res=1
            for ele in modified:
                args = dict(ele)
                del ele['build_tag']
                set_lines= ",".join([f"{k}=:{k}" for k in ele.keys()])
                statement = f"UPDATE data_mgr SET {set_lines} WHERE build_tag = :build_tag"
                with self.__connection:
                    res=res*self.execute(statement, args)
            if res:
                return "success"
            return "failed"

    def insert_data(self, u):
        res = 1
        with self.__connection:
            u.release_sub_comp=",".join(str(i) for i in u.release_sub_comp)
            res = res * self.execute("insert into data_mgr values (:tag, :comp, :stype, :url, :rdate, :sdate, :cdate, :edate, :status, :blocker, :ispromo, :mainUrl, :report, :remarks, :commit, :gtick, :basecommit, :pdetail, :pstatus, :rscomponent, :cppatch, :relcommit)",
                            {'tag': u.build_tag, 'comp': u.comp_name, 'stype': u.stg_type, 'url': u.build_url, 'rdate': u.request_date, 'sdate': u.start_date, 'cdate': u.code_date,
                             'edate': u.end_date, 'status': u.status, 'blocker': u.blocker_tick, 'ispromo': u.is_promoted, 'mainUrl': u.promoted_main_build, 'report': u.details_report,
                             'remarks': u.remarks, 'commit': u.commit_info, 'gtick': u.ticket_fixed, 'basecommit': u.base_commit, 'pdetail': u.promo_details, 'pstatus': u.promo_status,
                             'rscomponent': u.release_sub_comp, 'cppatch': u.cp_patches, 'relcommit': u.release_commit})
        if res:
            return "success"
        return "failed"

    def get_data_by_element(self, element, data, from_date=-1, to_date=-1):
        try:
            with self.__connection:
                if from_date != -1:
                    if(self.execute(f"select comp_name, stg_type, start_date, build_url, request_date, code_date, end_date, status, blocker_tick, is_promoted, promoted_main_build, details_report, remarks, commit_info, ticket_fixed, base_commit, promo_details, promo_status, release_sub_comp, cp_patches, release_commit, build_tag FROM data_mgr where ({element} = :data) and (:from_date <= start_date) and (start_date <= :to_date) order by start_date desc;",
                                    {'data': data, 'from_date':from_date, 'to_date':to_date})):
                        return ("success",self.__cur.fetchall())
                else:
                    if(self.execute(f"select comp_name, stg_type, start_date, build_url, request_date, code_date, end_date, status, blocker_tick, is_promoted, promoted_main_build, details_report, remarks, commit_info, ticket_fixed, base_commit, promo_details, promo_status, release_sub_comp, cp_patches, release_commit, build_tag FROM data_mgr where {element} = :data order by start_date desc limit 10;",
                                    {'data': data})):
                        return ("success",self.__cur.fetchall())
                return ("failed",())
        except Exception as e:
            return (f"failed error:{e}",())

    def get_data_by_two_elements(self, data, from_date=-1, to_date=-1):
        try:
            d_list = list(data.items())
            with self.__connection:
                if from_date != -1:
                    if(self.execute(f"select comp_name, stg_type, start_date, build_url, request_date, code_date, end_date, status, blocker_tick, is_promoted, promoted_main_build, details_report, remarks, commit_info, ticket_fixed, base_commit, promo_details, promo_status, release_sub_comp, cp_patches, release_commit, build_tag FROM data_mgr where ({d_list[0][0]}=:el1) and ({d_list[1][0]}=:el2) and (:from_date <= start_date) and (start_date <= :to_date) order by start_date desc;",
                                    {'el1': d_list[0][1], 'el2': d_list[1][1], 'from_date': from_date, 'to_date': to_date})):
                        return ("success", self.__cur.fetchall())
                else:
                    if(self.execute(f"select comp_name, stg_type, start_date, build_url, request_date, code_date, end_date, status, blocker_tick, is_promoted, promoted_main_build, details_report, remarks, commit_info, ticket_fixed, base_commit, promo_details, promo_status, release_sub_comp, cp_patches, release_commit, build_tag FROM data_mgr where {d_list[0][0]}=:el1 and {d_list[1][0]}=:el2 order by start_date desc limit 10;",
                                    {'el1': d_list[0][1], 'el2': d_list[1][1]})):
                        return ("success", self.__cur.fetchall())
            return ("failed",())
        except Exception as e:
            return (f"failed error:{e}",())

    def get_data_by_three_elements(self, data, from_date=-1, to_date=-1):
        try:
            d_list = list(data.items())
            with self.__connection:
                if from_date != -1:
                    if(self.execute(f"select comp_name, stg_type, start_date, build_url, request_date, code_date, end_date, status, blocker_tick, is_promoted, promoted_main_build, details_report, remarks, commit_info, ticket_fixed, base_commit, promo_details, promo_status, release_sub_comp, cp_patches, release_commit, build_tag FROM data_mgr where ({d_list[0][0]}=:el1) and ({d_list[1][0]}=:el2) and ({d_list[2][0]}=:el3) and (:from_date <= start_date) and (start_date <= :to_date) order by start_date desc;",
                                    {'el1': d_list[0][1], 'el2': d_list[1][1], 'el3': d_list[2][1], 'from_date': from_date, 'to_date': to_date})):
                        return ("success", self.__cur.fetchall())
                else:
                    if(self.execute(f"select comp_name, stg_type, start_date, build_url, request_date, code_date, end_date, status, blocker_tick, is_promoted, promoted_main_build, details_report, remarks, commit_info, ticket_fixed, base_commit, promo_details, promo_status, release_sub_comp, cp_patches, release_commit, build_tag FROM data_mgr where {d_list[0][0]}=:el1 and {d_list[1][0]}=:el2 and {d_list[2][0]}=:el3 order by start_date desc limit 10;",
                                    {'el1': d_list[0][1], 'el2': d_list[1][1], 'el3': d_list[2][1]})):
                        return ("success", self.__cur.fetchall())
            return ("failed",())
        except Exception as e:
            return (f"failed error:{e}",())
        
    def get_data_by_component_limit(self, comp, entries=10):
        try:
            with self.__connection:
                if (self.execute(f"select comp_name, stg_type, start_date, build_url, request_date, code_date, end_date, status, blocker_tick, is_promoted, promoted_main_build, details_report, remarks, commit_info, ticket_fixed, base_commit, promo_details, promo_status, release_sub_comp, cp_patches, release_commit, build_tag FROM data_mgr where comp_name = :comp order by start_date desc limit {entries};", {'comp': comp})):
                    return ("success",self.__cur.fetchall())
                return ("failed",())
        except Exception as e:
            return (f"failed error:{e}",())

    def get_data_by_filters(self,filters):
        try:
            with self.__connection:
                query="select comp_name, stg_type, start_date, build_url, request_date, code_date, end_date, status, blocker_tick, is_promoted, promoted_main_build, details_report, remarks, commit_info, ticket_fixed, base_commit, promo_details, promo_status, release_sub_comp, cp_patches, release_commit, build_tag FROM data_mgr"
                query+=f" where (comp_name = '{filters['comp_name']}')"
                values=[]
                for k,v in filters.items():
                    if k in ["stg_type","status","is_promoted"]:
                        query+=f" and ({k} in ({','.join('?'*len(v))}))"
                        values.extend(v)
                    elif k in ["build_url","ticket_fixed","promoted_main_build","details_report","cp_patches","remarks"]:
                        query+=f" and ({k} like '%{v}%')"
                    elif k in ["start_date","end_date"]:
                        query+=f" and ('{v[0]}' <= {k}) and ({k} <= '{v[1]}')"
                query+=" order by start_date desc;"
                if(self.execute(query,values)):
                    return ("success",self.__cur.fetchall())
                return ("failed",())
        except Exception as e:
            return (f"Failed DB error:{e}",())

    def remove_data_by_component(self, tag):
        with self.__connection:
            self.execute("DELETE from data_mgr WHERE build_tag = :tag", {'tag': tag})

    def add_entry(self, tag, comp, data):
        res = 1
        cmd = f"UPDATE data_mgr SET {comp} = :data WHERE build_tag = :tag"
        with self.__connection:
            res = res * self.execute(cmd, {'tag': tag, 'data': data})
        if res:
            return "success"
        return "failed"

    def db_size(self):
        self.execute("select count(*) from data_mgr")
        return self.__cur.fetchone()[0]

    def fetch_column_data(self, element):
        self.execute(f"select {element} from data_mgr")
        val = self.__cur.fetchall()
        return [i[0] for i in val]

