import streamlit as st
import streamlit_survey as ss
import asyncio
from database import models
from database.database import AsyncSessionLocal
import json
import datetime

# 回答対象アンケートIDをsession_stateから取得
survey_id = st.session_state.get("answer_survey_id")
if not survey_id:
    st.error("アンケートIDが指定されていません")
    st.stop()

st.write(st.session_state)


# DBからアンケート情報と設問リストを取得
async def fetch_survey_and_questions(survey_id):
    async with AsyncSessionLocal() as session:
        survey_result = await session.execute(
            models.Survey.__table__.select().where(models.Survey.survey_id == survey_id)
        )
        survey = survey_result.fetchone()
        questions_result = await session.execute(
            models.Question.__table__.select()
            .where(models.Question.survey_id == survey_id)
            .order_by(models.Question.order_number)
        )
        questions = questions_result.fetchall()
        return survey, questions


survey, questions = asyncio.run(fetch_survey_and_questions(survey_id))

if not survey:
    st.error("アンケートが見つかりません")
    st.stop()

# アンケートタイトル・説明
st.title(survey.title if hasattr(survey, "title") else survey[1])
# st.write(survey.description if hasattr(survey, "description") else survey[2])

# st.write(questions)


# streamlit-survey形式のJSONに変換
def questions_to_json(questions):
    qlist = {}
    for q in questions:
        qlist[f"Q{q.order_number if hasattr(q, 'order_number') else q[5]}"] = {
            "type": q.question_type if hasattr(q, "question_type") else q[3],
            "label": q.question_text if hasattr(q, "question_text") else q[2],
            "options": json.loads(q.options)
            if (hasattr(q, "options") and q.options)
            or (not hasattr(q, "options") and q[4])
            else None,
            "page": q.page_number if hasattr(q, "page_number") else q[6],
        }

    return qlist


survey_json = questions_to_json(questions)

# st.write(survey_json)

# streamlit-survey形式のページング表示
survey_widget = ss.StreamlitSurvey("アンケート回答")

# # Update survey data
# survey_widget.data.clear()
# survey_widget.data.update(survey_json)

# # Update displayed Streamlit widgets values
# for _, data in survey_widget.data.items():
#     if "widget_key" in data and data["widget_key"] in st.session_state:
#         st.session_state[data["widget_key"]] = data["value"]


# 設問をページごとにグループ化


def group_questions_by_page(questions):
    qlist = {}
    for q in questions:
        page = q.page_number if hasattr(q, "page_number") else q[6] - 1
        if page not in qlist:
            qlist[page] = {}
        order = q.order_number if hasattr(q, "order_number") else q[5]
        if order not in qlist[page]:
            qlist[page][order] = {}
        qlist[page][order] = {
            "type": q.question_type if hasattr(q, "question_type") else q[3],
            "label": q.question_text if hasattr(q, "question_text") else q[2],
            "options": json.loads(q.options)
            if (hasattr(q, "options") and q.options)
            or (not hasattr(q, "options") and q[4])
            else None,
        }

    return qlist


def submit():
    # 回答をDBに提出（is_draft=False）
    async def submit_answers():
        async with AsyncSessionLocal() as session:
            responses = json.loads(survey_widget.to_json())
            st.json(responses)
            st.write("---")
            st.json(questions)
            st.write("---")
            for q in questions:
                page = q.page_number if hasattr(q, "page_number") else q[6]
                order = q.order_number if hasattr(q, "order_number") else q[5]
                qkey = f"Q{page}_{order}"
                st.write(qkey)
                answer_text = responses.get(qkey, {}).get("value", "")
                from sqlalchemy import and_

                result = await session.execute(
                    models.Answer.__table__.select().where(
                        and_(
                            models.Answer.username == getattr(st.user, "name", ""),
                            models.Answer.question_id
                            == (q.question_id if hasattr(q, "question_id") else q[0]),
                        )
                    )
                )
                answer = result.fetchone()
                if answer:
                    await session.execute(
                        models.Answer.__table__.update()
                        .where(
                            models.Answer.answer_id
                            == (
                                answer.answer_id
                                if hasattr(answer, "answer_id")
                                else answer[0]
                            )
                        )
                        .values(
                            answer_text=answer_text,
                            submitted_at=datetime.datetime.now(),
                            is_draft=False,
                        )
                    )
                else:
                    session.add(
                        models.Answer(
                            username=getattr(st.user, "name", ""),
                            question_id=(
                                q.question_id if hasattr(q, "question_id") else q[0]
                            ),
                            answer_text=answer_text,
                            submitted_at=datetime.datetime.now(),
                            is_draft=False,
                        )
                    )
            await session.commit()
        st.success("提出しました")

    asyncio.run(submit_answers())


