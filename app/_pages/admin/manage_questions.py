import streamlit as st
import json
from datetime import datetime
import base64

def manage_questions_for_survey_and_info(db, survey_id):
    st.subheader("アンケート編集と質問管理")

    survey = db.get_survey_by_id(survey_id)
    if not survey:
        st.error("アンケートが見つかりません。")
        st.session_state.admin_selected_survey_id = None
        st.session_state.admin_sub_page = "アンケート一覧"
        st.rerun() # 見つからない場合は一覧に戻す
        return

    st.markdown(f"#### 対象アンケート: {survey['title']} (ID: {survey['survey_id']})")
    
    # --- アンケート基本情報の編集フォーム ---
    st.markdown("---")
    st.subheader("アンケート基本情報の編集")
    with st.form("edit_survey_info_form", clear_on_submit=False):
        edited_title = st.text_input("アンケートタイトル", value=survey['title'], key="edit_survey_title")
        edited_description = st.text_area("アンケート説明", value=survey['description'] if survey['description'] else "", key="edit_survey_description")
        
        # end_date の datetimeオブジェクトへの変換と表示
        current_end_date = datetime.strptime(survey['end_date'], '%Y-%m-%d').date() if survey['end_date'] else None
        edited_end_date = st.date_input(
            "回答期限 (任意)",
            value=current_end_date,
            min_value=datetime.now().date(),
            key="edit_survey_end_date"
        )
        
        update_info_button = st.form_submit_button("アンケート基本情報を更新")

        if update_info_button:
            if not edited_title:
                st.error("アンケートタイトルは必須です。")
            else:
                db.update_survey(
                    survey_id,
                    edited_title,
                    edited_description,
                    edited_end_date.strftime('%Y-%m-%d') if edited_end_date else None
                )
                st.success("アンケート基本情報が更新されました！")
                st.rerun() # 更新を反映して再描画

    # --- 質問の追加/編集セクション ---
    st.markdown("---")
    st.subheader("質問の追加/編集")

    # 既存の質問を取得
    questions = db.get_survey_questions(survey_id)

    # 編集中の質問がある場合、その情報をフォームにプリセット
    edit_question_id = st.session_state.get('admin_edit_question_id')
    editing_question = next((q for q in questions if q['question_id'] == edit_question_id), None)

    # 質問追加/編集フォーム
    with st.form("question_form", clear_on_submit=True):
        st.markdown("##### 質問詳細")
        question_text_val = editing_question['question_text'] if editing_question else ""
        question_text = st.text_area("質問文", value=question_text_val, key="q_text")
        
        question_type_options = ['選択肢', '自由記述']
        question_type_idx = question_type_options.index(editing_question['question_type']) if editing_question and editing_question['question_type'] in question_type_options else 0
        question_type = st.selectbox(
            "質問形式",
            question_type_options,
            index=question_type_idx,
            key="q_type"
        )

        options_text_val = ""
        if editing_question and editing_question['options']:
            options_text_val = "\n".join(editing_question['options'])

        options = []
        if question_type in ['選択肢']:
            options_text = st.text_area(
                "選択肢 (改行区切りで入力)",
                value=options_text_val,
                key="q_options"
            )
            options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
            # 選択肢がない場合のエラーメッセージはフォームサブミット時に表示


        col_order, col_number= st.columns([1,1])
        with col_order:
            # 質問追加の場合、現在の最大順序+1、最大ページ番号を使用
            max_order = db.get_max_order_number(survey_id, st.session_state.get(f'current_question_page_{survey_id}', 1))
            order_number_val = editing_question['order_number'] if editing_question else max_order + 1
            order_number = st.number_input(
                "表示順序",
                min_value=1,
                value=order_number_val,
                key="q_order"
            )

        with col_number:
            max_page = db.get_max_page_number(survey_id)
            page_number_val = editing_question['page_number'] if editing_question else (max_page if max_page > 0 else 1)
            page_number = st.number_input(
                "ページ番号",
                min_value=1,
                value=page_number_val,
                key="q_page"
            )

        # --- 画像アップロード欄 ---
        image_bytes = None
        if editing_question and editing_question.get('image_data'):
            # 既存画像がある場合は表示
            st.image(editing_question['image_data'], caption="現在の画像", width=200)
        uploaded_file = st.file_uploader("画像ファイル（任意）", type=["png", "jpg", "jpeg"], key="q_image_upload")
        if uploaded_file is not None:
            image_bytes = uploaded_file.read()
            st.image(image_bytes, caption="アップロード画像", width=200)
        elif editing_question and editing_question.get('image_data'):
            image_bytes = editing_question['image_data']


        col_submit, col_cancel = st.columns([1,1])
        with col_submit:
            submit_label = "質問を更新" if editing_question else "質問を追加"
            submit_button = st.form_submit_button(submit_label)
        with col_cancel:
            if editing_question:
                cancel_button = st.form_submit_button("キャンセル")
                if cancel_button:
                    st.session_state.admin_edit_question_id = None
                    st.rerun()

        if submit_button:
            if not question_text:
                st.error("質問文は必須です。")
            elif question_type in ['選択肢'] and not options:
                st.error("選択肢形式の質問には選択肢が必要です。")
            else:
                if editing_question:
                    db.update_question(
                        editing_question['question_id'],
                        question_text,
                        question_type,
                        options,
                        order_number,
                        page_number,
                        image_bytes  # 画像データを渡す
                    )
                    st.success("質問が更新されました！")
                    st.session_state.admin_edit_question_id = None
                else:
                    db.add_question(
                        survey_id,
                        question_text,
                        question_type,
                        options,
                        order_number,
                        page_number,
                        image_bytes  # 画像データを渡す
                    )
                    st.success("質問が追加されました！")
                st.rerun()

    # --- 既存の質問リストセクション ---
    st.markdown("---")
    st.subheader("既存の質問")

    # 再度質問リストを取得（追加・更新を反映するため）
    questions = db.get_survey_questions(survey_id)

    if questions:
        # ページナビゲーション
        unique_pages = sorted(list(set(q['page_number'] for q in questions)))
        # 現在表示しているページをセッションに保持
        if f'current_question_page_{survey_id}' not in st.session_state:
            st.session_state[f'current_question_page_{survey_id}'] = 1
        
        current_question_page = st.session_state[f'current_question_page_{survey_id}']
        
        # ページ番号がユニークなページリストに含まれていない場合（例：ページ削除後に存在しないページ番号になった場合）
        if current_question_page not in unique_pages and unique_pages:
            st.session_state[f'current_question_page_{survey_id}'] = unique_pages[0]
            current_question_page = unique_pages[0] # 最初のページにリセット
            st.rerun() # リセットしたら再描画

        if len(unique_pages) > 1:
            st.write(f"現在のページ: {current_question_page} / {max(unique_pages)}")
            col_q_prev, col_q_next = st.columns(2)
            with col_q_prev:
                if current_question_page > min(unique_pages):
                    if st.button("前のページ", key=f"q_prev_page_{survey_id}"):
                        st.session_state[f'current_question_page_{survey_id}'] = current_question_page - 1
                        st.rerun()
            with col_q_next:
                if current_question_page < max(unique_pages):
                    if st.button("次のページ", key=f"q_next_page_{survey_id}"):
                        st.session_state[f'current_question_page_{survey_id}'] = current_question_page + 1
                        st.rerun()

        questions_on_current_page = [q for q in questions if q['page_number'] == current_question_page]
        questions_on_current_page.sort(key=lambda x: x['order_number'])

        if not questions_on_current_page:
            st.info("このページには質問がありません。")
            # 質問がないページの場合でも、前のページに戻るボタンを提供
            if len(unique_pages) > 1 and current_question_page > min(unique_pages):
                 if st.button("前のページに戻る", key=f"back_to_prev_page_{survey_id}"):
                    st.session_state[f'current_question_page_{survey_id}'] = current_question_page - 1
                    st.rerun()
            return

        for question in questions_on_current_page:
            st.markdown(f"**Q{question['order_number']}. (ページ {question['page_number']}) {question['question_text']}**")
            st.write(f"形式: {question['question_type']}")
            if question['options']:
                st.write(f"選択肢: {', '.join(question['options'])}")
            if question['image_url']:
                st.image(question['image_url'], caption="質問画像", width=200)

            col_edit, col_delete = st.columns([1,1])
            with col_edit:
                if st.button("編集", key=f"edit_question_list_{question['question_id']}"): # Keyを修正
                    st.session_state.admin_edit_question_id = question['question_id']
                    st.rerun()
            with col_delete:
                if st.button("削除", key=f"delete_question_list_{question['question_id']}"): # Keyを修正
                    db.delete_question(question['question_id'])
                    st.success("質問が削除されました。")
                    st.session_state.admin_edit_question_id = None # 削除した質問の編集状態をクリア
                    st.rerun()
            st.markdown("---")
    else:
        st.info("このアンケートにはまだ質問がありません。")

    # アンケート一覧に戻るボタン
    if st.button("アンケート一覧に戻る", key="back_to_survey_list_from_questions_end"):
        st.session_state.admin_selected_survey_id = None
        st.session_state.admin_edit_question_id = None
        st.session_state.admin_sub_page = "アンケート一覧"
        st.rerun()