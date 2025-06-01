import streamlit as st
import asyncio
from database import models
from database.database import AsyncSessionLocal
import datetime


# ユーザー名を取得（仮: st.user.username で取得できる想定）
username = getattr(st.user, "name", None)

st.title("ダッシュボード")


# 公開中アンケート・回答済み・一時保存アンケート取得をmodels.pyの関数で呼び出す
async def fetch_open_surveys():
    async with AsyncSessionLocal() as session:
        now = datetime.datetime.now()
        all_surveys = await models.get_open_surveys(session, now)
        # 回答済み・一時保存済みIDを取得
        answered = await models.get_answered_survey_ids(session, username)
        draft = await models.get_draft_survey_ids(session, username)
        # 未回答のみ返す
        return [
            s
            for s in all_surveys
            if (s.survey_id if hasattr(s, "survey_id") else s[0]) not in answered
            and (s.survey_id if hasattr(s, "survey_id") else s[0]) not in draft
        ]


async def fetch_answered_open_surveys():
    async with AsyncSessionLocal() as session:
        now = datetime.datetime.now()
        all_surveys = await models.get_open_surveys(session, now)
        answered = await models.get_answered_survey_ids(session, username)
        # 回答済みかつ公開中
        return [
            s
            for s in all_surveys
            if (s.survey_id if hasattr(s, "survey_id") else s[0]) in answered
        ]


async def fetch_draft_survey_ids(username):
    async with AsyncSessionLocal() as session:
        return await models.get_draft_survey_ids(session, username)


open_surveys = asyncio.run(fetch_open_surveys())
answered_open_surveys = asyncio.run(fetch_answered_open_surveys())
draft_ids = asyncio.run(fetch_draft_survey_ids(username))

# 未回答アンケート一覧
st.subheader("未回答のアンケート")
if open_surveys:
    cols = st.columns([2, 8, 2])
    cols[0].write("###### ID")
    cols[1].write("###### アンケート名")
    cols[2].write("###### ")
    for survey in open_surveys:
        survey_id = survey.survey_id if hasattr(survey, "survey_id") else survey[0]
        title = survey.title if hasattr(survey, "title") else survey[1]
        row = st.columns([2, 8, 2])
        row[0].write(survey_id)
        row[1].write(title)
        if row[2].button("回答する", key=f"answer_{survey_id}"):
            st.session_state["answer_survey_id"] = survey_id
            for key in ["__streamlit-survey-data_アンケート回答"]:
                if key in st.session_state:
                    del st.session_state[key]
                if f"{key}_Pages_" in st.session_state:
                    del st.session_state[f"{key}_Pages_"]

            st.switch_page("pages/user/survey_answer.py")
else:
    st.write("未回答のアンケートはありません")

# 一時保存中アンケート一覧
st.subheader("一時保存中のアンケート")
draft_surveys = [
    s
    for s in open_surveys
    if (s.survey_id if hasattr(s, "survey_id") else s[0]) in draft_ids
]
if draft_surveys:
    cols = st.columns([2, 8, 2])
    cols[0].write("###### ID")
    cols[1].write("###### アンケート名")
    cols[2].write("###### ")
    for survey in draft_surveys:
        survey_id = survey.survey_id if hasattr(survey, "survey_id") else survey[0]
        title = survey.title if hasattr(survey, "title") else survey[1]
        row = st.columns([2, 8, 2])
        row[0].write(survey_id)
        row[1].write(title)
        if row[2].button("回答を再開", key=f"resume_{survey_id}"):
            st.session_state["answer_survey_id"] = survey_id
            for key in ["__streamlit-survey-data_アンケート回答"]:
                if key in st.session_state:
                    del st.session_state[key]
                if f"{key}_Pages_" in st.session_state:
                    del st.session_state[f"{key}_Pages_"]
            st.switch_page("pages/user/survey_answer.py")
else:
    st.write("一時保存中のアンケートはありません")

# 回答済みかつ公開中アンケート一覧
st.subheader("回答済みのアンケート（公開中）")
if answered_open_surveys:
    cols = st.columns([2, 8, 2])
    cols[0].write("###### ID")
    cols[1].write("###### アンケート名")
    cols[2].write("###### ")
    for survey in answered_open_surveys:
        survey_id = survey.survey_id if hasattr(survey, "survey_id") else survey[0]
        title = survey.title if hasattr(survey, "title") else survey[1]
        row = st.columns([2, 8, 2])
        row[0].write(survey_id)
        row[1].write(title)
        if row[2].button("再回答する", key=f"reanswer_{survey_id}"):
            st.session_state["answer_survey_id"] = survey_id
            for key in ["__streamlit-survey-data_アンケート回答"]:
                if key in st.session_state:
                    del st.session_state[key]
                if f"{key}_Pages_" in st.session_state:
                    del st.session_state[f"{key}_Pages_"]
            st.switch_page("pages/user/survey_answer.py")
else:
    st.write("回答済みのアンケート（公開中）はありません")
