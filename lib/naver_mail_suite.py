#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
네이버 메일 통합 모듈 (Naver Mail Suite)

이 모듈은 네이버 메일 파싱, LLM 요약, SMTP 발송 기능을 통합한 올인원 솔루션입니다.

주요 클래스:
- NaverMailSuite: 모든 기능을 통합한 메인 클래스
- MailProcessor: 메일 처리 워크플로우 관리
- BatchProcessor: 대량 메일 처리

사용 예시:
    suite = NaverMailSuite(
        naver_username="user@naver.com",
        naver_password="app_password",
        openai_api_key="your_api_key"
    )
    
    # 메일 가져오기 → 요약 → 전송
    suite.fetch_summarize_send(
        to_emails=["recipient@example.com"],
        summary_type="korean",
        limit=5
    )
"""

import os
import json
import time
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
from datetime import datetime
import logging

# 기존 모듈들 import
from lib.naver_mail_parser import NaverMailParser
from lib.text_summarizer import TextSummarizer
from lib.naver_smtp_with_attachments import NaverSMTPSender

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NaverMailSuite:
    """
    네이버 메일 통합 처리 클래스
    
    메일 파싱, LLM 요약, SMTP 발송을 하나의 클래스에서 처리합니다.
    """
    
    def __init__(self, 
                 naver_username: str, 
                 naver_password: str,
                 openai_api_key: str = None,
                 openai_model: str = "gpt-3.5-turbo"):
        """
        초기화
        
        Args:
            naver_username: 네이버 아이디
            naver_password: 네이버 앱 비밀번호
            openai_api_key: OpenAI API 키 (환경변수에서 가져올 수도 있음)
            openai_model: 사용할 OpenAI 모델
        """
        self.naver_username = naver_username
        self.naver_password = naver_password
        
        # 컴포넌트들
        self.mail_parser = None
        self.summarizer = None
        self.smtp_sender = None
        
        # 상태 관리
        self.parser_connected = False
        self.summarizer_ready = False
        self.smtp_ready = False
        
        # OpenAI 설정
        if openai_api_key:
            os.environ['OPENAI_API_KEY'] = openai_api_key
        
        self.openai_model = openai_model
        
        # 초기화
        self._initialize_components()
    
    def _initialize_components(self):
        """모든 컴포넌트 초기화"""
        try:
            # 메일 파서 초기화
            self.mail_parser = NaverMailParser(self.naver_username, self.naver_password)
            if self.mail_parser.connect():
                self.mail_parser.select_mailbox('INBOX')
                self.parser_connected = True
                logger.info("메일 파서 연결 성공")
            else:
                logger.error("메일 파서 연결 실패")
            
            # LLM 요약기 초기화
            if os.getenv('OPENAI_API_KEY'):
                self.summarizer = TextSummarizer(model=self.openai_model)
                self.summarizer_ready = True
                logger.info("LLM 요약기 초기화 성공")
            else:
                logger.warning("OpenAI API 키가 없어 요약기를 초기화할 수 없습니다")
            
            # SMTP 발송기 초기화
            self.smtp_sender = NaverSMTPSender(self.naver_username, self.naver_password)
            test_result = self.smtp_sender.test_connection()
            if test_result['success']:
                self.smtp_ready = True
                logger.info("SMTP 발송기 초기화 성공")
            else:
                logger.error(f"SMTP 발송기 초기화 실패: {test_result['error']}")
                
        except Exception as e:
            logger.error(f"컴포넌트 초기화 오류: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """현재 시스템 상태 반환"""
        return {
            'parser_connected': self.parser_connected,
            'summarizer_ready': self.summarizer_ready,
            'smtp_ready': self.smtp_ready,
            'all_ready': self.parser_connected and self.summarizer_ready and self.smtp_ready,
            'naver_username': self.naver_username,
            'openai_model': self.openai_model
        }
    
    def fetch_emails(self,
                    limit: int = 10,
                    criteria: str = 'ALL',
                    download_full: bool = False,
                    extract_attachment_text: bool = True) -> List[Dict]:
        """
        이메일 가져오기

        Args:
            limit: 가져올 이메일 수
            criteria: 검색 조건 ('ALL', 'UNSEEN', etc.)
            download_full: 첨부파일 포함 전체 다운로드 여부
            extract_attachment_text: 첨부파일 텍스트 추출 여부

        Returns:
            List[Dict]: 가져온 이메일 리스트
        """
        if not self.parser_connected:
            raise Exception("메일 파서가 연결되지 않았습니다")

        try:
            emails = self.mail_parser.get_emails(
                criteria=criteria,
                limit=limit,
                download_full=download_full,
                extract_attachment_text=extract_attachment_text
            )
            logger.info(f"{len(emails)}개 이메일을 가져왔습니다")
            return emails
        except Exception as e:
            logger.error(f"이메일 가져오기 실패: {e}")
            raise

    def download_email_full(self, email_id: str, extract_attachment_text: bool = True) -> Dict:
        """
        특정 이메일 전체 다운로드 (본문 + 첨부파일)

        Args:
            email_id: 이메일 ID
            extract_attachment_text: 첨부파일 텍스트 추출 여부

        Returns:
            Dict: 다운로드된 이메일 정보
        """
        if not self.parser_connected:
            raise Exception("메일 파서가 연결되지 않았습니다")

        try:
            email_id_bytes = email_id.encode() if isinstance(email_id, str) else email_id
            email_data = self.mail_parser.download_email_full(email_id_bytes, extract_attachment_text=extract_attachment_text)
            if email_data:
                logger.info(f"이메일 전체 다운로드 완료: {email_id}")
            return email_data
        except Exception as e:
            logger.error(f"이메일 다운로드 실패: {e}")
            raise

    def view_email_content(self, email_id: str) -> Dict:
        """
        특정 이메일의 전체 내용 보기 (로컬 저장된 내용 또는 새로 다운로드)

        Args:
            email_id: 이메일 ID

        Returns:
            Dict: 이메일 상세 내용
        """
        if not self.parser_connected:
            raise Exception("메일 파서가 연결되지 않았습니다")

        try:
            email_content = self.mail_parser.view_email_content(email_id)
            return email_content
        except Exception as e:
            logger.error(f"이메일 내용 보기 실패: {e}")
            raise

    def get_attachment_path(self, email_id: str, filename: str) -> str:
        """
        특정 첨부파일의 경로 반환

        Args:
            email_id: 이메일 ID
            filename: 첨부파일명

        Returns:
            str: 첨부파일 경로 (없으면 None)
        """
        if not self.parser_connected:
            raise Exception("메일 파서가 연결되지 않았습니다")

        try:
            return self.mail_parser.get_attachment_path(email_id, filename)
        except Exception as e:
            logger.error(f"첨부파일 경로 가져오기 실패: {e}")
            return None

    def search_emails(self, criteria: str = 'ALL', limit: int = 10) -> List:
        """
        이메일 ID 검색

        Args:
            criteria: 검색 조건
            limit: 검색 개수

        Returns:
            List: 이메일 ID 리스트
        """
        if not self.parser_connected:
            raise Exception("메일 파서가 연결되지 않았습니다")

        try:
            return self.mail_parser.search_emails(criteria, limit)
        except Exception as e:
            logger.error(f"이메일 검색 실패: {e}")
            raise

    def select_mailbox(self, mailbox: str = 'INBOX'):
        """
        메일박스 선택

        Args:
            mailbox: 메일박스 이름 (기본값: 'INBOX')
        """
        if not self.parser_connected:
            raise Exception("메일 파서가 연결되지 않았습니다")

        try:
            self.mail_parser.select_mailbox(mailbox)
            logger.info(f"메일박스 선택: {mailbox}")
        except Exception as e:
            logger.error(f"메일박스 선택 실패: {e}")
            raise
    
    def summarize_email(self, 
                       email_data: Dict, 
                       summary_type: str = "detailed") -> Dict:
        """
        개별 이메일 요약
        
        Args:
            email_data: 이메일 데이터
            summary_type: 요약 타입 (brief, detailed, bullet, korean)
        
        Returns:
            Dict: 요약 결과
        """
        if not self.summarizer_ready:
            raise Exception("LLM 요약기가 준비되지 않았습니다")
        
        try:
            # 이메일 내용을 임시 파일로 저장
            email_content = f"""
