import streamlit as st
import streamlit_survey as ss
import asyncio
import json
import time
from database import models
from database.database import AsyncSessionLocal
from pages.user.answer_mode import AnswerMode

# 回答対象アンケートIDをsession_stateから取得
survey_id = st.session_state.get("answer_survey_id")
if not survey_id:
    st.error("アンケートIDが指定されていません")
    st.stop()

# --- 未回答アンケートの内容を取得し、StreamlitSurveyに設定するJSON ---
async def get_survey_json(survey_id):
    async with AsyncSessionLocal() as session:
        results = await models.get_streamlit_survey_format_json(session, survey_id)
        return results["questions"], results["title"], results["description"]

    
# --- 一時保存、回答済みアンケートの内容を取得し、StreamlitSurveyに設定するJSON ---
async def get_answered_survey_json(survey_id, username):
    async with AsyncSessionLocal() as session:
        # 設問情報を取得
        results = await models.get_streamlit_survey_format_json(session, survey_id)
        # 回答情報を取得（SQLはmodels.pyの新規メソッドを呼び出し）
        answers = await models.get_answers_for_survey_and_user(session, survey_id, username)
        # 回答内容を設問に反映
        for answer, question in answers:
            qid = f"Q{question.page_number}_{question.order_number}"
            if qid in results["questions"]:
                # answer_textがJSONの場合（複数選択肢など）も考慮
                try:
                    value = json.loads(answer.answer_text)
                except Exception:
                    value = answer.answer_text
                results["questions"][qid]["value"] = value
        return results["questions"], results["title"], results["description"]

# アンケートNoが変わった時、カレントページを初期化する
if st.session_state.get("before_answer_survey_id", None) != survey_id:
    st.session_state["before_answer_survey_id"] = survey_id

    # アンケートNoが変わった
    if st.session_state["answer_mode"] == AnswerMode.NEW:
        survey_json, title, description  = asyncio.run(get_survey_json(survey_id))
    else:
        survey_json, title, description  = asyncio.run(get_answered_survey_json(survey_id, getattr(st.user, "name", None)))
    st.session_state["__streamlit-survey-data_アンケート回答"] = survey_json
    st.session_state["__streamlit-survey-data_アンケート回答_Pages_"] = 0
    st.session_state["__streamlit-survey-data_アンケート回答_Title_"] = title
    st.session_state["__streamlit-survey-data_アンケート回答_Description_"] = description

survey_json = st.session_state["__streamlit-survey-data_アンケート回答"]
title = st.session_state["__streamlit-survey-data_アンケート回答_Title_"]
description = st.session_state["__streamlit-survey-data_アンケート回答_Description_"]
survey_widget = ss.StreamlitSurvey("アンケート回答", data=survey_json)

# st.json(survey_json)
st.header(title)
st.write(description)

# jsonの最後の要素のpage_numberを取得して総ページ数を取得
total_page = next(reversed(survey_json.values()), None)["page_number"] if survey_json else 1

# 回答保存用関数
async def save_answers_to_db(survey_id, username, answers, is_draft=False):
    async with AsyncSessionLocal() as session:
        from database.models import Answer, Question
        from sqlalchemy import select, and_
        # 設問リスト取得
        result = await session.execute(
            select(Question).where(Question.survey_id == survey_id)
        )
        questions = result.scalars().all()
        # 既存回答を取得
        result = await session.execute(
            select(Answer, Question)
            .join(Question, Answer.question_id == Question.question_id)
            .where(and_(Question.survey_id == survey_id, Answer.username == username))
        )
        existing_answers = {q.question_id: a for a, q in result.fetchall()}
        # 回答保存
        for q in questions:
            qid = f"Q{q.page_number}_{q.order_number}"
            value = answers.get(qid, None)
            if value is not None:
                if isinstance(value, (list, dict)):
                    value_str = json.dumps(value, ensure_ascii=False)
                else:
                    value_str = str(value)
                if q.question_id in existing_answers:
                    # 既存回答を更新
                    ans = existing_answers[q.question_id]
                    ans.answer_text = value_str
                    ans.is_draft = is_draft
                else:
                    # 新規回答
                    ans = Answer(
                        username=username,
                        question_id=q.question_id,
                        answer_text=value_str,
                        is_draft=is_draft
                    )
                    session.add(ans)
        await session.commit()

