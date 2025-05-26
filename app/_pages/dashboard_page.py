import streamlit as st
from datetime import datetime

def show_page(db):
    st.title("ダッシュボード")

    user_info = st.session_state.user_info
    if not user_info:
        st.warning("ユーザー情報がありません。ログインしてください。")
        return

    username = user_info['username']
    st.write(f"**ようこそ、{username}さん！** アンケートの状況を確認できます。")

    st.markdown("---")
    st.subheader("未回答のアンケート")
    display_unanswered_surveys(db, username)

    st.markdown("---")
    st.subheader("一時保存中のアンケート")
    display_draft_surveys(db, username)

    st.markdown("---")
    st.subheader("回答済みのアンケート")
    display_answered_surveys(db, username)


def display_unanswered_surveys(db, username):
    today = datetime.now().strftime('%Y-%m-%d')
    # 未回答かつ公開中のアンケートを取得
    # draftsでもsubmittedでもないアンケートのみを対象とする
    conn = db.conn # Databaseクラスの既存コネクションを使用
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
        WHERE submitted_answers.survey_id IS NULL -- 提出済みではない
          AND draft_answers.survey_id IS NULL      -- 一時保存でもない
          AND (s.end_date IS NULL OR s.end_date >= ?) -- 期限切れではないか、期限が設定されていない
        ORDER BY s.survey_id ASC
    """, (username, username, today))
    
    unanswered_surveys = [dict(row) for row in cursor.fetchall()]

    if unanswered_surveys:
        for survey in unanswered_surveys:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{survey['title']}** (ID: {survey['survey_id']})")
                st.write(f"説明: {survey['description']}")
                st.write(f"回答期限: {survey['end_date'] if survey['end_date'] else 'なし'}")
            with col2:
                if st.button("回答を開始", key=f"start_answer_{survey['survey_id']}"):
                    set_selected_survey_for_answer(survey['survey_id'])
    else:
        st.info("現在、回答可能な新しいアンケートはありません。")


def display_draft_surveys(db, username):
    draft_surveys = db.get_user_draft_surveys(username)

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
                    set_selected_survey_for_answer(survey['survey_id'])
    else:
        st.info("一時保存中のアンケートはありません。")

def display_answered_surveys(db, username):
    answered_surveys = db.get_user_answered_surveys(username)

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
                # 回答済みのアンケートは閲覧のみと想定。
                # ただし、回答期限内であれば再編集可能にするロジックは answer_page 側で制御されるため、
                # ここではボタンで遷移させるのみ。
                if st.button("回答を見る", key=f"view_answer_{survey['survey_id']}"):
                    set_selected_survey_for_answer(survey['survey_id'])
    else:
        st.info("まだ回答済みのアンケートはありません。")

def set_selected_survey_for_answer(survey_id):
    """
    選択されたアンケートIDをセッション状態に保存し、回答ページに遷移する。
    """
    st.session_state.selected_survey_id = survey_id
    st.session_state.page = "answer"
    st.rerun()