제목: {email_data.get('subject', '')}
발신자: {email_data.get('sender', '')}
날짜: {email_data.get('date', '')}

{"="*50}

{email_data.get('body', '')}
            """.strip()
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(email_content)
                temp_file_path = temp_file.name
            
            # LLM으로 요약
            result = self.summarizer.summarize_file(temp_file_path, summary_type)
            
            # 임시 파일 삭제
            os.unlink(temp_file_path)
            
            # 원본 이메일 정보와 요약 결과 합치기
            if "error" not in result:
                return {
                    **email_data,
                    'summary': result['summary'],
                    'summary_tokens': result['summary_tokens'],
                    'original_tokens': result['original_tokens'],
                    'compression_ratio': result['compression_ratio'],
                    'summary_type': summary_type
                }
            else:
                return {**email_data, 'summary_error': result['error']}
                
        except Exception as e:
            logger.error(f"이메일 요약 실패: {e}")
            return {**email_data, 'summary_error': str(e)}
    
    def summarize_emails(self,
                        emails: List[Dict],
                        summary_type: str = "detailed",
                        delay: float = 1.0) -> List[Dict]:
        """
        여러 이메일 일괄 요약

        Args:
            emails: 이메일 리스트
            summary_type: 요약 타입
            delay: API 호출 간격 (초)

        Returns:
            List[Dict]: 요약된 이메일 리스트
        """
        if not self.summarizer_ready:
            raise Exception("LLM 요약기가 준비되지 않았습니다")

        summarized_emails = []

        for i, email in enumerate(emails, 1):
            logger.info(f"[{i}/{len(emails)}] 이메일 요약 중: {email.get('subject', 'No Subject')[:50]}...")

            try:
                summarized_email = self.summarize_email(email, summary_type)
                summarized_emails.append(summarized_email)

                if 'summary' in summarized_email:
                    logger.info(f"요약 완료 (압축률: {summarized_email.get('compression_ratio', 0)}%)")
                else:
                    logger.warning(f"요약 실패: {summarized_email.get('summary_error', 'Unknown error')}")

                # API 호출 제한 방지
                if i < len(emails):
                    time.sleep(delay)

            except Exception as e:
                logger.error(f"이메일 {i} 처리 실패: {e}")
                summarized_emails.append({**email, 'summary_error': str(e)})

        return summarized_emails

    def summarize_email_advanced(self,
                                email_id: str,
                                summary_type: str = "detailed",
                                summarize_body: bool = True,
                                summarize_attachments: bool = False) -> Dict:
        """
        메일 본문과 첨부파일을 선택적으로 요약 (고급 기능)

        Args:
            email_id: 이메일 ID
            summary_type: 요약 타입 (brief, detailed, bullet, korean)
            summarize_body: 본문 요약 여부
            summarize_attachments: 첨부파일 요약 여부

        Returns:
            Dict: 요약 결과 (본문 요약, 첨부파일별 요약, 통합 요약 포함)
        """
        if not self.summarizer_ready:
            raise Exception("LLM 요약기가 준비되지 않았습니다")

        if not self.parser_connected:
            raise Exception("메일 파서가 연결되지 않았습니다")

        try:
            result = self.summarizer.summarize_email_from_parser(
                parser=self.mail_parser,
                email_id=email_id,
                summary_type=summary_type,
                summarize_body=summarize_body,
                summarize_attachments=summarize_attachments
            )

            return result

        except Exception as e:
            logger.error(f"고급 이메일 요약 실패: {e}")
            return {'error': str(e)}

    def summarize_selected_emails_advanced(self,
                                          email_ids: List[str],
                                          summary_type: str = "detailed",
                                          summarize_body: bool = True,
                                          summarize_attachments: bool = False) -> List[Dict]:
        """
        선택한 여러 메일을 본문/첨부파일 분리하여 요약

        Args:
            email_ids: 이메일 ID 리스트
            summary_type: 요약 타입
            summarize_body: 본문 요약 여부
            summarize_attachments: 첨부파일 요약 여부

        Returns:
            List[Dict]: 요약 결과 리스트
        """
        if not self.summarizer_ready:
            raise Exception("LLM 요약기가 준비되지 않았습니다")

        if not self.parser_connected:
            raise Exception("메일 파서가 연결되지 않았습니다")

        results = []

        for i, email_id in enumerate(email_ids, 1):
            logger.info(f"[{i}/{len(email_ids)}] 메일 ID {email_id} 요약 중...")

            try:
                result = self.summarize_email_advanced(
                    email_id=email_id,
                    summary_type=summary_type,
                    summarize_body=summarize_body,
                    summarize_attachments=summarize_attachments
                )

                results.append(result)

                if 'error' not in result:
                    logger.info(f"✅ 완료 (압축률: {result.get('total_compression_ratio', 0)}%)")
                else:
                    logger.warning(f"❌ 실패: {result.get('error', 'Unknown')}")

                # API 호출 제한 방지
                if i < len(email_ids):
                    time.sleep(1.0)

            except Exception as e:
                logger.error(f"메일 {email_id} 요약 실패: {e}")
                results.append({'error': str(e), 'email_id': email_id})

        return results

    def get_email_body_and_attachments_separately(self, email_id: str) -> Dict:
        """
        메일의 본문과 첨부파일을 명확히 분리

        Args:
            email_id: 이메일 ID

        Returns:
            Dict: 본문과 첨부파일 정보가 분리된 데이터
        """
        if not self.summarizer_ready:
            raise Exception("LLM 요약기가 준비되지 않았습니다")

        if not self.parser_connected:
            raise Exception("메일 파서가 연결되지 않았습니다")

        try:
            return self.summarizer.get_email_body_and_attachments_separately(
                parser=self.mail_parser,
                email_id=email_id
            )
        except Exception as e:
            logger.error(f"본문/첨부파일 분리 실패: {e}")
            return {'error': str(e)}

    def summarize_downloaded_attachment(self, attachment_path: str, summary_type: str = "detailed") -> Dict:
        """
        다운로드 받은 첨부파일을 파싱하고 요약

        Args:
            attachment_path: 첨부파일 경로
            summary_type: 요약 타입 (brief, detailed, bullet, korean)

        Returns:
            Dict: 요약 결과
        """
        if not self.summarizer_ready:
            raise Exception("LLM 요약기가 준비되지 않았습니다")

        try:
            return self.summarizer.summarize_downloaded_attachment(attachment_path, summary_type)
        except Exception as e:
            logger.error(f"첨부파일 요약 실패: {e}")
            return {'error': str(e)}

    def summarize_email_attachments_from_path(self, email_folder_path: str, summary_type: str = "detailed") -> Dict:
        """
        이메일 폴더의 모든 첨부파일을 파싱하고 요약

        Args:
            email_folder_path: 이메일 다운로드 폴더 경로 (예: downloads/email_123)
            summary_type: 요약 타입 (brief, detailed, bullet, korean)

        Returns:
            Dict: 전체 첨부파일 요약 결과
        """
        if not self.summarizer_ready:
            raise Exception("LLM 요약기가 준비되지 않았습니다")

        try:
            return self.summarizer.summarize_email_attachments_from_path(email_folder_path, summary_type)
        except Exception as e:
            logger.error(f"이메일 첨부파일 일괄 요약 실패: {e}")
            return {'error': str(e)}
    
    def send_email(self, 
                  to_emails: Union[str, List[str]],
                  subject: str,
                  body: str,
                  cc_emails: Optional[Union[str, List[str]]] = None,
                  bcc_emails: Optional[Union[str, List[str]]] = None,
                  attachments: Optional[List[str]] = None,
                  is_html: bool = False) -> Dict:
        """
        이메일 전송
        
        Args:
            to_emails: 받는 사람 (문자열 또는 리스트)
            subject: 제목
            body: 본문
            cc_emails: 참조
            bcc_emails: 숨은참조
            attachments: 첨부파일 경로 리스트
            is_html: HTML 형식 여부
        
        Returns:
            Dict: 전송 결과
        """
        if not self.smtp_ready:
            raise Exception("SMTP 발송기가 준비되지 않았습니다")
        
        try:
            # 문자열을 리스트로 변환
            if isinstance(to_emails, str):
                to_emails = [email.strip() for email in to_emails.split(',')]
            if isinstance(cc_emails, str):
                cc_emails = [email.strip() for email in cc_emails.split(',')]
            if isinstance(bcc_emails, str):
                bcc_emails = [email.strip() for email in bcc_emails.split(',')]
            
            result = self.smtp_sender.send_email(
                to_emails=to_emails,
                subject=subject,
                body=body,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
                attachments=attachments,
                is_html=is_html
            )
            
            if result['success']:
                logger.info(f"이메일 전송 성공: {len(result['to'])}명에게 전송")
            else:
                logger.error(f"이메일 전송 실패: {result['error']}")
            
            return result
            
        except Exception as e:
            logger.error(f"이메일 전송 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def fetch_summarize_send(self,
                           to_emails: Union[str, List[str]],
                           subject_template: str = "이메일 요약 결과",
                           summary_type: str = "detailed",
                           limit: int = 10,
                           criteria: str = 'ALL',
                           cc_emails: Optional[Union[str, List[str]]] = None,
                           attachments: Optional[List[str]] = None,
                           is_html: bool = False,
                           save_results: bool = True) -> Dict:
        """
        통합 워크플로우: 메일 가져오기 → 요약 → 전송
        
        Args:
            to_emails: 받는 사람
            subject_template: 제목 템플릿
            summary_type: 요약 타입
            limit: 가져올 이메일 수
            criteria: 검색 조건
            cc_emails: 참조
            attachments: 첨부파일
            is_html: HTML 형식 여부
            save_results: 결과 저장 여부
        
        Returns:
            Dict: 전체 처리 결과
        """
        logger.info("통합 워크플로우 시작: 메일 가져오기 → 요약 → 전송")
        
        try:
            # 1. 메일 가져오기
            logger.info("1단계: 메일 가져오기")
            emails = self.fetch_emails(limit=limit, criteria=criteria)
            
            if not emails:
                return {'success': False, 'error': '가져올 이메일이 없습니다'}
            
            # 2. 요약하기
            logger.info("2단계: 이메일 요약")
            summarized_emails = self.summarize_emails(emails, summary_type)
            
            # 3. 요약 결과 정리
            successful_summaries = [e for e in summarized_emails if 'summary' in e]
            
            if not successful_summaries:
                return {'success': False, 'error': '요약된 이메일이 없습니다'}
            
            # 4. 이메일 본문 생성
            email_body = self._create_summary_email_body(successful_summaries, summary_type)
            
            # 5. 이메일 전송
            logger.info("3단계: 요약 결과 이메일 전송")
            send_result = self.send_email(
                to_emails=to_emails,
                subject=subject_template,
                body=email_body,
                cc_emails=cc_emails,
                attachments=attachments,
                is_html=is_html
            )
            
            # 6. 결과 저장 (선택사항)
            if save_results:
                self._save_workflow_results(summarized_emails, send_result)
            
            # 7. 최종 결과 반환
            result = {
                'success': True,
                'emails_fetched': len(emails),
                'emails_summarized': len(successful_summaries),
                'send_result': send_result,
                'summary_type': summary_type,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"통합 워크플로우 완료: {len(emails)}개 메일 → {len(successful_summaries)}개 요약 → 전송")
            return result
            
        except Exception as e:
            logger.error(f"통합 워크플로우 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_summary_email_body(self, 
                                  summarized_emails: List[Dict], 
                                  summary_type: str) -> str:
        """요약 결과로 이메일 본문 생성"""
        
        body_parts = [
            "📧 네이버 메일 요약 결과",
            "=" * 50,
            "",
            f"📊 요약 정보:",
            f"  • 처리된 이메일: {len(summarized_emails)}개",
            f"  • 요약 타입: {summary_type}",
            f"  • 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "📝 요약 내용:",
            "=" * 50
        ]
        
        for i, email in enumerate(summarized_emails, 1):
            body_parts.extend([
                "",
                f"[{i}] {email.get('subject', 'No Subject')}",
                f"발신자: {email.get('sender', 'Unknown')}",
                f"날짜: {email.get('date', 'Unknown')}",
                f"압축률: {email.get('compression_ratio', 0)}%",
                "",
                f"{email.get('summary', 'No Summary')}",
                "-" * 50
            ])
        
        body_parts.extend([
            "",
            "🤖 이 요약은 AI를 활용하여 자동 생성되었습니다.",
            "📧 네이버 메일 통합 시스템"
        ])
        
        return "\n".join(body_parts)
    
    def _save_workflow_results(self, 
                              summarized_emails: List[Dict], 
                              send_result: Dict):
        """워크플로우 결과 저장"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"mail_workflow_result_{timestamp}.json"
            
            result_data = {
                'timestamp': timestamp,
                'summarized_emails': summarized_emails,
                'send_result': send_result,
                'system_status': self.get_status()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"워크플로우 결과 저장: {filename}")
            
        except Exception as e:
            logger.warning(f"결과 저장 실패: {e}")


