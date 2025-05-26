import streamlit as st
from datetime import datetime

def create_new_survey_form(db):
    st.subheader("新規アンケート作成")

    with st.form("new_survey_form", clear_on_submit=True):
        title = st.text_input("アンケートタイトル", help="必須項目")
        description = st.text_area("アンケート説明", help="アンケートの目的や内容を記載してください")

        submitted = st.form_submit_button("アンケートを作成")

        if submitted:
            if not title:
                st.error("アンケートタイトルは必須です。")
            else:
                # end_date は None を渡すように変更
                end_date = None # 回答期限は設定しない
                survey_id = db.create_survey(title, description, end_date)
                if survey_id:
                    st.success(f"アンケート '{title}' が作成されました！ (ID: {survey_id})")
                    st.session_state.admin_selected_survey_id = survey_id
                    st.session_state.admin_sub_page = "アンケート編集" # 作成後、質問管理ページへ遷移
                    st.rerun()
                else:
                    st.error("アンケートの作成に失敗しました。")