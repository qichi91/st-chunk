import streamlit as st
import streamlit_authenticator as stauth
from user_manager import AppUser

import yaml
from yaml.loader import SafeLoader


class LoginUtil:
    def __init__(self):
        self.app_user = None
        # --- Load Authenticator Config ---
        with open('./config.yaml') as file:
            self.config = yaml.load(file, Loader=SafeLoader)

        self.authenticator = stauth.Authenticate(
            self.config['credentials'],
            self.config['cookie']['name'],
            self.config['cookie']['key'],
            self.config['cookie']['expiry_days']
        )

    def is_logged_in(self):
        return 'authentication_status' in st.session_state and st.session_state.authentication_status
    
    def get_user_info(self):
        if self.is_logged_in():
            return st.session_state.get("user_info")
        return None

    # --- Login Page ---
    def login_handler(self):
        st.title("ログイン")

        try:
            self.authenticator.login()
        except Exception as e:
            st.error(e)

        authentication_status = st.session_state.get("authentication_status")
        username = st.session_state.get("username")
        name = st.session_state.get("name") # Streamlit Authenticatorで設定したname

        if authentication_status:
            # config.yaml から email と admin フラグを取得
            email = self.config['credentials']['usernames'][username].get('email', f"{username}@example.com")
            is_admin = self.config['credentials']['usernames'][username].get('admin', False)

            # AppUserオブジェクトを作成しセッションに保存
            st.session_state.user_info = AppUser(username=username, email=email, fullname=name, is_admin=is_admin)
            # st.session_state.current_page = "ホーム"
            st.success(f"ようこそ、{st.session_state.user_info.fullname}さん！")
            st.session_state.current_page = "ホーム"
            st.rerun()
        elif authentication_status == False:
            st.error('ユーザー名またはパスワードが間違っています。')
        elif authentication_status == None:
            st.info('上記にユーザー名とパスワードを入力してください。')


    def show_logout(self):
        # self.authenticator.logout('ログアウト')
        if st.button("ログアウト"):
            self.authenticator.logout('ログアウト')
            st.session_state.user_info = None
            st.rerun()
