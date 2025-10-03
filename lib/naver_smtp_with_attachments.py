#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.application import MIMEApplication
from email import encoders
from email.header import Header
import os
import mimetypes
from pathlib import Path
from typing import List, Optional

class NaverSMTPSender:
    def __init__(self, username: str, password: str):
        """
        네이버 SMTP 메일 발송기
        
        Args:
            username: 네이버 아이디 (예: user@naver.com)
            password: 네이버 앱 비밀번호
        """
        self.username = username
        self.password = password
        self.smtp_server = "smtp.naver.com"
        self.smtp_port = 587
        self.smtp_ssl_port = 465
    
    def _detect_mime_type(self, file_path: str):
        """파일의 MIME 타입 자동 감지"""
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            return 'application', 'octet-stream'
        
        main_type, sub_type = mime_type.split('/', 1)
        return main_type, sub_type
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """첨부파일을 메시지에 추가"""
        if not os.path.isfile(file_path):
            print(f"⚠️ 첨부파일을 찾을 수 없습니다: {file_path}")
            return False
        
        try:
            file_name = Path(file_path).name
            main_type, sub_type = self._detect_mime_type(file_path)
            
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # MIME 타입별 처리
            if main_type == 'text':
                # 텍스트 파일
                attachment = MIMEText(file_data.decode('utf-8'), sub_type)
                
            elif main_type == 'image':
                # 이미지 파일
                attachment = MIMEImage(file_data, _subtype=sub_type)
                
            elif main_type == 'audio':
                # 오디오 파일
                attachment = MIMEAudio(file_data, _subtype=sub_type)
                
            elif main_type == 'application':
                # 애플리케이션 파일 (PDF, DOC, ZIP 등)
                attachment = MIMEApplication(file_data, _subtype=sub_type)
                
            else:
                # 기타 파일
                attachment = MIMEBase(main_type, sub_type)
                attachment.set_payload(file_data)
                encoders.encode_base64(attachment)
            
            # Content-Disposition 헤더 추가
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="{file_name}"'
            )
            
            msg.attach(attachment)
            print(f"✅ 첨부파일 추가됨: {file_name} ({main_type}/{sub_type})")
            return True
            
        except Exception as e:
            print(f"❌ 첨부파일 추가 실패 ({file_path}): {e}")
            return False
    
    def send_email(self, 
                   to_emails: List[str],
                   subject: str,
                   body: str,
                   cc_emails: Optional[List[str]] = None,
                   bcc_emails: Optional[List[str]] = None,
                   attachments: Optional[List[str]] = None,
                   is_html: bool = False,
                   use_ssl: bool = False) -> dict:
        """
        이메일 전송
        
        Args:
            to_emails: 받는 사람 이메일 리스트
            subject: 제목
            body: 본문
            cc_emails: 참조 이메일 리스트
            bcc_emails: 숨은참조 이메일 리스트
            attachments: 첨부파일 경로 리스트
            is_html: HTML 형식 여부
            use_ssl: SSL 사용 여부 (기본: TLS)
        
        Returns:
            dict: 전송 결과
        """
        try:
            # 메시지 객체 생성
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = Header(subject, 'utf-8')
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # 본문 추가
            if is_html:
                msg.attach(MIMEText(body, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 첨부파일 추가
            attached_files = []
            if attachments:
                for file_path in attachments:
                    if self._add_attachment(msg, file_path):
                        attached_files.append(Path(file_path).name)
            
            # 전체 수신자 리스트
            all_recipients = to_emails.copy()
            if cc_emails:
                all_recipients.extend(cc_emails)
            if bcc_emails:
                all_recipients.extend(bcc_emails)
            
            # SMTP 서버 연결 및 전송
            if use_ssl:
                # SSL 연결
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_ssl_port, context=context) as server:
                    server.login(self.username, self.password)
                    server.send_message(msg, to_addrs=all_recipients)
            else:
                # TLS 연결 (권장)
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.username, self.password)
                    server.send_message(msg, to_addrs=all_recipients)
            
            return {
                'success': True,
                'message': '이메일 전송 성공',
                'recipients': len(all_recipients),
                'to': to_emails,
                'cc': cc_emails or [],
                'bcc': bcc_emails or [],
                'attachments': attached_files,
                'attachment_count': len(attached_files)
            }
            
        except smtplib.SMTPAuthenticationError:
            return {
                'success': False,
                'error': 'SMTP 인증 실패: 아이디 또는 앱 비밀번호를 확인하세요.'
            }
        except smtplib.SMTPRecipientsRefused as e:
            return {
                'success': False,
                'error': f'수신자 거부: {e}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'이메일 전송 실패: {str(e)}'
            }
    
    def test_connection(self) -> dict:
        """SMTP 연결 테스트"""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                return {
                    'success': True,
                    'message': '네이버 SMTP 서버 연결 성공'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'연결 실패: {str(e)}'
            }

