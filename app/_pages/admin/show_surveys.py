import streamlit as st
from datetime import datetime
import json # display_survey_results で json を使用するため追加

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