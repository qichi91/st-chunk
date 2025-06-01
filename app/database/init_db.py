from models import Base
from sqlalchemy import create_engine

if __name__ == "__main__":
    engine = create_engine("sqlite:///./survey_app.db")
    Base.metadata.create_all(bind=engine)
    print("DB初期化完了")
