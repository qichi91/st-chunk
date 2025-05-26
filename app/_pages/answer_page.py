import streamlit as st
from streamlit_survey import StreamlitSurvey
import json
from datetime import datetime

# on_submitコールバック関数
def handle_survey_submit(db, survey_id, all_questions_data, survey_data_dict):
    """
    アンケートが提出されたときに呼び出されるコールバック関数。
    回答をデータベースに保存し、完了メッセージを表示します。
    """
    user_id = st.session_state.user_info.username
    # 全ての質問の回答を保存
    save_current_page_answers(db, survey_id, all_questions_data, survey_data_dict, is_draft=False)
    st.success("アンケートを提出しました！")
    st.session_state.selected_survey_id = None
    st.rerun()

# 一時保存ボタンのハンドラ関数
def handle_save_draft(db, survey_id, all_questions_data, survey_data_dict):
    """
    一時保存ボタンが押されたときに呼び出されるハンドラ関数。
    回答をデータベースにドラフトとして保存します。
    """
    user_id = st.session_state.user_info.username
    # 全ての質問の回答を一時保存
    save_current_page_answers(db, survey_id, all_questions_data, survey_data_dict, is_draft=True)
    st.info("回答を一時保存しました。")
    st.rerun()


def show_page(db):
    st.title("アンケート回答ページ")

    if st.session_state.selected_survey_id:
        survey_id = st.session_state.selected_survey_id
        survey_info = db.get_survey_by_id(survey_id)
        all_questions_data = db.get_survey_questions(survey_id)

        if not survey_info:
            st.error("選択されたアンケートが見つかりません。")
            if st.button("別のアンケートを選択"):
                st.session_state.selected_survey_id = None
                st.rerun()
            return

        st.header(survey_info['title'])
        st.markdown(f"*{survey_info['description']}*")

        created_at_str = survey_info['created_at']
        end_date_str = survey_info['end_date']
        current_date_obj = datetime.now().date() # 日付のみで比較

        # 公開期間の判定ロジック
        is_active_for_answering = False # 回答可能かどうか
        is_expired = False # 期限切れかどうか
        is_unpublished_or_invalid = False # 未公開（end_dateなし）またはcreated_atがない場合

        st.write(f"**作成日:** {created_at_str if created_at_str else '不明'}")
        st.write(f"**公開終了日:** {end_date_str if end_date_str else '設定なし'}")

        if end_date_str: # 公開終了日が設定されている場合のみ、回答可能かの判定を行う
            try:
                end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                if current_date_obj <= end_date_obj:
                    # 作成日が有効であることも確認（ここでは created_at が必須とはしないが、運用で必要なら追加）
                    is_active_for_answering = True # 現在日時が終了日を超えていない
                else:
                    is_expired = True # 終了日を超えている
            except ValueError:
                # end_date の形式が不正な場合
                is_unpublished_or_invalid = True
                st.error("アンケートの公開終了日の形式が不正です。管理者に確認してください。")
        else:
            is_unpublished_or_invalid = True # 公開終了日が設定されていないので、回答は不可

        st.markdown("---")

        user_answers = db.get_user_answers_for_survey(st.session_state.user_info.username, survey_id)
        # ユーザーが提出済みの回答を持っているか
        user_has_submitted_answers = any(a['is_draft'] == False and a['answer_text'] is not None for a in user_answers)

        # 回答期限が過ぎている、または未公開の場合で、かつ回答済みの場合は閲覧モード
        # is_unpublished_or_invalid は「未公開」の意図だが、回答は不可。
        # 期限切れで、かつ回答済みの場合のみ閲覧を許可
        if is_expired and user_has_submitted_answers:
            st.subheader("あなたの回答（閲覧のみ）")
            if not user_answers: # ありえないケースだが念のため
                st.info("このアンケートにはまだ回答していません。")
            else:
                # streamlit_surveyを使用せず、質問と回答をリストで表示
                for q_data in all_questions_data: # 全ての質問を回る
                    st.write(f"**設問 {q_data['order_number']}.** {q_data['question_text']}")
                    if q_data['image_url']:
                        st.image(q_data['image_url'], caption="設問画像", width=300)

                    # 該当する質問のユーザーの回答を見つける
                    answer_for_this_q = next((a for a in user_answers if a['question_id'] == q_data['question_id']), None)

                    answer_display_text = "未回答"
                    if answer_for_this_q and answer_for_this_q['answer_text']:
                        try:
                            # Try to load as JSON for single/multiple choice options
                            answer_val = json.loads(answer_for_this_q['answer_text'])
                            if isinstance(answer_val, list): # For multiselect/checkboxes
                                answer_display_text = ", ".join(answer_val)
                            else: # For single choice
                                answer_display_text = str(answer_val)
                        except json.JSONDecodeError:
                            answer_display_text = answer_for_this_q['answer_text'] # For text answers
                    st.write(f"**あなたの回答:** {answer_display_text}")
                    st.markdown("---")

            if st.button("別のアンケートを選択"):
                st.session_state.selected_survey_id = None
                st.rerun()
            return # 閲覧モードの場合はここで終了

        # 回答可能な状態でない場合（期限切れで未回答、または未公開/不正な形式）
        if not is_active_for_answering:
            if is_expired:
                st.warning("このアンケートは回答期限を過ぎています。回答はできません。")
            elif is_unpublished_or_invalid:
                st.warning("このアンケートは公開されていません（公開終了日が設定されていないか、形式が不正です）。回答はできません。")
            st.info("このアンケートは現在、回答を受け付けていません。")
            if st.button("別のアンケートを選択"):
                st.session_state.selected_survey_id = None
                st.rerun()
            return


        # 以下、回答可能な場合
        survey = StreamlitSurvey(f"survey_{survey_id}")

        # Populate survey.data with existing answers for editing/continuing draft
        for q in user_answers:
            if q['answer_text'] is not None:
                q_key = f"q_{q['question_id']}"
                try:
                    parsed_answer = json.loads(q['answer_text'])
                except json.JSONDecodeError:
                    parsed_answer = q['answer_text']
                survey.data[q_key] = {"value": parsed_answer, "widget_key": q_key}


        # Determine the number of pages
        max_page_number = db.get_max_page_number(survey_id)
        num_pages = max_page_number if max_page_number > 0 else 1

        pages = survey.pages(num_pages, on_submit=lambda: handle_survey_submit(db, survey_id, all_questions_data, survey.data))

        pages.submit_button = pages.default_btn_submit("アンケートを提出")
        pages.prev_button = pages.default_btn_previous("前のページへ")
        pages.next_button = pages.default_btn_next("次のページへ")

        with pages:
            current_page_questions = [
                q for q in all_questions_data if q['page_number'] == pages.current + 1
            ]

            if not current_page_questions and num_pages > 1:
                st.info("このページには設問がありません。")
            elif not current_page_questions and num_pages == 1:
                 st.info("このアンケートには設問がありません。")


            for question in current_page_questions:
                q_id = question['question_id']
                q_text = question['question_text']
                q_type = question['question_type']
                q_options = question['options']
                q_image_url = question['image_url']

                st.subheader(f"設問 {question['order_number']}. {q_text}")
                if q_image_url:
                    st.image(q_image_url, caption="設問画像", width=300)

                if q_type == 'single':
                    survey.radio(q_text, options=q_options, key=f"q_{q_id}", help="いずれか一つを選択してください。")
                elif q_type == 'text':
                    survey.text_area(q_text, key=f"q_{q_id}", help="自由記述で回答してください。")

            st.markdown("---")

            st.button(
                "一時保存",
                key=f"save_draft_page_{pages.current}",
                on_click=lambda: handle_save_draft(db, survey_id, all_questions_data, survey.data)
            )

        if st.button("別のアンケートを選択", key="back_from_survey_list_page"):
            st.session_state.selected_survey_id = None
            st.rerun()

    else: # selected_survey_id が None の場合 (アンケート選択リスト表示)
        st.title("アンケート選択")
        username = st.session_state.user_info.username
        today = datetime.now().date()

        # 未回答アンケート（公開終了日が現在日時を超えていないもの）
        unanswered_surveys = []
        conn = db.conn
        cursor = db.cursor
        cursor.execute("""
            SELECT
                s.survey_id,
                s.title,
                s.description,
                s.end_date
            FROM surveys s
            LEFT JOIN (
                SELECT DISTINCT survey_id
                FROM answers
                WHERE username = ? AND is_draft = FALSE
            ) AS submitted_answers ON s.survey_id = submitted_answers.survey_id
            LEFT JOIN (
                SELECT DISTINCT survey_id
                FROM answers
                WHERE username = ? AND is_draft = TRUE
            ) AS draft_answers ON s.survey_id = draft_answers.survey_id
            WHERE submitted_answers.survey_id IS NULL
              AND draft_answers.survey_id IS NULL
              AND (s.end_date IS NULL OR s.end_date >= ?)
            ORDER BY s.survey_id ASC
        """, (username, username, today.strftime('%Y-%m-%d')))
        unanswered_surveys = [dict(row) for row in cursor.fetchall()]

        # 一時保存アンケート（公開終了日が現在日時を超えていないもの）
        draft_surveys = db.get_user_draft_surveys(username)
        draft_surveys = [
            s for s in draft_surveys
            if not s.get('end_date') or datetime.strptime(s['end_date'], '%Y-%m-%d').date() >= today
        ]

        # 回答済みアンケート（期限は問わない）
        answered_surveys = db.get_user_answered_surveys(username)

        # --- 表示 ---
        st.subheader("未回答のアンケート")
        if unanswered_surveys:
            for survey in unanswered_surveys:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{survey['title']}** (ID: {survey['survey_id']})")
                    st.write(f"説明: {survey['description']}")
                    st.write(f"回答期限: {survey['end_date'] if survey['end_date'] else 'なし'}")
                with col2:
                    if st.button("回答を開始", key=f"start_answer_{survey['survey_id']}"):
                        st.session_state.selected_survey_id = survey['survey_id']
                        st.rerun()
        else:
            st.info("現在、回答可能な新しいアンケートはありません。")

        st.markdown("---")
        st.subheader("一時保存中のアンケート")
        if draft_surveys:
            for survey in draft_surveys:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{survey['title']}** (ID: {survey['survey_id']})")
                    survey_info = db.get_survey_by_id(survey['survey_id'])
                    if survey_info:
                        st.write(f"説明: {survey_info['description']}")
                        st.write(f"回答期限: {survey_info['end_date'] if survey_info['end_date'] else 'なし'}")
                    else:
                        st.write("説明: 取得できませんでした")
                with col2:
                    if st.button("回答を再開", key=f"resume_answer_{survey['survey_id']}"):
                        st.session_state.selected_survey_id = survey['survey_id']
                        st.rerun()
        else:
            st.info("一時保存中のアンケートはありません。")

        st.markdown("---")
        st.subheader("回答済みのアンケート")
        if answered_surveys:
            for survey in answered_surveys:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{survey['title']}** (ID: {survey['survey_id']})")
                    survey_info = db.get_survey_by_id(survey['survey_id'])
                    if survey_info:
                        st.write(f"説明: {survey_info['description']}")
                        st.write(f"回答期限: {survey_info['end_date'] if survey_info['end_date'] else 'なし'}")
                    else:
                        st.write("説明: 取得できませんでした")
                with col2:
                    if st.button("回答を見る", key=f"view_answer_{survey['survey_id']}"):
                        st.session_state.selected_survey_id = survey['survey_id']
                        st.rerun()
        else:
            st.info("まだ回答済みのアンケートはありません。")

def save_current_page_answers(db, survey_id, all_questions_data, survey_data_dict, is_draft):
    user_id = st.session_state.user_info.username
    for q_data in all_questions_data:
        q_id = q_data['question_id']
        st_key = f"q_{q_id}"

        answer_entry = survey_data_dict.get(st_key)
        answer_value = answer_entry.get("value") if answer_entry else None

        if answer_value is not None:
            answer_text = json.dumps(answer_value) if isinstance(answer_value, (list, dict)) else str(answer_value)
            db.save_answer(user_id, survey_id, q_id, answer_text, is_draft=is_draft)
        else:
            # 回答が提供されていない場合（例: ラジオボタンが未選択、テキストエリアが空）
            db.save_answer(user_id, survey_id, q_id, None, is_draft=is_draft)


def set_selected_survey_for_answer_local(survey_id):
    st.session_state.selected_survey_id = survey_id
    st.rerun()