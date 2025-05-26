import streamlit as st
import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu

# Import custom modules (assuming they are in the same directory as app.py or in a higher level)
from user_manager import AppUser
from database import DatabaseManager

# Import page modules (relative to app/app.py)
from pages import home_page, answer_page
# Import admin sub-modules
from pages.admin import manage_surveys, create_survey

import yaml
from yaml.loader import SafeLoader

# --- Page Configuration ---
st.set_page_config(
    page_title="アンケート回答アプリ",
    page_icon="📝",
    layout="wide"
)

# --- Initialize Database ---
@st.cache_resource
def get_database():
    return DatabaseManager("survey_app.db")

db = get_database()

# --- Load Authenticator Config ---
with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- Session State Management ---
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "selected_survey_id" not in st.session_state:
    st.session_state.selected_survey_id = None
if "current_page" not in st.session_state:
    st.session_state.current_page = None
if "admin_selected_survey_id" not in st.session_state:
    st.session_state.admin_selected_survey_id = None
if "admin_edit_question_id" not in st.session_state:
    st.session_state.admin_edit_question_id = None
if "admin_sub_page" not in st.session_state:
    st.session_state.admin_sub_page = "アンケート一覧"


# --- Login Page ---
def login_handler():
    st.title("ログイン")

    try:
        authenticator.login()
    except Exception as e:
        st.error(e)

    authentication_status = st.session_state.get("authentication_status")
    username = st.session_state.get("username")
    name = st.session_state.get("name") # Streamlit Authenticatorで設定したname

    if authentication_status:
        # config.yaml から email と admin フラグを取得
        email = config['credentials']['usernames'][username].get('email', f"{username}@example.com")
        is_admin = config['credentials']['usernames'][username].get('admin', False)

        # AppUserオブジェクトを作成しセッションに保存
        st.session_state.user_info = AppUser(username, email, name, is_admin)
        st.success(f"ようこそ、{st.session_state.user_info.fullname}さん！")
        st.session_state.current_page = "ホーム"
        st.rerun()
    elif authentication_status == False:
        st.error('ユーザー名またはパスワードが間違っています。')
    elif authentication_status == None:
        st.info('上記にユーザー名とパスワードを入力してください。')

# --- Navigation Bar ---
def create_navigation_bar():
    with st.sidebar:
        menu_items = ["ホーム", "回答ページ"]
        if st.session_state.user_info and st.session_state.user_info.is_admin:
            menu_items.append("管理者ページ")

        selected = option_menu(
            "Navigation",
            menu_items,
            icons=["house", "card-checklist", "gear"],
            menu_icon="cast",
            default_index=0 if st.session_state.current_page == "ホーム" else \
                            1 if st.session_state.current_page == "回答ページ" else \
                            2 if st.session_state.current_page == "管理者ページ" else 0,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "25px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#0283C3"},
            }
        )
    return selected

# --- Main App Logic ---
if st.session_state.user_info is None:
    login_handler()
else:
    authenticator.logout('ログアウト', 'sidebar')
    st.sidebar.write(f"ログイン中: **{st.session_state.user_info.fullname}**")

    if st.session_state.current_page is None:
        st.session_state.current_page = "ホーム"

    selected_page = create_navigation_bar()

    if selected_page != st.session_state.current_page:
        st.session_state.current_page = selected_page
        st.session_state.selected_survey_id = None
        st.session_state.admin_selected_survey_id = None
        st.session_state.admin_edit_question_id = None
        st.session_state.admin_sub_page = "アンケート一覧"
        st.rerun()

    if st.session_state.current_page == "ホーム":
        home_page.show_page(db)
    elif st.session_state.current_page == "回答ページ":
        answer_page.show_page(db)
    elif st.session_state.current_page == "管理者ページ":
        if not st.session_state.user_info.is_admin:
            st.error("管理者のみがこのページにアクセスできます。")
            st.session_state.current_page = "ホーム" # Redirect non-admins
            st.rerun()

        st.title("管理者ページ")
        st.write("アンケートの作成、編集、削除を行います。")

        admin_menu = option_menu(
            None,
            ["アンケート一覧", "新規アンケート作成"],
            icons=["list-task", "plus-circle"],
            menu_icon="cast",
            default_index=0 if st.session_state.admin_sub_page == "アンケート一覧" else 1,
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "20px"},
                "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#0283C3"},
            }
        )

        if admin_menu != st.session_state.admin_sub_page:
            st.session_state.admin_sub_page = admin_menu
            st.session_state.admin_selected_survey_id = None
            st.session_state.admin_edit_question_id = None
            # admin_sub_page が変わったときに current_question_page もリセット
            if f'current_question_page_{st.session_state.admin_selected_survey_id}' in st.session_state:
                del st.session_state[f'current_question_page_{st.session_state.admin_selected_survey_id}']
            st.rerun()

        if st.session_state.admin_sub_page == "アンケート一覧":
            manage_surveys.display_admin_survey_list(db)
        elif st.session_state.admin_sub_page == "新規アンケート作成":
            create_survey.create_new_survey_form(db)