class MailProcessor:
    """
    메일 처리 워크플로우를 관리하는 클래스
    """
    
    def __init__(self, suite: NaverMailSuite):
        self.suite = suite
    
    def process_and_forward(self,
                          forward_to: Union[str, List[str]],
                          filter_criteria: Dict = None,
                          summary_type: str = "brief",
                          subject_prefix: str = "[요약]") -> Dict:
        """
        메일을 가져와서 요약한 후 지정된 주소로 전달
        
        Args:
            forward_to: 전달받을 이메일 주소
            filter_criteria: 필터링 조건
            summary_type: 요약 타입
            subject_prefix: 제목 접두사
        
        Returns:
            Dict: 처리 결과
        """
        try:
            # 필터 조건 설정
            criteria = filter_criteria.get('criteria', 'ALL') if filter_criteria else 'ALL'
            limit = filter_criteria.get('limit', 10) if filter_criteria else 10
            
            # 통합 워크플로우 실행
            result = self.suite.fetch_summarize_send(
                to_emails=forward_to,
                subject_template=f"{subject_prefix} 메일 요약 ({datetime.now().strftime('%m/%d')})",
                summary_type=summary_type,
                limit=limit,
                criteria=criteria
            )
            
            return result
            
        except Exception as e:
            logger.error(f"메일 처리 및 전달 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_digest(self,
                     digest_emails: Union[str, List[str]],
                     digest_type: str = "daily") -> Dict:
        """
        메일 다이제스트 생성 및 전송
        
        Args:
            digest_emails: 다이제스트를 받을 이메일 주소
            digest_type: 다이제스트 타입 (daily, weekly)
        
        Returns:
            Dict: 다이제스트 생성 결과
        """
        try:
            criteria_map = {
                'daily': 'SINCE "01-Jan-2024"',  # 실제로는 오늘 날짜
                'weekly': 'SINCE "01-Jan-2024"'  # 실제로는 일주일 전 날짜
            }
            
            criteria = criteria_map.get(digest_type, 'ALL')
            
            result = self.suite.fetch_summarize_send(
                to_emails=digest_emails,
                subject_template=f"📧 {digest_type.title()} 메일 다이제스트 - {datetime.now().strftime('%Y-%m-%d')}",
                summary_type="detailed",
                criteria=criteria,
                limit=20
            )
            
            return result
            
        except Exception as e:
            logger.error(f"다이제스트 생성 실패: {e}")
            return {'success': False, 'error': str(e)}


