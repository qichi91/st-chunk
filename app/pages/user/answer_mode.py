from enum import Enum

class AnswerMode(Enum):
    NEW = "NEW"         # 未回答アンケートへの新規回答
    RESUME = "RESUME"   # 一時保存中アンケートの再開
    REANSWER = "REANSWER" # 回答済みアンケートへの再回答
