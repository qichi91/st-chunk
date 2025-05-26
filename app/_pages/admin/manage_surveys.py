import streamlit as st
from datetime import datetime
import json # display_survey_results で json を使用するため追加

# manage_questions_for_survey は別のファイルにあるので、ここでのインポートは不要
# ただし、呼び出す際には from .manage_questions import manage_questions_for_survey のように相対パスでインポートする必要がある

def display_admin_survey_list(db):

    # サブページの表示ロジックをここに集約
    if 'admin_sub_page_func' not in st.session_state:
        st.session_state.admin_sub_page_func = None
        
    if st.session_state.admin_sub_page_func == "アンケート編集" and st.session_state.admin_selected_survey_id:
        from pages.admin.manage_questions import manage_questions_for_survey_and_info # 修正後の関数をインポート
        manage_questions_for_survey_and_info(db, st.session_state.admin_selected_survey_id)
    elif st.session_state.admin_sub_page_func == "回答結果確認" and st.session_state.admin_selected_survey_id:
        display_survey_results(db, st.session_state.admin_selected_survey_id)
    else:
        st.session_state.admin_sub_page_func = None
        display_surveys(db)

def display_surveys(db):
    st.subheader("アンケート一覧")

    surveys = db.get_all_surveys()

    if surveys:
        for survey in surveys:
            st.markdown(f"#### {survey['title']} (ID: {survey['survey_id']})")
            st.write(f"説明: {survey['description']}")
            st.write(f"作成日: {survey['created_at']}")
            st.write(f"期限: {survey['end_date'] if survey['end_date'] else 'なし'}")

            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
            with col1:
                # 「編集」ボタンを押したら「アンケート編集」サブページに遷移
                if st.button("編集", key=f"edit_survey_{survey['survey_id']}"):
                    st.session_state.admin_selected_survey_id = survey['survey_id']
                    st.session_state.admin_sub_page_func = "アンケート編集" # 新しいサブページへ遷移
                    st.session_state.admin_edit_question_id = None # 質問編集状態をリセット
                    st.rerun()
            with col2:
                if st.button("削除", key=f"delete_survey_{survey['survey_id']}"):
                    # 削除確認をモーダルなどで実装するのがよりユーザーフレンドリーですが、今回はシンプルに確認
                    if st.warning(f"本当にアンケート '{survey['title']}' を削除しますか？"):
                        if st.button("はい、削除します", key=f"confirm_delete_{survey['survey_id']}"):
                            db.delete_survey(survey['survey_id'])
                            st.success("アンケートが削除されました。")
                            st.rerun()
            with col3:
                if st.button("複製", key=f"duplicate_survey_{survey['survey_id']}"):
                    new_survey_id = db.duplicate_survey(survey['survey_id'])
                    if new_survey_id:
                        st.success(f"アンケート '{survey['title']}' が複製されました。(新しいID: {new_survey_id})")
                        st.rerun()
                    else:
                        st.error("アンケートの複製に失敗しました。")
            with col4:
                if st.button("回答結果を見る", key=f"view_results_{survey['survey_id']}"):
                    st.session_state.admin_selected_survey_id = survey['survey_id']
                    st.session_state.admin_sub_page_func = "回答結果確認" # 新しいサブページへ遷移
                    st.rerun()

            st.markdown("---")
    else:
        st.info("現在、アンケートは登録されていません。")


def display_survey_results(db, survey_id):
    st.subheader(f"アンケートID: {survey_id} の回答結果")
    survey = db.get_survey_by_id(survey_id)
    if survey:
        st.markdown(f"### {survey['title']}")
        st.write(f"説明: {survey['description']}")
        st.write(f"期限: {survey['end_date'] if survey['end_date'] else 'なし'}")

        all_answers = db.get_all_answers_for_survey(survey_id)
        questions = db.get_survey_questions(survey_id)

        if not all_answers:
            st.info("このアンケートにはまだ提出された回答がありません。")
            # 「アンケート一覧に戻る」ボタン
            if st.button("アンケート一覧に戻る", key="back_from_results_no_answers"):
                st.session_state.admin_selected_survey_id = None
                st.session_state.admin_sub_page = "アンケート一覧"
                st.rerun()
            return

        # 回答をユーザーと質問ごとに整理
        user_responses = {}
        for answer in all_answers:
            username = answer['username']
            question_id = answer['question_id']
            if username not in user_responses:
                user_responses[username] = {}
            user_responses[username][question_id] = answer['answer_text']

        # 質問IDから質問テキストへのマッピング (質問順序を考慮)
        question_map_ordered = {q['question_id']: q for q in questions}

        st.markdown("---")
        st.subheader("個別回答詳細")
        
        # ユーザーごとに回答を表示
        for username, answers_by_question in user_responses.items():
            st.markdown(f"##### 回答者: {username}")
            # 質問の表示順序を維持するために questions リストを直接使う
            for q in questions:
                question_text = q['question_text']
                answer_text = answers_by_question.get(q['question_id'], "未回答") # 回答がない場合は「未回答」
                
                # 選択肢形式の場合の表示を調整
                if q['question_type'] == 'single' and answer_text != "未回答":
                    st.write(f"**Q{q['order_number']}. {question_text}**")
                    st.success(f"選択: {answer_text}")
                elif q['question_type'] == 'multi' and answer_text != "未回答":
                    try:
                        selected_options = json.loads(answer_text)
                        st.write(f"**Q{q['order_number']}. {question_text}**")
                        st.success(f"選択: {', '.join(selected_options) if selected_options else 'なし'}")
                    except json.JSONDecodeError:
                        st.write(f"**Q{q['order_number']}. {question_text}**")
                        st.warning(f"回答内容 (JSON解析エラー): {answer_text}")
                else: # テキスト形式など
                    st.write(f"**Q{q['order_number']}. {question_text}**")
                    st.info(f"回答: {answer_text}")
            st.markdown("---")
        
        # 「アンケート一覧に戻る」ボタン
        if st.button("アンケート一覧に戻る", key="back_from_results"):
            st.session_state.admin_selected_survey_id = None
            st.session_state.admin_sub_page = "アンケート一覧"
            st.rerun()

    else:
        st.error("指定されたアンケートは見つかりませんでした。")
        if st.button("アンケート一覧に戻る", key="back_from_results_not_found"):
            st.session_state.admin_selected_survey_id = None
            st.session_state.admin_sub_page = "アンケート一覧"
            st.rerun()