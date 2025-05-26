
# アンケート回答アプリケーションの仕様

## アプリケーションの目的

ユーザーがアンケートに回答できる。
管理者がアンケートを作成、編集、削除できる。
回答状況を管理・確認できる。

## 主要な技術スタック

フロントエンド / UI: Streamlit
認証: streamlit_authenticator
データ永続化: SQLite3
構成ファイル: YAML

## ユーザーとロール

* 一般ユーザー
  * アンケートの閲覧、回答（一時保存、提出）。
  * 自分の回答状況（未回答、一時保存中、回答済み）の確認。
* 管理者ユーザー
  *  一般ユーザーの全機能。
  * アンケートの作成、編集、削除、複製。
  * 質問の追加、編集、削除。
  * 回答結果の確認。
* 認証はconfig.yamlで管理される。
  * 将来的にkeycloakなどでOIDCにする

## データベーススキーマ (survey_app.db)

ユーザー情報は streamlit_authenticator で管理されるため、データベースにはユーザーテーブルは不要。

```mermaid
erDiagram
  surveys {
      INTEGER survey_id PK "アンケートID"
      TEXT title "アンケートタイトル"
      TEXT description "アンケート説明"
      TEXT created_at "作成日時"
      TEXT end_date "回答期限"
  }
  questions {
      INTEGER question_id PK "質問ID"
      INTEGER survey_id FK "アンケートID"
      TEXT question_text "質問内容"
      TEXT question_type "質問形式"
      TEXT options "選択肢(JSON)"
      INTEGER order_number "ページ内の表示順序"
      INTEGER page_number "ページ番号"
      BLOB image "設問画像"
  }
  answers {
      INTEGER answer_id PK "回答ID"
      TEXT username "ユーザー名"
      INTEGER question_id FK "質問ID"
      TEXT answer_text "回答内容"
      TEXT submitted_at "回答日時"
      BOOLEAN is_draft "一時保存フラグ"
  }

  surveys ||--o{ questions : "1:N"
  questions ||--o{ answers : "1:1"
```

##  アプリケーションの画面フローと機能

5.1 ログイン画面
streamlit_authenticator を使用してログイン。
ログイン成功後、st.session_state.user_info にユーザー情報 (AppUser オブジェクト) を保存。
ログイン失敗時はエラーメッセージを表示。

5.2 メインナビゲーション (サイドバー)
streamlit_option_menu を使用。
ログイン中のユーザー名を表示し、ログアウトボタンを提供。
メニュー項目:
「ホーム」（全ユーザー向けダッシュボード）
「回答ページ」（全ユーザー向けアンケート回答）
「管理者ページ」（管理者ユーザーのみ表示）

5.3 ホームページ (home_page.py - 旧 dashboard_page.py)
ユーザーが自身のアンケート状況を一覧できるダッシュボード。
表示内容:
回答可能なアンケート: 未回答かつ回答期限内のアンケートリスト。
一時保存中のアンケート: 回答を途中で保存しているアンケートリスト。
回答済みのアンケート: すでに回答を提出済みのアンケートリスト。
各アンケートのエントリから、対応する回答ページへの遷移ボタンを提供。

5.4 回答ページ (answer_page.py)
ユーザーが選択したアンケートの質問を表示し、回答を入力・選択できる。
回答の一時保存 (is_draft = TRUE) と提出 (is_draft = FALSE) が可能。
回答済み/一時保存済みのアンケートは、その内容を読み込んで表示できる。

5.5 管理者ページ (pages/admin/ 以下)
管理者ユーザーのみアクセス可能。
サブメニュー（水平ナビゲーション）:
「アンケート一覧」（manage_surveys.py）
「新規アンケート作成」（create_survey.py）
アンケート一覧:
既存のアンケートリストを表示。
各アンケートに対し、編集、削除、複製ボタンを提供。
編集ボタンクリックで、そのアンケートの質問管理画面に遷移。
新規アンケート作成:
アンケートのタイトル、説明、回答期限などを入力して新しいアンケートを作成。
質問管理画面 (アンケート編集時):
選択されたアンケートの質問リストを表示。
質問の追加、編集、削除機能。
質問タイプに応じた入力（テキスト、選択肢など）。
質問の順序、ページ番号、画像URLの設定。

## セッション状態の管理 (st.session_state)

user_info: ログイン中のユーザー情報 (AppUser オブジェクト)。
selected_survey_id: 回答ページで現在選択されているアンケートのID。
current_page: 現在表示中のメインページの識別子（「ホーム」「回答ページ」「管理者ページ」など）。
admin_selected_survey_id: 管理者ページで現在選択されているアンケートのID（編集対象）。
admin_edit_question_id: 管理者ページで現在編集中の質問ID。
admin_sub_page: 管理者ページ内で現在表示中のサブページの識別子（「アンケート一覧」「新規アンケート作成」など）。