class BatchProcessor:
    """
    대량 메일 처리를 위한 클래스
    """
    
    def __init__(self, suite: NaverMailSuite):
        self.suite = suite
    
    def process_large_mailbox(self,
                            batch_size: int = 50,
                            summary_type: str = "brief",
                            output_dir: str = None) -> Dict:
        """
        대용량 메일박스 일괄 처리
        
        Args:
            batch_size: 배치 크기
            summary_type: 요약 타입
            output_dir: 출력 디렉토리
        
        Returns:
            Dict: 처리 결과
        """
        try:
            # 출력 디렉토리 설정
            if not output_dir:
                output_dir = f"batch_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            Path(output_dir).mkdir(exist_ok=True)
            
            # 전체 이메일 수 확인 (대략적)
            logger.info("대량 메일박스 처리 시작")
            
            processed_count = 0
            batch_number = 1
            all_results = []
            
            while True:
                try:
                    # 배치 단위로 메일 가져오기
                    emails = self.suite.fetch_emails(limit=batch_size)
                    
                    if not emails:
                        break
                    
                    logger.info(f"배치 {batch_number}: {len(emails)}개 이메일 처리 중")
                    
                    # 요약 처리
                    summarized_emails = self.suite.summarize_emails(emails, summary_type, delay=1.5)
                    
                    # 배치 결과 저장
                    batch_file = Path(output_dir) / f"batch_{batch_number:03d}.json"
                    with open(batch_file, 'w', encoding='utf-8') as f:
                        json.dump(summarized_emails, f, ensure_ascii=False, indent=2)
                    
                    all_results.extend(summarized_emails)
                    processed_count += len(emails)
                    batch_number += 1
                    
                    logger.info(f"배치 {batch_number-1} 완료. 총 처리: {processed_count}개")
                    
                    # 배치 간 대기 (API 제한 방지)
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"배치 {batch_number} 처리 실패: {e}")
                    break
            
            # 전체 결과 요약 저장
            summary_file = Path(output_dir) / "processing_summary.json"
            summary_data = {
                'total_processed': processed_count,
                'total_batches': batch_number - 1,
                'successful_summaries': len([r for r in all_results if 'summary' in r]),
                'failed_summaries': len([r for r in all_results if 'summary_error' in r]),
                'processing_time': datetime.now().isoformat(),
                'summary_type': summary_type
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"대량 처리 완료: {processed_count}개 이메일, 결과: {output_dir}")
            
            return {
                'success': True,
                'processed_count': processed_count,
                'output_dir': output_dir,
                'summary': summary_data
            }
            
        except Exception as e:
            logger.error(f"대량 처리 실패: {e}")
            return {'success': False, 'error': str(e)}


