from database import models
from database.database import AsyncSessionLocal
from sqlalchemy import update
import streamlit as st
import asyncio
import time
import datetime


# 公開期限設定ダイアログ
@st.dialog("アンケートの公開期限を設定")
def update_end_date(survey):
    # アンケート情報を表示
    st.write(
        f"アンケートID: {survey.survey_id if hasattr(survey, 'survey_id') else survey[0]}"
    )
    st.write(f"アンケート名: {survey.title if hasattr(survey, 'title') else survey[1]}")
    # 公開期限の初期値を設定
    default_dt = (
        survey.end_date
        if hasattr(survey, "end_date") and survey.end_date is not None
        else datetime.datetime.now() + datetime.timedelta(hours=6)
    )
    # 日付・時刻入力
    end_date = st.date_input(
        "公開期限 (年月日)",
        value=default_dt,
        format="YYYY/MM/DD",
    )
    end_time = st.time_input("公開期限 (時分)", value=default_dt)
    if st.button("更新"):
        # 非同期でDB更新
        async def update_survey_end_date():
            async with AsyncSessionLocal() as session:
                end_date_ = datetime.datetime.combine(end_date, end_time)
                stmt = (
                    update(models.Survey)
                    .where(
                        models.Survey.survey_id
                        == (
                            survey.survey_id
                            if hasattr(survey, "survey_id")
                            else survey[0]
                        )
                    )
                    .values(end_date=end_date_)
                )
                await session.execute(stmt)
                await session.commit()
            st.success("アンケートの公開期限を更新しました")
            # 少し待ってリロード
            time.sleep(2)
            st.rerun()

        asyncio.run(update_survey_end_date())


# アンケート複製ダイアログ
@st.dialog("アンケートの複製")
def copy_survey(survey):
    st.write(
        f"アンケートID: {survey.survey_id if hasattr(survey, 'survey_id') else survey[0]}"
    )
    if st.button("複製"):
        # 非同期で複製処理
        async def copy_survey_to_new_situation(survey):
            async with AsyncSessionLocal() as session:
                # 新しいアンケートを作成
                new_survey = models.Survey(
                    title=f"{survey.title if hasattr(survey, 'title') else survey[1]} (複製)",
                    description=survey.description
                    if hasattr(survey, "description")
                    else survey[2],
                    created_at=datetime.datetime.now(),
                    end_date=survey.end_date
                    if hasattr(survey, "end_date")
                    else survey[4],
                )
                session.add(new_survey)
                await session.commit()
                await session.refresh(new_survey)

                # 元のアンケートの質問をDBから取得し複製
                orig_survey_id = (
                    survey.survey_id if hasattr(survey, "survey_id") else survey[0]
                )
                result = await session.execute(
                    models.Question.__table__.select().where(
                        models.Question.survey_id == orig_survey_id
                    )
                )
                questions = result.fetchall()
                for q in questions:
                    session.add(
                        models.Question(
                            survey_id=new_survey.survey_id,
                            question_text=q.question_text
                            if hasattr(q, "question_text")
                            else q[2],
                            question_type=q.question_type
                            if hasattr(q, "question_type")
                            else q[3],
                            options=q.options if hasattr(q, "options") else q[4],
                            order_number=q.order_number
                            if hasattr(q, "order_number")
                            else q[5],
                            page_number=q.page_number
                            if hasattr(q, "page_number")
                            else q[6],
                            image=q.image if hasattr(q, "image") else q[7],
                        )
                    )
                await session.commit()

            st.success(f"アンケートID( {new_survey.survey_id} )として複製しました")
            # 少し待ってリロード
            time.sleep(3)
            st.rerun()

        asyncio.run(copy_survey_to_new_situation(survey))


# アンケート削除ダイアログ
@st.dialog("アンケートの削除")
def confirm_delete_survey(survey):
    st.write(
        f"アンケートID: {survey.survey_id if hasattr(survey, 'survey_id') else survey[0]}"
    )
    if st.button("削除"):
        # 非同期で削除処理
        async def delete_survey(survey):
            async with AsyncSessionLocal() as session:
                stmt = models.Survey.__table__.delete().where(
                    models.Survey.survey_id
                    == (survey.survey_id if hasattr(survey, "survey_id") else survey[0])
                )
                await session.execute(stmt)
                await session.commit()
            st.success("アンケートを削除しました")
            # 少し待ってリロード
            time.sleep(2)
            st.rerun()

        asyncio.run(delete_survey(survey))


# アンケート管理ページ本体
st.title("アンケート管理")


# アンケート一覧をDBから取得
async def fetch_surveys():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            models.Survey.__table__.select().order_by(models.Survey.survey_id)
        )
        return result.fetchall()


surveys = asyncio.run(fetch_surveys())

st.subheader("アンケート一覧")

# 一覧ヘッダー
cols = st.columns([1, 7, 3, 3, 4])
cols[0].write("###### ID")
cols[1].write("###### アンケート名")
cols[2].write("###### 作成日")
cols[3].write("###### 公開期限")
cols[4].write("###### ")

# 各アンケート行を表示
for survey in surveys:
    # surveyはRow型またはORM型のどちらか
    survey_id = survey.survey_id if hasattr(survey, "survey_id") else survey[0]
    title = survey.title if hasattr(survey, "title") else survey[1]
    created_at = survey.created_at if hasattr(survey, "created_at") else survey[3]
    end_date = survey.end_date if hasattr(survey, "end_date") else survey[4]
    cols = st.columns([1, 7, 3, 3, 1, 1, 1, 1])
    cols[0].write(survey_id)  # アンケートID
    cols[1].write(title)  # アンケート名
    cols[2].write(
        created_at.strftime("%Y/%m/%d %H:%M") if created_at else "--"
    )  # 作成日
    cols[3].write(end_date.strftime("%Y/%m/%d %H:%M") if end_date else "--")  # 公開期限
    # 公開ボタン
    if cols[4].button(
        ":material/publish:", key=f"publish_{survey_id}", help="アンケートを公開"
    ):
        update_end_date(survey)
    # 編集ボタン
    if cols[5].button(
        ":material/edit:", key=f"edit_{survey_id}", help="アンケートを編集"
    ):
        # 編集対象のアンケートデータをsession_stateに格納し、編集ページへ遷移
        st.session_state.survey_data = survey
        st.switch_page("pages/admin/survey_edit.py")
    # 複製ボタン
    if cols[6].button(
        ":material/content_copy:", key=f"copy_{survey_id}", help="アンケートを複製"
    ):
        copy_survey(survey)
    # 削除ボタン
    if cols[7].button(
        ":material/delete:", key=f"delete_{survey_id}", help="アンケートを削除"
    ):
        confirm_delete_survey(survey)
