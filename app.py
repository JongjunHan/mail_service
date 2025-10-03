#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
네이버 메일 통합 웹 서비스
Flask 기반 Web UI 서비스 (회신 기능 및 첨부파일 다운로드 포함)
"""

from flask import Flask, render_template, request, jsonify, session, send_file
from lib import NaverMailSuite
import secrets
import webbrowser
import threading
import time

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Timeout 설정 (무제한)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24시간

# 세션별 suite 인스턴스 저장
suite_instances = {}


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/api/connect', methods=['POST'])
def connect():
    """네이버 메일 서버 연결"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        openai_key = data.get('openai_key')

        if not username or not password:
            return jsonify({'success': False, 'error': '아이디와 비밀번호를 입력해주세요'})

        # 세션 ID 생성
        session_id = secrets.token_hex(16)

        # Suite 인스턴스 생성
        suite = NaverMailSuite(
            naver_username=username,
            naver_password=password,
            openai_api_key=openai_key
        )

        status = suite.get_status()

        if not status['parser_connected']:
            return jsonify({'success': False, 'error': '메일 서버 연결 실패'})

        # 세션에 저장
        suite_instances[session_id] = suite
        session['session_id'] = session_id

        return jsonify({'success': True, 'status': status})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/select_mailbox', methods=['POST'])
def select_mailbox():
    """메일박스 선택"""
    try:
        session_id = session.get('session_id')
        if not session_id or session_id not in suite_instances:
            return jsonify({'success': False, 'error': '먼저 로그인해주세요'})

        suite = suite_instances[session_id]
        data = request.json
        mailbox = data.get('mailbox', 'INBOX')

        # 메일박스 선택
        suite.select_mailbox(mailbox)

        return jsonify({'success': True, 'mailbox': mailbox})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/fetch_emails', methods=['POST'])
def fetch_emails():
    """이메일 목록 가져오기"""
    try:
        session_id = session.get('session_id')
        if not session_id or session_id not in suite_instances:
            return jsonify({'success': False, 'error': '먼저 로그인해주세요'})

        suite = suite_instances[session_id]
        data = request.json

        mailbox = data.get('mailbox', 'INBOX')
        criteria = data.get('criteria', 'ALL')
        limit = int(data.get('limit', 10))

        # 메일박스 선택
        suite.select_mailbox(mailbox)

        # 이메일 가져오기
        emails = suite.fetch_emails(
            limit=limit,
            criteria=criteria,
            download_full=True,
            extract_attachment_text=True
        )

        # 응답용 데이터 가공
        email_list = []
        for email in emails:
            email_list.append({
                'id': email.get('id', ''),
                'subject': email.get('subject', '제목 없음'),
                'sender': email.get('sender', ''),
                'date': email.get('date', ''),
                'body_preview': email.get('body', '')[:200] + '...' if len(email.get('body', '')) > 200 else email.get('body', ''),
                'has_attachments': email.get('attachment_count', 0) > 0,
                'attachment_count': email.get('attachment_count', 0)
            })

        return jsonify({'success': True, 'emails': email_list, 'count': len(email_list)})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/get_email_detail', methods=['POST'])
def get_email_detail():
    """이메일 상세 내용 가져오기"""
    try:
        session_id = session.get('session_id')
        if not session_id or session_id not in suite_instances:
            return jsonify({'success': False, 'error': '먼저 로그인해주세요'})

        suite = suite_instances[session_id]
        data = request.json
        email_id = data.get('email_id')

        if not email_id:
            return jsonify({'success': False, 'error': '이메일 ID가 필요합니다'})

        # 본문과 첨부파일 분리하여 가져오기
        separated = suite.get_email_body_and_attachments_separately(email_id)

        if 'error' in separated:
            return jsonify({'success': False, 'error': separated['error']})

        return jsonify({'success': True, 'email': separated})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/summarize_email', methods=['POST'])