# 모듈 레벨 함수들 (간편 사용을 위한)

def quick_summary(naver_username: str,
                 naver_password: str,
                 openai_api_key: str,
                 to_email: str,
                 limit: int = 5) -> Dict:
    """
    빠른 메일 요약 및 전송
    
    Args:
        naver_username: 네이버 아이디
        naver_password: 네이버 앱 비밀번호
        openai_api_key: OpenAI API 키
        to_email: 받을 이메일 주소
        limit: 처리할 이메일 수
    
    Returns:
        Dict: 처리 결과
    """
    try:
        suite = NaverMailSuite(naver_username, naver_password, openai_api_key)
        return suite.fetch_summarize_send(
            to_emails=to_email,
            limit=limit,
            summary_type="korean"
        )
    except Exception as e:
        return {'success': False, 'error': str(e)}


def create_daily_digest(naver_username: str,
                       naver_password: str,
                       openai_api_key: str,
                       digest_emails: Union[str, List[str]]) -> Dict:
    """
    일일 메일 다이제스트 생성
    
    Args:
        naver_username: 네이버 아이디
        naver_password: 네이버 앱 비밀번호
        openai_api_key: OpenAI API 키
        digest_emails: 다이제스트를 받을 이메일 주소
    
    Returns:
        Dict: 다이제스트 생성 결과
    """
    try:
        suite = NaverMailSuite(naver_username, naver_password, openai_api_key)
        processor = MailProcessor(suite)
        return processor.create_digest(digest_emails, "daily")
    except Exception as e:
        return {'success': False, 'error': str(e)}


