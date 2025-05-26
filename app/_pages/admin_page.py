import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime, date
import json
import pandas as pd
# For drag and drop reordering
# You might need to install streamlit-extras for this if not already installed:
# pip install streamlit-extras
from streamlit_extras.dataframe_explorer import dataframe_explorer # Simple reorder example

def show_page(db):
    if not st.session_state.user_info.is_admin:
        st.error("管理者のみがこのページにアクセスできます。")
        return

    st.title("管理者ページ")
    st.write("アンケートの作成、編集、削除を行います。")

    admin_menu = option_menu(
        None,
        ["アンケート一覧", "新規アンケート作成"],
        icons=["list-task", "plus-circle"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "orange", "font-size": "20px"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#0283C3"},
        }
    )

    if admin_menu == "アンケート一覧":
        display_admin_survey_list(db)
    elif admin_menu == "新規アンケート作成":
        create_new_survey_form(db)

def display_admin_survey_list(db):
    st.subheader("登録済みアンケート")
    surveys = db.get_all_surveys()

    if st.session_state.admin_selected_survey_id:
        selected_survey = db.get_survey_by_id(st.session_state.admin_selected_survey_id)
        if selected_survey:
            edit_survey_details(db, selected_survey)
            return
        else:
            st.session_state.admin_selected_survey_id = None # Clear if survey not found

    if not surveys:
        st.info("現在、登録されているアンケートはありません。")
        return

    for survey in surveys:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"### {survey['title']}")
            st.write(survey['description'])
            st.write(f"回答期限: {survey['end_date'] if survey['end_date'] else 'なし'}")
        with col2:
            if st.button("編集", key=f"edit_survey_{survey['survey_id']}"):
                st.session_state.admin_selected_survey_id = survey['survey_id']
                st.session_state.admin_edit_question_id = None # Clear question selection
                st.rerun()
        with col3:
            if st.button("削除", key=f"delete_survey_{survey['survey_id']}"):
                # Use a confirmation pattern
                if st.warning(f"本当に「{survey['title']}」を削除しますか？関連する質問と回答も削除されます。", icon="⚠️"):
                    if st.button("はい、削除します", key=f"confirm_delete_{survey['survey_id']}"):
                        db.delete_survey(survey['survey_id'])
                        st.success("アンケートを削除しました。")
                        st.rerun()
        st.markdown("---")

def create_new_survey_form(db):
    st.subheader("新規アンケート作成")
    with st.form("new_survey_form", clear_on_submit=True):
        title = st.text_input("アンケートタイトル", help="アンケートのタイトルを入力してください。")
        description = st.text_area("アンケート説明", help="アンケートの説明文を入力してください。")
        end_date = st.date_input("回答期限 (任意)", value=None, min_value=date.today(), help="回答の締め切り日を設定します。")

        submitted = st.form_submit_button("アンケートを作成")

        if submitted:
            if title:
                db.add_survey(title, description, end_date.strftime('%Y-%m-%d') if end_date else None)
                st.success("アンケートを作成しました！")
                st.session_state.admin_selected_survey_id = None # Clear any previous selection
                st.rerun()
            else:
                st.error("タイトルは必須です。")

