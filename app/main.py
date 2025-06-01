import streamlit as st


def login():
    if st.button("Log in"):
        st.login("keycloak")


def logout():
    if st.button("Log out"):
        st.logout()


def get_user_pages():
    return [
        st.Page(
            "pages/user/user_dashboard.py",
            title="ダッシュボード",
            icon=":material/dashboard:",
            url_path="/dashboard",
        ),
        # 公開中のアンケートへの回答ページ
        st.Page(
            "pages/user/survey_answer.py",
            title="アンケート回答",
            icon=":material/stylus:",
            url_path="/survey_answer",
        ),
        # アンケートの回答履歴ページ
        st.Page(
            "pages/user/survey_history.py",
            title="アンケート回答履歴",
            icon=":material/history:",
            url_path="/survey_history",
        ),
    ]


def get_admin_pages():
    return [
        st.Page(
            "pages/admin/dummy.py",
            title="管理者ページ",
            icon=":material/admin_panel_settings:",
            url_path="/survey_admin",
        ),
        # アンケートの管理ページ
        st.Page(
            "pages/admin/survey_admin.py",
            title="アンケート管理",
            icon=":material/folder_managed:",
            url_path="/admin_survey_manage",
        ),
        # アンケートの作成ページ
        st.Page(
            "pages/admin/survey_create.py",
            title="アンケート作成",
            icon=":material/add:",
            url_path="/admin_survey_admin_create",
        ),
        # アンケートの編集ページ
        st.Page(
            "pages/admin/survey_edit.py",
            title="アンケート編集",
            icon=":material/build:",
            url_path="/admin_survey_admin_edit",
        ),
        # アンケートの回答集計ページ
        st.Page(
            "pages/admin/survey_analysis.py",
            title="アンケート回答集計",
            icon=":material/query_stats:",
            url_path="/admin_survey_analysis",
        ),
    ]


def page_routing():
    login_page = st.Page(login, title="ログイン", icon=":material/login:")
    logout_page = st.Page(logout, title="ログアウト", icon=":material/logout:")

    if not st.user or not st.user.is_logged_in:
        pg = st.navigation([login_page])
    else:
        st.write(f"User: {st.user.to_dict()}")
        pages = {"Account": [logout_page], "Dashboard": get_user_pages()}
        if "/survey_admin" in st.user.groups:
            pages["Admin"] = get_admin_pages()

        pg = st.navigation(pages)
    pg.run()


def main():
    # ページ遷移したら変数を初期化したい

    # ログイン制御や、ログイン後のページを表示
    # サイドバーにメニューを表示
    page_routing()


if __name__ == "__main__":
    main()
