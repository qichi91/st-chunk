import sqlite3
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="survey_app.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()

    def connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def create_tables(self):
        self.connect()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS surveys (
                survey_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                end_date TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                survey_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT NOT NULL, -- 'text', 'single', 'multi'
                options TEXT, -- JSON string for single/multi choice
                order_number INTEGER NOT NULL,
                page_number INTEGER NOT NULL DEFAULT 1,
                image_data BLOB,
                FOREIGN KEY (survey_id) REFERENCES surveys (survey_id) ON DELETE CASCADE
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                survey_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer_text TEXT,
                submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_draft BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (survey_id) REFERENCES surveys (survey_id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions (question_id) ON DELETE CASCADE,
                UNIQUE (username, survey_id, question_id)
            )
        """)
        self.conn.commit()

    def create_survey(self, title, description, end_date):
        self.connect()
        self.cursor.execute("INSERT INTO surveys (title, description, end_date) VALUES (?, ?, ?)",
                            (title, description, end_date))
        self.conn.commit()
        return self.cursor.lastrowid

    def update_survey(self, survey_id, title, description, end_date):
        self.connect()
        self.cursor.execute("UPDATE surveys SET title = ?, description = ?, end_date = ? WHERE survey_id = ?",
                            (title, description, end_date, survey_id))
        self.conn.commit()

    def delete_survey(self, survey_id):
        self.connect()
        self.cursor.execute("DELETE FROM surveys WHERE survey_id = ?", (survey_id,))
        self.conn.commit()

    def get_all_surveys(self):
        self.connect()
        self.cursor.execute("SELECT survey_id, title, description, created_at, end_date FROM surveys ORDER BY created_at DESC")
        return [dict(row) for row in self.cursor.fetchall()]

    def get_survey_by_id(self, survey_id):
        self.connect()
        self.cursor.execute("SELECT survey_id, title, description, created_at, end_date FROM surveys WHERE survey_id = ?", (survey_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def add_question(self, survey_id, question_text, question_type, options, order_number, page_number, image_data=None):
        self.connect()
        options_json = json.dumps(options) if options else None
        self.cursor.execute(
            "INSERT INTO questions (survey_id, question_text, question_type, options, order_number, page_number, image_data) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (survey_id, question_text, question_type, options_json, order_number, page_number, image_data)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def update_question(self, question_id, question_text, question_type, options, order_number, page_number, image_data):
        self.connect()
        options_json = json.dumps(options) if options else None
        self.cursor.execute(
            "UPDATE questions SET question_text = ?, question_type = ?, options = ?, order_number = ?, page_number = ?, image_data = ? WHERE question_id = ?",
            (question_text, question_type, options_json, order_number, page_number, image_data, question_id)
        )
        self.conn.commit()

    def delete_question(self, question_id):
        self.connect()
        self.cursor.execute("DELETE FROM questions WHERE question_id = ?", (question_id,))
        self.conn.commit()

    def get_survey_questions(self, survey_id):
        self.connect()
        self.cursor.execute("SELECT * FROM questions WHERE survey_id = ? ORDER BY page_number, order_number", (survey_id,))
        questions = []
        for row in self.cursor.fetchall():
            q_dict = dict(row)
            if q_dict['options']:
                q_dict['options'] = json.loads(q_dict['options'])
            # image_dataはそのまま
            questions.append(q_dict)
        return questions

    def get_question_by_id(self, question_id):
        self.connect()
        self.cursor.execute("SELECT * FROM questions WHERE question_id = ?", (question_id,))
        row = self.cursor.fetchone()
        if row:
            q_dict = dict(row)
            if q_dict['options']:
                q_dict['options'] = json.loads(q_dict['options'])
            return q_dict
        return None

    def get_max_order_number(self, survey_id, page_number):
        self.connect()
        self.cursor.execute("SELECT MAX(order_number) FROM questions WHERE survey_id = ? AND page_number = ?", (survey_id, page_number))
        result = self.cursor.fetchone()[0]
        return result if result is not None else 0

    def get_max_page_number(self, survey_id):
        self.connect()
        self.cursor.execute("SELECT MAX(page_number) FROM questions WHERE survey_id = ?", (survey_id,))
        result = self.cursor.fetchone()[0]
        return result if result is not None else 0

    def save_answer(self, username, survey_id, question_id, answer_text, is_draft=True):
        self.connect()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute("""
            INSERT INTO answers (username, survey_id, question_id, answer_text, submitted_at, is_draft)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(username, survey_id, question_id) DO UPDATE SET
                answer_text = EXCLUDED.answer_text,
                submitted_at = ?,
                is_draft = EXCLUDED.is_draft
        """, (username, survey_id, question_id, answer_text, current_time, is_draft, current_time))
        self.conn.commit()

    def get_user_answers_for_survey(self, username, survey_id):
        self.connect()
        self.cursor.execute("""
            SELECT
                q.question_id,
                q.question_text,
                q.question_type,
                q.options,
                q.order_number,
                q.page_number,
                q.image_url,
                a.answer_text,
                a.is_draft,
                a.submitted_at
            FROM questions q
            LEFT JOIN answers a ON q.question_id = a.question_id AND a.username = ? AND a.survey_id = ?
            WHERE q.survey_id = ?
            ORDER BY q.page_number, q.order_number
        """, (username, survey_id, survey_id))
        results = []
        for row in self.cursor.fetchall():
            row_dict = dict(row)
            if row_dict['options']:
                row_dict['options'] = json.loads(row_dict['options'])
            results.append(row_dict)
        return results

    def get_all_answers_for_survey(self, survey_id):
        self.connect()
        self.cursor.execute("""
            SELECT
                a.username,
                q.question_text,
                q.question_type,
                q.options,
                a.answer_text,
                a.submitted_at,
                a.is_draft
            FROM answers a
            JOIN questions q ON a.question_id = q.question_id
            WHERE a.survey_id = ? AND a.is_draft = FALSE
            ORDER BY a.username, q.order_number
        """, (survey_id,))
        results = []
        for row in self.cursor.fetchall():
            row_dict = dict(row)
            if row_dict['options']:
                row_dict['options'] = json.loads(row_dict['options'])
            results.append(row_dict)
        return results

    def get_user_unanswered_surveys(self, username):
        self.connect()
        self.cursor.execute("""
            SELECT s.survey_id, s.title, s.description, s.end_date
            FROM surveys s
            WHERE (s.end_date IS NULL OR s.end_date >= ?)
              AND s.survey_id NOT IN (
                SELECT survey_id
                FROM answers
                WHERE username = ? AND is_draft = FALSE AND answer_text IS NOT NULL
              )
            ORDER BY s.end_date ASC
        """, (datetime.now().strftime('%Y-%m-%d'), username))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_user_answered_surveys(self, username):
        self.connect()
        self.cursor.execute("""
            SELECT DISTINCT s.survey_id, s.title
            FROM answers a
            JOIN surveys s ON a.survey_id = s.survey_id
            WHERE a.username = ? AND a.is_draft = FALSE AND a.answer_text IS NOT NULL
        """, (username,))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_user_draft_surveys(self, username):
        self.connect()
        self.cursor.execute("""
            SELECT DISTINCT s.survey_id, s.title
            FROM answers a
            JOIN surveys s ON a.survey_id = s.survey_id
            WHERE a.username = ? AND a.is_draft = TRUE AND a.answer_text IS NOT NULL
        """, (username,))
        return [dict(row) for row in self.cursor.fetchall()]

    def duplicate_survey(self, original_survey_id):
        self.connect()
        original_survey = self.get_survey_by_id(original_survey_id)
        if not original_survey:
            return None

        new_created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.cursor.execute(
            "INSERT INTO surveys (title, description, created_at, end_date) VALUES (?, ?, ?, ?)",
            (f"{original_survey['title']} (複製)", original_survey['description'], new_created_at, original_survey['end_date'])
        )
        new_survey_id = self.cursor.lastrowid

        original_questions = self.get_survey_questions(original_survey_id)
        for q in original_questions:
            self.cursor.execute(
                """
                INSERT INTO questions (survey_id, question_text, question_type, options, order_number, page_number, image_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (new_survey_id, q['question_text'], q['question_type'], q['options'], q['order_number'], q['page_number'], q['image_data'])
            )
        self.conn.commit()
        return new_survey_id
    
    # end_dateが設定されており、現在日時よりも未来日時であるアンケートの内、ユーザーが回答していないアンケートを取得する関数
    def get_unanswered_surveys(self, username):
        self.connect()
        self.cursor.execute("""
            SELECT s.survey_id, s.title, s.description, s.end_date
            FROM surveys s
            LEFT JOIN (
                SELECT DISTINCT survey_id
                FROM answers
                WHERE username = ? AND is_draft = FALSE
            ) AS answered_answers ON s.survey_id = answered_answers.survey_id
            WHERE answered_answers.survey_id IS NULL
                AND s.end_date > ?
        """, (username, datetime.now()))
        unanswered_surveys = self.cursor.fetchall()
        return unanswered_surveys
    
    # 公開されているアンケートの内、下書き保存されているアンケートを取得する関数
    def get_draft_surveys(self, username):
        self.connect()
        self.cursor.execute("""
            SELECT s.survey_id, s.title, s.description, s.end_date
            FROM surveys s
            LEFT JOIN (
                SELECT DISTINCT survey_id
                FROM answers
                WHERE username = ? AND is_draft = TRUE
            ) AS draft_answers ON s.survey_id = draft_answers.survey_id
            WHERE draft_answers.survey_id IS NOT NULL
        """, (username,))
        draft_surveys = self.cursor.fetchall()
        return draft_surveys
    
    # 公開されているアンケートの内、回答済みのアンケートを取得する関数
    def get_answered_surveys(self, username):
        self.connect()
        self.cursor.execute("""
            SELECT s.survey_id, s.title, s.description, s.end_date
            FROM surveys s
            JOIN (
                SELECT DISTINCT survey_id
                FROM answers
                WHERE username = ? AND is_draft = FALSE
            ) AS answered ON s.survey_id = answered.survey_id
        """, (username,))
        answered_surveys = self.cursor.fetchall()
        return answered_surveys
    
    # 公開期限が過ぎた回答済みアンケートを取得する関数
    def get_expired_answered_surveys(self, username):
        self.connect()
        today = datetime.now().strftime('%Y-%m-%d')
        self.cursor.execute("""
            SELECT s.survey_id, s.title, s.description, s.end_date
            FROM surveys s
            JOIN (
                SELECT DISTINCT survey_id
                FROM answers
                WHERE username = ? AND is_draft = FALSE AND end_date < ?
            ) AS expired_answers ON s.survey_id = expired_answers.survey_id
        """, (username, today))
        expired_answered_surveys = self.cursor.fetchall()
        return expired_answered_surveys