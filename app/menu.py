import streamlit as st
from local_login import LoginUtil
from user_manager import AppUser


class Menu:
    def __init__(self):
        self.u_login = LoginUtil()
    
    def authenticated_menu(self):
        # Show a navigation menu for authenticated users
        st.sidebar.page_link("app.py", label="Switch accounts")
        st.sidebar.page_link("pages/user.py", label="Your profile")
        if 'user_info' in st.session_state and st.session_state.user_info.is_admin:
            st.sidebar.page_link("pages/admin.py", label="Manage users")
            st.sidebar.page_link(
                "pages/super-admin.py",
                label="Manage admin access",
                # disabled=st.session_state.role != "super-admin",
            )


    def unauthenticated_menu(self):
        # Show a navigation menu for unauthenticated users
        st.sidebar.page_link("app.py", label="Log in")


    def menu(self):
        # Determine if a user is logged in or not, then show the correct
        # navigation menu
        if 'user_info' not in st.session_state and st.session_state.user_info is None:
            self.unauthenticated_menu()
            return
        self.authenticated_menu()


    def menu_with_redirect(self):
        # Redirect users to the main page if not logged in, otherwise continue to
        # render the navigation menu
        if 'user_info' not in st.session_state and st.session_state.user_info is None:
            st.switch_page("app.py")
        self.menu()