def create_sample_files():
    """테스트용 샘플 파일들 생성"""
    # 텍스트 파일
    with open('sample.txt', 'w', encoding='utf-8') as f:
        f.write('안녕하세요!\n이것은 테스트용 텍스트 파일입니다.\n첨부파일 테스트 중입니다.')
    
    # HTML 파일
    with open('sample.html', 'w', encoding='utf-8') as f:
        f.write('''
        <!DOCTYPE html>
        <html>
        <head><title>테스트 HTML</title></head>
        <body>
            <h1>HTML 첨부파일 테스트</h1>
            <p>이것은 <strong>HTML 첨부파일</strong> 테스트입니다.</p>
        </body>
        </html>
        ''')
    
    # CSV 파일
    with open('sample.csv', 'w', encoding='utf-8') as f:
        f.write('이름,이메일,회사\n')
        f.write('홍길동,hong@example.com,ABC회사\n')
        f.write('김철수,kim@example.com,XYZ회사\n')
    
    print("📁 샘플 파일들이 생성되었습니다: sample.txt, sample.html, sample.csv")

# 사용 예시
if __name__ == "__main__":
    # 설정 (실제 값으로 변경하세요)
    NAVER_ID = "your_id@naver.com"
    NAVER_APP_PASSWORD = "your_app_password"
    RECIPIENT_EMAIL = "recipient@example.com"
    
    # 메일 발송기 초기화
    sender = NaverSMTPSender(NAVER_ID, NAVER_APP_PASSWORD)
    
    # 연결 테스트
    print("=== SMTP 연결 테스트 ===")
    test_result = sender.test_connection()
    if test_result['success']:
        print(f"✅ {test_result['message']}")
    else:
        print(f"❌ {test_result['error']}")
        exit(1)
    
    # 샘플 파일 생성
    print("\n=== 샘플 파일 생성 ===")
    create_sample_files()
    
    # 예시 1: 단일 첨부파일 전송
    print("\n=== 단일 첨부파일 전송 ===")
    result1 = sender.send_email(
        to_emails=[RECIPIENT_EMAIL],
        subject="단일 첨부파일 테스트",
        body="텍스트 파일이 첨부되었습니다.",
        attachments=["sample.txt"]
    )
    
    if result1['success']:
        print(f"✅ {result1['message']}")
        print(f"📎 첨부파일: {result1['attachments']}")
    else:
        print(f"❌ {result1['error']}")
    
    # 예시 2: 다중 첨부파일 전송
    print("\n=== 다중 첨부파일 전송 ===")
    result2 = sender.send_email(
        to_emails=[RECIPIENT_EMAIL],
        subject="다중 첨부파일 테스트",
        body="""
        안녕하세요!
        
        다음 파일들이 첨부되었습니다:
        1. 텍스트 파일 (sample.txt)
        2. HTML 파일 (sample.html)  
        3. CSV 파일 (sample.csv)
        
        감사합니다.
        """,
        attachments=["sample.txt", "sample.html", "sample.csv"]
    )
    
    if result2['success']:
        print(f"✅ {result2['message']}")
        print(f"📎 첨부파일 {result2['attachment_count']}개: {result2['attachments']}")
    else:
        print(f"❌ {result2['error']}")
    
    # 예시 3: HTML 이메일 + 첨부파일
    print("\n=== HTML 이메일 + 첨부파일 ===")
    html_body = """
    <html>
    <body>
        <h2>🎉 HTML 이메일 + 첨부파일 테스트</h2>
        
        <p>안녕하세요! <strong>HTML 형식</strong>의 이메일에 첨부파일을 포함하여 전송합니다.</p>
        
        <h3>📎 첨부파일 목록:</h3>
        <ul>
            <li><code>sample.txt</code> - 텍스트 파일</li>
            <li><code>sample.csv</code> - 데이터 파일</li>
        </ul>
        
        <p style="color: blue;">파일을 다운로드하여 확인해보세요!</p>
        
        <hr>
        <small>이 메일은 네이버 SMTP를 통해 전송되었습니다.</small>
    </body>
    </html>
    """
    
    result3 = sender.send_email(
        to_emails=[RECIPIENT_EMAIL],
        subject="📧 HTML + 첨부파일 테스트",
        body=html_body,
        attachments=["sample.txt", "sample.csv"],
        is_html=True
    )
    
    if result3['success']:
        print(f"✅ {result3['message']}")
        print(f"📎 첨부파일: {result3['attachments']}")
    else:
        print(f"❌ {result3['error']}")
    
    # 예시 4: 참조/숨은참조 + 첨부파일
    print("\n=== 참조/숨은참조 + 첨부파일 ===")
    result4 = sender.send_email(
        to_emails=[RECIPIENT_EMAIL],
        cc_emails=["cc@example.com"],  # 실제 이메일로 변경
        bcc_emails=["bcc@example.com"],  # 실제 이메일로 변경
        subject="참조/숨은참조 + 첨부파일 테스트",
        body="참조와 숨은참조가 포함된 이메일에 첨부파일을 포함했습니다.",
        attachments=["sample.html"]
    )
    
    if result4['success']:
        print(f"✅ {result4['message']}")
        print(f"📧 전송 대상: TO({len(result4['to'])}), CC({len(result4['cc'])}), BCC({len(result4['bcc'])})")
        print(f"📎 첨부파일: {result4['attachments']}")
    else:
        print(f"❌ {result4['error']}")
    
    print("\n🎉 모든 테스트가 완료되었습니다!")
    print("💡 실제 사용 시에는 NAVER_ID, NAVER_APP_PASSWORD, RECIPIENT_EMAIL을 실제 값으로 변경하세요.")