# Author      : Lenine Ajagappane <Lenine.Ajagappane@amd.com>
# Description : HTML/CSS Styles template

import os
import streamlit as st


class StyleTemplate:

    def __init__(self):
        self.nav_styles = {
            "nav": {
                "background-color": "rgb(148, 214, 245 )",
                "justify-content": "left",
                "font-family": "var(--font)",
                "font-size": "14px",
                "height": "2.5rem",
                "padding-right": "10px",
                "align-items": "center"
            },
            "img": {
                "padding-right": "30px",
                "padding-left": "0.1px",
                "height": "1.9rem",
            },
            "div": {
                "max-width": "50rem",
            },
            "span": {
                "border-radius": "1rem",
                "color": "rgb(49, 51, 63)",
                "margin": "0.5 0.5rem",
                "padding": "0.5rem 0.5rem",
                "height": "1rem",
            },
            "active": {
                "background-color": "rgba(255, 255, 255, 0.25)",
                "height": "1rem",
            },
            "hover": {
                "background-color": "rgba(255, 255, 255, 0.35)",
                "height": "1rem",
            },
        }
        self.nav_options = {
            "show_menu": True,
            # "use_padding": True,
            # "fix_shadow":True,
            "show_sidebar": False,
        }
        self.nav_logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rocm_cqe_logo.svg")

    def set_page_config(self):
        image_path = os.path.join(os.path.dirname(__file__), 'images/dashboard.PNG')
        st.set_page_config(page_title="ROCm CQE Dashboard", page_icon=image_path, layout="wide")
        page_bg_img = f"""
        <style>
            [data-testid="stAppViewContainer"] > .main {{
                background-image: url("");
                background-size: 100%;
                display: flex;
                background-position: top left;
                background-repeat: no-repeat;
                background-attachment: local;
            }}
            .block-container {{
                padding-top: 0rem;
                padding-bottom: 0rem;
                padding-left: 2rem;
                padding-right: 2rem;
            }}
            [data-testid="stHeader"] {{
                background: rgba(0,0,0,0);
            }}
            [data-testid="stToolbar"] .css-ng1t4o {{
                right: 1rem;
            }}
            .stTabs [data-baseweb="tab-list"] {{
                gap: 2px;
            }}
            .stTabs [data-baseweb="tab"] {{
                height: 30px;
                width: 160px;
                white-space: pre-wrap;
                border-radius: 4px 4px 0px 0px;
                gap: 1px;
                padding-top: 10px;
                padding-bottom: 10px;
            }}
            .stTabs [aria-selected="true"] {{
                background-color: #F5F5F5;
            }}
        </style>
        """
        #st.markdown(page_bg_img, unsafe_allow_html=True)

    def table_format(self):
        th_props = [
            ('font-size', '14px'),
            ('text-align', 'center'),
            ('font-weight', 'bold'),
            ('color', '#000000'),
            ('background-color', '#B0E0E6')
        ]
        td_props = [
            ('text-align', 'left'),
            ('font-size', '13px')
        ]
        styles = [
            dict(selector="th", props=th_props),
            dict(selector="td", props=td_props)
        ]
        return styles
