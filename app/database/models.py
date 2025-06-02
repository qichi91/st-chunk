from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    BLOB,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.future import select
import json

Base = declarative_base()


class Survey(Base):
    __tablename__ = "surveys"
    survey_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    questions = relationship(
        "Question", back_populates="survey", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"
    question_id = Column(Integer, primary_key=True, autoincrement=True)
    survey_id = Column(Integer, ForeignKey("surveys.survey_id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(Text, nullable=False)
    options = Column(Text, nullable=True)  # JSON形式の選択肢
    order_number = Column(Integer, nullable=True)
    page_number = Column(Integer, nullable=True)
    image = Column(BLOB, nullable=True)
    survey = relationship("Survey", back_populates="questions")
    answers = relationship(
        "Answer", back_populates="question", cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"
    answer_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Text, nullable=False)
    question_id = Column(Integer, ForeignKey("questions.question_id"), nullable=False)
    answer_text = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    is_draft = Column(Boolean, nullable=False, default=True)
    question = relationship("Question", back_populates="answers")


# 公開中アンケート一覧を取得するクエリ
async def get_open_surveys(session, now):
    stmt = select(Survey).where((Survey.end_date > now))
    result = await session.execute(stmt)
    return result.scalars().all()


# 回答済みアンケートIDリスト（is_draft=False）
async def get_answered_survey_ids(session, username):
    from sqlalchemy import and_

    stmt = (
        select(Question.survey_id)
        .join(Answer, Question.question_id == Answer.question_id)
        .where(and_(Answer.username == username, ~Answer.is_draft))
    )
    result = await session.execute(stmt)
    return set(row[0] for row in result.fetchall())


# 一時保存中アンケートIDリスト（is_draft=True）
async def get_draft_survey_ids(session, username):
    from sqlalchemy import and_

    stmt = (
        select(Question.survey_id)
        .join(Answer, Question.question_id == Answer.question_id)
        .where(and_(Answer.username == username, Answer.is_draft))
    )
    result = await session.execute(stmt)
    return set(row[0] for row in result.fetchall())


# streamlit-survey形式のアンケートデータ
async def get_streamlit_survey_format_json(session, survey_id):
    from sqlalchemy import select
    # Survey本体も取得
    survey_result = await session.execute(select(Survey).where(Survey.survey_id == survey_id))
    survey = survey_result.scalar_one_or_none()
    result = await session.execute(
        select(Question).where(Question.survey_id == survey_id).order_by(Question.page_number, Question.order_number)
    )
    questions = result.scalars().all()
    survey_json = {}
    for q in questions:
        qid = f"Q{q.page_number}_{q.order_number}"
        qdata = {
            "label": q.question_text,
            "widget_key": qid,
            "value": None,
            "type": q.question_type,
            "page_number": q.page_number,
        }
        # 選択肢がある場合はoptionsを追加
        if q.options:
            try:
                qdata["options"] = json.loads(q.options)
            except Exception:
                qdata["options"] = []
        survey_json[qid] = qdata
    # title, descriptionも返す
    return {
        "title": survey.title if survey else None,
        "description": survey.description if survey else None,
        "questions": survey_json
    }


# 指定ユーザーのアンケート回答（設問情報も含めて返す）
async def get_answers_for_survey_and_user(session, survey_id, username):
    from sqlalchemy import select, and_
    # AnswerとQuestionをjoinし、該当survey_id, usernameの回答を取得
    stmt = (
        select(Answer, Question)
        .join(Question, Answer.question_id == Question.question_id)
        .where(and_(Question.survey_id == survey_id, Answer.username == username))
    )
    result = await session.execute(stmt)
    return result.fetchall()