# on_submit時の処理

def handle_submit():
    answers = survey_widget.to_json()
    # ここでanswersがstr型ならdictに変換
    if isinstance(answers, str):
        answers = json.loads(answers)
    username = getattr(st.user, "name", None)
    asyncio.run(save_answers_to_db(survey_id, username, {k: v["value"] for k, v in answers.items()}, is_draft=False))
    st.success("回答を保存しました。ありがとうございました。")
    # 回答済みアンケートIDをsession_stateから削除
    st.session_state.pop("answer_survey_id")
    time.sleep(3)  # 少し待ってからページを更新
    st.switch_page("pages/user/user_dashboard.py")

# ページングのon_submitに保存処理を割り当て
pages = survey_widget.pages(total_page, on_submit=handle_submit)

# 次へボタン押下時、カレントページ内のradio設問が未選択なら警告を出し、ページ遷移を抑止するカスタム関数
def next_page_with_radio_check():
    current_page = pages.current + 1
    # カレントページのradio設問を抽出
    radio_questions = [q for q in survey_json.values() if q.get("page_number") == current_page and q.get("type") == "radio"]
    # 未選択のradio設問があるかチェック
    not_selected = [q for q in radio_questions if q.get("value") is None]
    if not_selected:
        st.session_state["is_warning"]=True
    else:
        pages.next()

def next_button(label="次へ"):
    return lambda pages: st.button(
        label,
        use_container_width=True,
        on_click=next_page_with_radio_check,
        disabled=pages.current == pages.n_pages - 1,
        key=f"{pages.current_page_key}_btn_next",
    )

pages.prev_button = pages.default_btn_previous("前へ")
pages.next_button = next_button("次へ")

st.header("")

# 各ページごとに設問をstreamlit-surveyで表示
with pages:
    current_page = pages.current + 1
    # page_numberが一致する要素だけ抽出
    for q in [v for v in survey_json.values() if v.get("page_number") == current_page]:
        order_number = q["widget_key"].split("_")[1]
        qid = q["widget_key"]
        qlabel = q["label"]
        qtype = q["type"]
        options = q.get("options", None)
        value = q.get("value", None)

        # 設問内容を表示
        st.write(f"{order_number} : {qlabel}")
        # 設問の回答形式を表示
        if qtype == "text":
            survey_widget.text_input(
                qlabel, id=qid, key=qid, label_visibility="collapsed", value=value
            )
        elif qtype == "radio":
            survey_widget.radio(
                qlabel, options=options, id=qid, key=qid, label_visibility="collapsed", index=options.index(value) if value in options else None
            )
        elif qtype == "select":
            survey_widget.selectbox(
                qlabel, options=options, id=qid, key=qid, label_visibility="collapsed", index=options.index(value) if value in options else 0
            )
        elif qtype == "multiselect":
            survey_widget.multiselect(
                qlabel, options=options, id=qid, key=qid, label_visibility="collapsed", default=value if value in options else []
            )
        elif qtype == "slider":
            survey_widget.slider(
                qlabel,
                min_value=options[0],
                max_value=options[-1],
                id=qid,
                key=qid,
                label_visibility="collapsed",
                value=value if value else options[0]
            )
        elif qtype == "select_slider":
            survey_widget.select_slider(
                qlabel, options=options, id=qid, key=qid, label_visibility="collapsed", value=value if value else options[0] if options else None
            )
        else:
            survey_widget.text_input(
                qlabel, id=qid, key=qid, label_visibility="collapsed", value=value
            )

if st.button("一時保存"):
    answers = survey_widget.to_json()
    # ここでanswersがstr型ならdictに変換
    if isinstance(answers, str):
        answers = json.loads(answers)
    username = getattr(st.user, "name", None)
    asyncio.run(save_answers_to_db(survey_id, username, {k: v["value"] for k, v in answers.items()}, is_draft=True))
    st.success("一時保存しました。")


if "is_warning" in st.session_state:
    if st.session_state.pop("is_warning"):
        st.warning("未選択の選択肢があります。すべて選択してください。")