pages_questions = group_questions_by_page(questions)
num_pages = len(pages_questions)
pages = survey_widget.pages(
    num_pages,
    on_submit=submit,
    # st.success("ご回答ありがとうございました。")
)

# st.write(pages_questions)
# 各ページごとに設問をstreamlit-surveyで表示
with pages:
    current_page = pages.current

    for order_number in pages_questions[current_page + 1]:
        q = pages_questions[current_page + 1][order_number]
        qid = f"Q{current_page + 1}_{order_number}"
        qtype = q["type"] if "type" in q else q[3]
        qname = q["label"] if "label" in q else q[2]
        options = q["options"] if "options" in q else None
        st.write(f"{order_number} : {qname}")
        if qtype == "text":
            survey_widget.text_input(
                qname, id=qid, key=qid, label_visibility="collapsed"
            )
        elif qtype == "radio":
            survey_widget.radio(
                qname, options=options, id=qid, key=qid, label_visibility="collapsed"
            )
        elif qtype == "select":
            survey_widget.selectbox(
                qname, options=options, id=qid, key=qid, label_visibility="collapsed"
            )
        elif qtype == "multiselect":
            survey_widget.multiselect(
                qname, options=options, id=qid, key=qid, label_visibility="collapsed"
            )
        elif qtype == "slider":
            survey_widget.slider(
                qname,
                min_value=options[0],
                max_value=options[-1],
                id=qid,
                key=qid,
                label_visibility="collapsed",
            )
        elif qtype == "select_slider":
            survey_widget.select_slider(
                qname, options=options, id=qid, key=qid, label_visibility="collapsed"
            )
        else:
            survey_widget.text_input(
                qname, id=qid, key=qid, label_visibility="collapsed"
            )

# 回答保存ボタン
if st.button("一時保存"):
    # 回答をDBに一時保存（is_draft=True）
    async def save_answers():
        # 回答データを取得（to_jsonで内部データ取得可能）
        responses = json.loads(survey_widget.to_json())
        async with AsyncSessionLocal() as session:
            for q in questions:
                # Q{page_number}_{order_number} 形式のキーを生成
                page = q.page_number if hasattr(q, "page_number") else q[6]
                order = q.order_number if hasattr(q, "order_number") else q[5]
                qkey = f"Q{page}_{order}"
                answer_text = responses.get(qkey, {}).get("value", "")
                from sqlalchemy import and_

                result = await session.execute(
                    models.Answer.__table__.select().where(
                        and_(
                            models.Answer.username == getattr(st.user, "name", ""),
                            models.Answer.question_id
                            == (q.question_id if hasattr(q, "question_id") else q[0]),
                            models.Answer.is_draft,
                        )
                    )
                )
                answer = result.fetchone()
                if answer:
                    await session.execute(
                        models.Answer.__table__.update()
                        .where(
                            models.Answer.answer_id
                            == (
                                answer.answer_id
                                if hasattr(answer, "answer_id")
                                else answer[0]
                            )
                        )
                        .values(
                            answer_text=answer_text,
                            submitted_at=datetime.datetime.now(),
                        )
                    )
                else:
                    session.add(
                        models.Answer(
                            username=getattr(st.user, "name", ""),
                            question_id=(
                                q.question_id if hasattr(q, "question_id") else q[0]
                            ),
                            answer_text=answer_text,
                            submitted_at=datetime.datetime.now(),
                            is_draft=True,
                        )
                    )
            await session.commit()
        st.success("一時保存しました")

    asyncio.run(save_answers())
