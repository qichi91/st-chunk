import streamlit as st
import asyncio
from database import models
from database.database import AsyncSessionLocal
import datetime
import json

username = getattr(st.user, "name", None)

st.title("回答履歴")

async def fetch_answered_surveys():
    async with AsyncSessionLocal() as session:
        # 回答済みアンケートID取得
        answered_ids = await models.get_answered_survey_ids(session, username)
        # アンケート本体取得
        surveys = []
        for sid in answered_ids:
            survey_data = await models.get_streamlit_survey_format_json(session, sid)
            # 最新の回答日取得
            answers = await models.get_answers_for_survey_and_user(session, sid, username)
            if answers:
                latest = max([a.submitted_at for a, _ in answers if a.submitted_at])
            else:
                latest = None
            surveys.append({
                "survey_id": sid,
                "title": survey_data["title"],
                "answered_at": latest,
            })
        return surveys

answered_surveys = asyncio.run(fetch_answered_surveys())

async def fetch_survey_detail(survey_id, username):
    async with AsyncSessionLocal() as session:
        survey_data = await models.get_streamlit_survey_format_json(session, survey_id)
        answers = await models.get_answers_for_survey_and_user(session, survey_id, username)
        # 設問順に並べる
        questions = survey_data["questions"]
        detail = []
        for qid, q in questions.items():
            # 回答を探す
            answer_val = None
            for a, question in answers:
                if f"Q{question.page_number}_{question.order_number}" == qid:
                    try:
                        answer_val = json.loads(a.answer_text)
                    except Exception:
                        answer_val = a.answer_text
            detail.append({
                "label": q["label"],
                "value": answer_val
            })
        return detail

# ダイアログでアンケート内容を表示する関数
@st.dialog("アンケート内容の確認")
def show_survey_detail_dialog():
    survey_id = st.session_state.get("dialog_survey_id")
    survey_title = st.session_state.get("dialog_survey_title")
    if not survey_id:
        st.write("データがありません")
        return
    st.write(f"アンケートID: {survey_id}")
    st.write(f"アンケート名: {survey_title}")
    details = asyncio.run(fetch_survey_detail(survey_id, username))
    for d in details:
        st.write(f"- {d['label']}")
        st.write(f"  回答: {d['value'] if d['value'] is not None else '-'}")

st.subheader("あなたが回答したアンケート一覧")
if answered_surveys:
    cols = st.columns([2, 6, 3, 2])
    cols[0].write("###### ID")
    cols[1].write("###### アンケート名")
    cols[2].write("###### 回答日")
    cols[3].write("###### ")
    for s in answered_surveys:
        row = st.columns([2, 6, 3, 2])
        row[0].write(s["survey_id"])
        row[1].write(s["title"])
        row[2].write(s["answered_at"].strftime("%Y-%m-%d %H:%M") if s["answered_at"] else "-")
        if row[3].button("内容の確認", key=f"check_{s['survey_id']}"):
            st.session_state["dialog_survey_id"] = s["survey_id"]
            st.session_state["dialog_survey_title"] = s["title"]
            show_survey_detail_dialog()
else:
    st.write("まだ回答したアンケートはありません")