def summarize_email():
    """이메일 요약"""
    try:
        session_id = session.get('session_id')
        if not session_id or session_id not in suite_instances:
            return jsonify({'success': False, 'error': '먼저 로그인해주세요'})

        suite = suite_instances[session_id]

        if not suite.get_status()['summarizer_ready']:
            return jsonify({'success': False, 'error': 'OpenAI API 키가 설정되지 않았습니다'})

        data = request.json
        email_id = data.get('email_id')
        summary_type = data.get('summary_type', 'detailed')
        summarize_body = data.get('summarize_body', True)
        summarize_attachments = data.get('summarize_attachments', False)
        model = data.get('model', 'gpt-4o-mini')

        if not email_id:
            return jsonify({'success': False, 'error': '이메일 ID가 필요합니다'})

        # 선택한 모델로 text_summarizer 업데이트
        if hasattr(suite, 'text_summarizer') and suite.text_summarizer:
            suite.text_summarizer.model = model

        # 고급 요약 실행
        result = suite.summarize_email_advanced(
            email_id=email_id,
            summary_type=summary_type,
            summarize_body=summarize_body,
            summarize_attachments=summarize_attachments
        )

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']})

        return jsonify({'success': True, 'summary': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/reply_email', methods=['POST'])
def reply_email():
    """이메일 회신"""
    try:
        session_id = session.get('session_id')
        if not session_id or session_id not in suite_instances:
            return jsonify({'success': False, 'error': '먼저 로그인해주세요'})

        suite = suite_instances[session_id]

        if not suite.get_status()['smtp_ready']:
            return jsonify({'success': False, 'error': 'SMTP 서버가 준비되지 않았습니다'})

        data = request.json
        to_email = data.get('to_email')
        subject = data.get('subject')
        body = data.get('body')

        if not to_email or not subject or not body:
            return jsonify({'success': False, 'error': '받는사람, 제목, 본문은 필수입니다'})

        # 이메일 전송
        result = suite.send_email(
            to_emails=to_email,
            subject=subject,
            body=body
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/download_attachment', methods=['POST'])
def download_attachment():
    """첨부파일 다운로드"""
    try:
        session_id = session.get('session_id')
        if not session_id or session_id not in suite_instances:
            return jsonify({'success': False, 'error': '먼저 로그인해주세요'})

        suite = suite_instances[session_id]
        data = request.json
        email_id = data.get('email_id')
        filename = data.get('filename')

        if not email_id or not filename:
            return jsonify({'success': False, 'error': '이메일 ID와 파일명이 필요합니다'})

        # 첨부파일 경로 가져오기
        attachment_path = suite.get_attachment_path(email_id, filename)

        if not attachment_path:
            return jsonify({'success': False, 'error': '첨부파일을 찾을 수 없습니다'})

        return send_file(attachment_path, as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/summarize_attachment', methods=['POST'])
def summarize_attachment():
    """다운로드된 첨부파일 요약"""
    try:
        session_id = session.get('session_id')
        if not session_id or session_id not in suite_instances:
            return jsonify({'success': False, 'error': '먼저 로그인해주세요'})

        suite = suite_instances[session_id]

        if not suite.get_status()['summarizer_ready']:
            return jsonify({'success': False, 'error': 'OpenAI API 키가 설정되지 않았습니다'})

        data = request.json
        email_id = data.get('email_id')
        filename = data.get('filename')
        summary_type = data.get('summary_type', 'detailed')
        model = data.get('model', 'gpt-4o-mini')

        if not email_id or not filename:
            return jsonify({'success': False, 'error': '이메일 ID와 파일명이 필요합니다'})

        # 첨부파일 경로 가져오기
        attachment_path = suite.get_attachment_path(email_id, filename)

        if not attachment_path:
            return jsonify({'success': False, 'error': '첨부파일을 찾을 수 없습니다'})

        # 선택한 모델로 text_summarizer 업데이트
        if hasattr(suite, 'text_summarizer') and suite.text_summarizer:
            suite.text_summarizer.model = model

        # 첨부파일 요약
        result = suite.summarize_downloaded_attachment(attachment_path, summary_type)

        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']})

        return jsonify({'success': True, 'summary': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/logout', methods=['POST'])
def logout():
    """로그아웃"""
    try:
        session_id = session.get('session_id')
        if session_id and session_id in suite_instances:
            suite = suite_instances[session_id]
            suite.mail_parser.close()
            del suite_instances[session_id]

        session.clear()
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


def open_browser():
    """서버 시작 후 브라우저 자동 열기"""
    time.sleep(1.5)  # 서버가 완전히 시작될 때까지 대기
    webbrowser.open('http://localhost:5000')


if __name__ == '__main__':
    print("=" * 60)
    print("네이버 메일 통합 웹 서비스")
    print("=" * 60)
    print("\n서비스 시작 중...")
    print("\n브라우저가 자동으로 열립니다...")
    print("  URL: http://localhost:5000")
    print("\n종료하려면 Ctrl+C를 누르세요.")
    print("=" * 60 + "\n")

    # 브라우저 자동 열기 (별도 스레드)
    threading.Thread(target=open_browser, daemon=True).start()

    # Flask 서버 시작 (timeout 설정)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