# 사용 예시 및 테스트
if __name__ == "__main__":
    # 환경 변수에서 설정 읽기
    NAVER_USERNAME = os.getenv('NAVER_USERNAME', 'your_id@naver.com')
    NAVER_PASSWORD = os.getenv('NAVER_PASSWORD', 'your_app_password')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your_openai_key')
    
    try:
        # 1. 기본 사용법
        print("=== 네이버 메일 통합 모듈 테스트 ===")
        
        suite = NaverMailSuite(
            naver_username=NAVER_USERNAME,
            naver_password=NAVER_PASSWORD,
            openai_api_key=OPENAI_API_KEY
        )
        
        # 시스템 상태 확인
        status = suite.get_status()
        print(f"시스템 상태: {status}")
        
        if not status['all_ready']:
            print("⚠️ 일부 컴포넌트가 준비되지 않았습니다.")
            exit(1)
        
        # 2. 간단한 워크플로우 테스트
        print("\n=== 간단한 워크플로우 테스트 ===")
        result = suite.fetch_summarize_send(
            to_emails="test@example.com",  # 실제 이메일로 변경
            summary_type="korean",
            limit=3
        )
        
        print(f"워크플로우 결과: {result}")
        
        # 3. 메일 프로세서 테스트
        print("\n=== 메일 프로세서 테스트 ===")
        processor = MailProcessor(suite)
        
        digest_result = processor.create_digest("digest@example.com")
        print(f"다이제스트 결과: {digest_result}")
        
        # 4. 빠른 요약 함수 테스트
        print("\n=== 빠른 요약 함수 테스트 ===")
        quick_result = quick_summary(
            NAVER_USERNAME,
            NAVER_PASSWORD,
            OPENAI_API_KEY,
            "quick@example.com",
            limit=2
        )
        print(f"빠른 요약 결과: {quick_result}")
        
        print("\n✅ 모든 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        print("환경 변수를 확인하고 실제 값으로 설정해주세요:")
        print("- NAVER_USERNAME")
        print("- NAVER_PASSWORD") 
        print("- OPENAI_API_KEY")