def edit_survey_details(db, survey):
    st.subheader(f"アンケート編集: {survey['title']}")

    # Back button
    if st.button("アンケート一覧に戻る"):
        st.session_state.admin_selected_survey_id = None
        st.session_state.admin_edit_question_id = None
        st.rerun()
    st.markdown("---")

    with st.form(f"edit_survey_form_{survey['survey_id']}"):
        new_title = st.text_input("アンケートタイトル", value=survey['title'])
        new_description = st.text_area("アンケート説明", value=survey['description'])
        current_end_date = datetime.strptime(survey['end_date'], '%Y-%m-%d').date() if survey['end_date'] else None
        new_end_date = st.date_input("回答期限 (任意)", value=current_end_date, min_value=date.today() if current_end_date is None or current_end_date < date.today() else current_end_date, help="回答の締め切り日を設定します。")

        update_submitted = st.form_submit_button("アンケート情報を更新")

        if update_submitted:
            if new_title:
                db.update_survey(survey['survey_id'], new_title, new_description, new_end_date.strftime('%Y-%m-%d') if new_end_date else None)
                st.success("アンケート情報を更新しました！")
                st.rerun()
            else:
                st.error("タイトルは必須です。")
    st.markdown("---")

    # Question management for this survey
    st.subheader("設問管理")
    questions = db.get_survey_questions(survey['survey_id'])

    # Display question editing form if a question is selected
    if st.session_state.admin_edit_question_id:
        selected_question = next((q for q in questions if q['question_id'] == st.session_state.admin_edit_question_id), None)
        if selected_question:
            edit_question_form(db, survey['survey_id'], selected_question)
            return
        else:
            st.session_state.admin_edit_question_id = None # Clear if question not found

    # Add new question form
    st.subheader("新規設問追加")
    with st.form("new_question_form", clear_on_submit=True):
        max_page = db.get_max_page_number(survey['survey_id'])
        q_page_number = st.number_input("ページ番号", min_value=1, value=max_page + 1, step=1, help="設問を表示するページ番号。")

        # Get max order number for the selected page or default to 1 if no questions on that page
        max_order = db.get_max_order_number(survey['survey_id'], q_page_number)
        q_order_number = st.number_input("ページ内での表示順", min_value=1, value=max_order + 1, step=1, help="ページ内での設問の表示順。")

        q_text = st.text_area("設問内容", help="質問文を入力してください。")
        q_type = st.selectbox("設問タイプ", ["単一選択", "自由記述"], help="回答形式を選択してください。")
        options_input = st.text_area("選択肢 (カンマ区切り、単一選択の場合のみ)", help="例: はい, いいえ, わからない")
        image_url = st.text_input("画像URL (任意)", help="設問と共に表示する画像のURLを入力してください。")

        add_question_submitted = st.form_submit_button("設問を追加")

        if add_question_submitted:
            if q_text:
                options = [o.strip() for o in options_input.split(',')] if options_input and q_type == "単一選択" else None
                question_type_db = "single" if q_type == "単一選択" else "text"
                db.add_question(survey['survey_id'], q_page_number, q_order_number, q_text, question_type_db, options, image_url if image_url else None)
                st.success("設問を追加しました！")
                st.rerun()
            else:
                st.error("設問内容は必須です。")
    st.markdown("---")

    # List and manage existing questions
    st.subheader("既存の設問")
    if not questions:
        st.info("このアンケートにはまだ設問がありません。")
        return

    # Convert questions to DataFrame for potential reordering with streamlit-extras
    # Note: Streamlit-extras's dataframe_explorer offers basic reordering by columns
    # For true drag-and-drop row reordering, a custom component might be needed.
    # Here, we'll demonstrate using number_inputs for page and order changes.
    questions_df = pd.DataFrame(questions)
    questions_df['options_display'] = questions_df['options'].apply(lambda x: ', '.join(x) if x else '')

    st.write("各設問のページ番号や表示順を変更できます。")

    for index, q in questions_df.iterrows():
        st.markdown(f"**設問 {q['question_id']}: {q['question_text']}**")
        col_page, col_order, col_type, col_edit, col_delete = st.columns([1, 1, 2, 1, 1])
        with col_page:
            new_page_number = st.number_input(f"ページ", min_value=1, value=int(q['page_number']), key=f"page_q_{q['question_id']}")
            if new_page_number != q['page_number']:
                db.update_question_page(q['question_id'], new_page_number)
                st.rerun() # Rerun to reflect changes
        with col_order:
            new_order_number = st.number_input(f"順序", min_value=1, value=int(q['order_number']), key=f"order_q_{q['question_id']}")
            if new_order_number != q['order_number']:
                db.update_question_order(q['question_id'], new_order_number)
                st.rerun() # Rerun to reflect changes
        with col_type:
            st.write(f"タイプ: {q['question_type']}")
            if q['options_display']:
                st.write(f"選択肢: {q['options_display']}")
            if q['image_url']:
                st.image(q['image_url'], caption="画像", width=80)
        with col_edit:
            if st.button("編集", key=f"edit_question_{q['question_id']}"):
                st.session_state.admin_edit_question_id = q['question_id']
                st.rerun()
        with col_delete:
            if st.button("削除", key=f"delete_question_{q['question_id']}"):
                if st.warning(f"本当にこの設問を削除しますか？関連する回答も削除されます。", icon="⚠️"):
                    if st.button("はい、削除します", key=f"confirm_delete_q_{q['question_id']}"):
                        db.delete_question(q['question_id'])
                        st.success("設問を削除しました。")
                        st.rerun()
        st.markdown("---")

def edit_question_form(db, survey_id, question):
    st.subheader(f"設問編集: {question['question_text']}")

    # Back button
    if st.button("設問一覧に戻る"):
        st.session_state.admin_edit_question_id = None
        st.rerun()
    st.markdown("---")

    with st.form(f"edit_question_form_{question['question_id']}"):
        # Page and order numbers for editing
        max_page = db.get_max_page_number(survey_id)
        max_order_on_current_page = db.get_max_order_number(survey_id, question['page_number'])

        new_page_number = st.number_input("ページ番号", min_value=1, value=int(question['page_number']), step=1, key=f"edit_page_q_{question['question_id']}")
        new_order_number = st.number_input("ページ内での表示順", min_value=1, value=int(question['order_number']), step=1, key=f"edit_order_q_{question['question_id']}")

        new_q_text = st.text_area("設問内容", value=question['question_text'])
        new_q_type = st.selectbox("設問タイプ", ["単一選択", "自由記述"], index=0 if question['question_type'] == 'single' else 1)
        current_options_str = ", ".join(question['options']) if question['options'] else ""
        new_options_input = st.text_area("選択肢 (カンマ区切り、単一選択の場合のみ)", value=current_options_str)
        new_image_url = st.text_input("画像URL (任意)", value=question['image_url'] if question['image_url'] else "")

        update_question_submitted = st.form_submit_button("設問を更新")

        if update_question_submitted:
            if new_q_text:
                new_options = [o.strip() for o in new_options_input.split(',')] if new_options_input and new_q_type == "単一選択" else None
                question_type_db = "single" if new_q_type == "単一選択" else "text"
                db.update_question(question['question_id'], new_page_number, new_order_number, new_q_text, question_type_db, new_options, new_image_url if new_image_url else None)
                st.success("設問を更新しました！")
                st.session_state.admin_edit_question_id = None # Clear selection after update
                st.rerun()
            else:
                st.error("設問内容は必須です。")