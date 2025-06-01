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
    stmt = select(Survey).where((Survey.survey_id == survey_id))
    result = await session.execute(stmt)

    json_data = {}

    for survey in result.scalars().all():
        for i, question in enumerate(survey.questions):
            json_data[f"Q{i + 1}"] = {
                "label": question.question_text,
                "options": question.options,
            }
        #     question_data = {
        #         "question_id": question.question_id,
        #         "question_text": question.question_text,
        #         "question_type": question.question_type,
        #         "options": question.options,
        #         "order_number": question.order_number,
        #         "page_number": question.page_number,
        #     }
        #     if question.image:
        #         question_data["image"] = question.image

        #     if survey.survey_id not in json_data:
        #         json_data[survey.survey_id] = {
        #             "title": survey.title,
        #             "description": survey.description,
        #             "questions": []
        #         }
        #     json_data[survey.survey_id]["questions"].append(question_data)
        # survey_id = survey.survey_id if hasattr(survey, "survey_id") else survey[0]
        # title = survey.title if hasattr(survey, "title") else survey[1]

    return json_data
