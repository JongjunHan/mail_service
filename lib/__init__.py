"""
네이버 메일 통합 모듈 (Naver Mail Suite)

이 패키지는 네이버 메일 파싱, LLM 요약, SMTP 발송 기능을 통합한 올인원 솔루션입니다.

주요 모듈:
- naver_mail_parser: 네이버 메일 파싱 (첨부파일 자동 다운로드 및 텍스트 추출 지원)
- text_summarizer: LLM 기반 텍스트 요약 (OpenAI 1.0.0+ 지원, 본문/첨부파일 분리 요약, 다운로드된 첨부파일 직접 요약)
- naver_smtp_with_attachments: 네이버 SMTP 메일 발송
- naver_mail_suite: 통합 메일 처리 시스템

주요 기능:
1. 메일 파싱 및 첨부파일 자동 다운로드 (로컬 저장)
2. 첨부파일 텍스트 추출 (PDF, Word, Excel, PPT, 텍스트 등)
3. OpenAI 1.0.0+ API를 사용한 본문과 첨부파일 선택적 요약
4. 다운로드된 첨부파일 직접 파싱 및 요약
5. 첨부파일 다운로드 기능 (웹 UI 지원)
6. 메일 자동 전송

사용 예시:
    from lib import NaverMailSuite, quick_summary

    # 1. 통합 클래스 사용
    suite = NaverMailSuite(
        naver_username="user@naver.com",
        naver_password="app_password",
        openai_api_key="your_api_key"
    )

    # 2. 메일 가져오기 → 요약 → 전송 (원스탑)
    result = suite.fetch_summarize_send(
        to_emails=["recipient@example.com"],
        summary_type="korean",
        limit=5
    )

    # 3. 첨부파일 자동 다운로드 및 텍스트 추출하여 메일 가져오기
    emails = suite.fetch_emails(
        limit=5,
        download_full=True,
        extract_attachment_text=True
    )

    # 4. 본문 + 첨부파일 선택적 요약 (고급)
    result = suite.summarize_email_advanced(
        email_id="123",
        summary_type="detailed",
        summarize_body=True,           # 본문 요약
        summarize_attachments=True     # 첨부파일 요약
    )

    # 결과 확인
    print(result['body_summary'])          # 본문 요약
    print(result['attachment_summaries'])  # 첨부파일별 요약
    print(result['combined_summary'])      # 통합 요약

    # 5. 본문과 첨부파일 분리
    separated = suite.get_email_body_and_attachments_separately(email_id="123")
    print(separated['body_text'])      # 순수 본문
    print(separated['attachments'])    # 첨부파일 목록 및 텍스트

    # 6. 다운로드된 첨부파일 직접 요약 (신규)
    attachment_result = suite.summarize_downloaded_attachment(
        attachment_path="downloads/email_123/document.pdf",
        summary_type="detailed"
    )
    print(attachment_result['summary'])

    # 7. 이메일 폴더의 모든 첨부파일 일괄 요약 (신규)
    folder_result = suite.summarize_email_attachments_from_path(
        email_folder_path="downloads/email_123",
        summary_type="korean"
    )
    print(folder_result['attachment_summaries'])

    # 8. 첨부파일 경로 가져오기 (다운로드용)
    path = suite.get_attachment_path(email_id="123", filename="document.pdf")

    # 9. 빠른 요약 함수 사용
    quick_result = quick_summary(
        naver_username="user@naver.com",
        naver_password="app_password",
        openai_api_key="your_api_key",
        to_email="recipient@example.com",
        limit=3
    )

Author: Claude Code Assistant
Version: 2.2.0
"""

# 주요 클래스들을 패키지 레벨에서 import
from .naver_mail_suite import (
    NaverMailSuite,
    MailProcessor, 
    BatchProcessor,
    quick_summary,
    create_daily_digest
)

# 개별 모듈들도 import 가능하도록
from .naver_mail_parser import NaverMailParser
from .text_summarizer import TextSummarizer  
from .naver_smtp_with_attachments import NaverSMTPSender

__version__ = "2.2.0"
__author__ = "Claude Code Assistant"

__all__ = [
    # 통합 클래스들
    'NaverMailSuite',
    'MailProcessor',
    'BatchProcessor',
    
    # 편의 함수들
    'quick_summary',
    'create_daily_digest',
    
    # 개별 모듈 클래스들
    'NaverMailParser',
    'TextSummarizer', 
    'NaverSMTPSender'
]