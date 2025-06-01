# Streamlitによるアンケート作成ページ
import streamlit as st
from datetime import datetime as dt

# ページタイトル
st.title("アンケート作成")
# アンケート名入力欄
title = st.text_input("アンケート名")
# アンケート説明入力欄
description = st.text_area("アンケートの説明")
# アンケート内容（JSON形式）入力欄
json_data = st.text_area(
    "アンケート内容のJSONデータ (streamlit-survey形式)",
    height=200,
    placeholder='{"questions": [{"type": "text", "name": "Q1", "label": "質問1"}]}',
)
# 作成ボタン
submit = st.button("作成")

if submit:
    import json
    from database import models
    from database.database import AsyncSessionLocal
    import asyncio

    # 入力バリデーション: アンケート名必須
    if not title:
        st.error("アンケート名は必須です")
        st.stop()
    try:
        # JSONデータのパース
        survey_json = json.loads(json_data)
    except Exception as e:
        st.error(f"JSONデータが不正です: {e}")
        st.stop()

    # 非同期でDBにアンケートを保存
    async def save_survey():
        async with AsyncSessionLocal() as session:
            # Surveyテーブルに新規レコード追加
            survey = models.Survey(
                title=title,
                description=description,
                created_at=dt.now(),
            )
            session.add(survey)
            await session.flush()  # survey_id取得のため
            # 質問リストをQuestionテーブルに保存
            for idx, q in enumerate(survey_json.get("questions", [])):
                question = models.Question(
                    survey_id=survey.survey_id,
                    question_text=q.get("label", ""),
                    question_type=q.get("type", "text"),
                    options=json.dumps(q.get("options")) if q.get("options") else None,
                    order_number=idx + 1,
                    page_number=q.get("page", 1),
                )
                session.add(question)
            await session.commit()
        st.success("アンケートを作成しました")

    asyncio.run(save_survey())
