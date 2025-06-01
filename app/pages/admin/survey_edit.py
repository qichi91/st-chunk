from database import models
from database.database import AsyncSessionLocal
import streamlit as st
import json
import asyncio
import time

# survey_admin.pyの編集ボタンからsurveyを受け取る想定

st.title("アンケート編集")

# session_stateの内容をデバッグ表示
st.write(st.session_state)

# 他ページから遷移する時のsession_state
# ページ遷移したらsurvey_dataを消したいのでpopさせる
survey = st.session_state.pop("survey_data", None)

# 更新したアンケートパラメータのsession_state
survey_id = st.session_state.pop("survey_id", None)
new_title = st.session_state.pop("new_title", None)
new_description = st.session_state.pop("new_description", None)
survey_json = st.session_state.pop("survey_json", None)
# 設問を編集したか？
if survey_id and new_title and new_description and survey_json:
    # アンケート更新処理
    async def update(survey_id, new_title, new_description, survey_json):
        try:
            survey_json = json.loads(survey_json)
        except Exception as e:
            st.error(f"JSONデータが不正です: {e}")
            st.stop()
        async with AsyncSessionLocal() as session:
            # アンケート本体を更新
            await session.execute(
                models.Survey.__table__.update()
                .where(models.Survey.survey_id == survey_id)
                .values(title=new_title, description=new_description)
            )
            # 既存の質問を削除
            await session.execute(
                models.Question.__table__.delete().where(
                    models.Question.survey_id == survey_id
                )
            )
            # 新しい質問を追加
            for idx, q in enumerate(survey_json.get("questions", [])):
                question = models.Question(
                    survey_id=survey_id,
                    question_text=q.get("label", ""),
                    question_type=q.get("type", "text"),
                    options=json.dumps(q.get("options")) if q.get("options") else None,
                    order_number=idx + 1,
                    page_number=q.get("page", 1),
                )
                session.add(question)
            await session.commit()
        st.success("アンケートを更新しました")
        time.sleep(2)  # 少し待ってからページを更新
        st.switch_page("pages/admin/survey_admin.py")

    asyncio.run(update(survey_id, new_title, new_description, survey_json))

# 設問を編集していないし、設問管理から遷移してきていなければエラー
if survey is None:
    st.error("編集対象のアンケートが指定されていません")
    st.stop()

#
# 設問管理ページから遷移した時の処理
#

# surveyはRow型またはORM型のどちらか
survey_id = survey.survey_id if hasattr(survey, "survey_id") else survey[0]
title = survey.title if hasattr(survey, "title") else survey[1]
description = survey.description if hasattr(survey, "description") else survey[2]


# DBから質問リストを取得
async def fetch_questions():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            models.Question.__table__.select().where(
                models.Question.survey_id == survey_id
            )
        )
        return result.fetchall()


questions = asyncio.run(fetch_questions())


# JSON形式に変換
def questions_to_json(questions):
    qlist = []
    for q in questions:
        qlist.append(
            {
                "type": q.question_type if hasattr(q, "question_type") else q[3],
                "name": f"Q{q.order_number if hasattr(q, 'order_number') else q[5]}",
                "label": q.question_text if hasattr(q, "question_text") else q[2],
                "options": json.loads(q.options)
                if (hasattr(q, "options") and q.options)
                or (not hasattr(q, "options") and q[4])
                else None,
                "page": q.page_number if hasattr(q, "page_number") else q[6],
            }
        )
    return {"questions": qlist}


# 編集フォーム
with st.form("my_form"):
    questions_json = questions_to_json(questions)
    json_str = json.dumps(questions_json, ensure_ascii=False, indent=2)

    # 入力フォーム
    survey_id = st.text_input(
        "アンケートID", value=survey_id, disabled=True, key="survey_id"
    )
    new_title = st.text_input("アンケート名", value=title, key="new_title")
    new_description = st.text_area(
        "アンケートの説明", value=description, key="new_description"
    )
    survey_json = st.text_area(
        "アンケート内容のJSONデータ (streamlit-survey形式)",
        value=json_str,
        height=200,
        key="survey_json",
    )

    submitted = st.form_submit_button("更新")
