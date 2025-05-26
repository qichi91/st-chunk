import streamlit as st
from streamlit_option_menu import option_menu

# Import custom modules (assuming they are in the same directory as app.py or in a higher level)
from database import DatabaseManager

# Import page modules (relative to app/app.py)
# from pages import home_page, answer_page
# Import admin sub-modules
# from pages.admin import manage_surveys, create_survey

from login.local_login import LoginUtil

# --- Page Configuration ---
st.set_page_config(page_title="アンケート回答アプリ", page_icon="📝", layout="wide")


# --- Initialize Database ---
@st.cache_resource
def get_database():
    return DatabaseManager("survey_app.db")


db = get_database()

u_login = LoginUtil()

# --- Session State Management ---
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "selected_survey_id" not in st.session_state:
    st.session_state.selected_survey_id = None

# --- Main App Logic ---
if not u_login.is_logged_in():
    u_login.login_handler()
else:
    # logout_page = u_login.show_logout()

    st.sidebar.write(f"ログイン中: **{st.session_state.user_info.fullname}**")

    user_home_page = st.Page(
        "pages/user_home.py", title="ホーム", icon=":material/home:"
    )
    admin_home_page = st.Page(
        "pages/admin_home.py", title="ホーム", icon=":material/home:"
    )
    page_dict = {
        "Account": [u_login.show_logout],
        "User": [user_home_page],
        "Admin": [admin_home_page],
    }

    # manage_surveys = st.Page("pages/user/manage_surveys.py", title="Manage Surveys", icon=":material/login:")
    pg = st.navigation(page_dict)
    pg.run()
