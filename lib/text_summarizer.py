import os
from openai import OpenAI
from pathlib import Path
import tiktoken
import json
import time
from typing import List, Dict, Optional

# naver_mail_parser import 추가
from lib.naver_mail_parser import NaverMailParser

class TextSummarizer:
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        """
        텍스트 요약기 초기화

        Args:
            api_key: OpenAI API 키 (환경변수 OPENAI_API_KEY에서 자동 로드)
            model: 사용할 모델 (gpt-3.5-turbo, gpt-4, etc.)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API 키가 필요합니다. 환경변수 OPENAI_API_KEY를 설정하거나 api_key 매개변수를 제공하세요.")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.encoding = tiktoken.encoding_for_model(model)
        
        # 모델별 토큰 제한
        self.token_limits = {
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-4-turbo": 128000,
            "gpt-4o": 128000
        }
        
        self.max_tokens = self.token_limits.get(model, 4096)
    
    def count_tokens(self, text: str) -> int:
        """텍스트의 토큰 수 계산"""
        return len(self.encoding.encode(text))
    
    def read_text_file(self, file_path: str) -> str:
        """텍스트 파일 읽기 (다양한 인코딩 지원)"""
        encodings = ['utf-8', 'cp949', 'euc-kr', 'latin-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    return file.read()
            except UnicodeDecodeError:
                continue
        
        raise ValueError(f"파일을 읽을 수 없습니다: {file_path}")
    
    def split_text_by_tokens(self, text: str, max_chunk_tokens: int = 3000) -> List[str]:
        """텍스트를 토큰 기준으로 분할"""
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            test_chunk = current_chunk + sentence + ". "
            if self.count_tokens(test_chunk) > max_chunk_tokens:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
            else:
                current_chunk = test_chunk
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def summarize_chunk(self, text: str, summary_type: str = "detailed") -> str:
        """텍스트 청크 요약"""
        prompts = {
            "brief": "다음 텍스트를 3-5문장으로 간단히 요약해주세요:",
            "detailed": "다음 텍스트를 자세히 요약해주세요. 주요 내용과 핵심 포인트를 포함하여 요약하세요:",
            "bullet": "다음 텍스트를 불렛 포인트 형태로 요약해주세요:",
            "korean": "다음 텍스트를 한국어로 요약해주세요. 주요 내용을 놓치지 않고 자연스럽게 요약하세요:"
        }

        prompt = prompts.get(summary_type, prompts["detailed"])

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 텍스트 요약 전문가입니다. 정확하고 간결한 요약을 제공합니다."},
                    {"role": "user", "content": f"{prompt}\n\n{text}"}
                ],
                max_tokens=1000,
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"요약 실패: {str(e)}"
    
    def summarize_file(self, file_path: str, summary_type: str = "detailed", 
                      output_file: str = None) -> Dict:
        """파일 요약"""
        try:
            # 파일 읽기
            text = self.read_text_file(file_path)
            file_size = len(text)
            token_count = self.count_tokens(text)
            
            print(f"파일 크기: {file_size:,} 문자")
            print(f"토큰 수: {token_count:,}")
            
            # 텍스트가 너무 긴 경우 분할
            if token_count > self.max_tokens - 1000:  # 응답용 토큰 여유분
                print("텍스트가 길어 청크로 분할합니다...")
                chunks = self.split_text_by_tokens(text, max_chunk_tokens=3000)
                
                summaries = []
                for i, chunk in enumerate(chunks, 1):
                    print(f"청크 {i}/{len(chunks)} 요약 중...")
                    summary = self.summarize_chunk(chunk, summary_type)
                    summaries.append(summary)
                    time.sleep(1)  # API 호출 제한 방지
                
                # 전체 요약 생성
                combined_summary = "\n\n".join(summaries)
                if self.count_tokens(combined_summary) > 3000:
                    final_summary = self.summarize_chunk(combined_summary, summary_type)
                else:
                    final_summary = combined_summary
                
            else:
                print("단일 요약 생성 중...")
                final_summary = self.summarize_chunk(text, summary_type)
            
            # 결과 정리
            result = {
                "file_path": file_path,
                "original_size": file_size,
                "original_tokens": token_count,
                "summary": final_summary,
                "summary_tokens": self.count_tokens(final_summary),
                "compression_ratio": round(self.count_tokens(final_summary) / token_count * 100, 2)
            }
            
            # 파일로 저장
            if output_file:
                self.save_summary(result, output_file)
            
            return result
            
        except Exception as e:
            return {"error": f"요약 실패: {str(e)}"}
    
    def save_summary(self, result: Dict, output_file: str):
        """요약 결과를 파일로 저장"""
        output_path = Path(output_file)

        if output_path.suffix.lower() == '.json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        else:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"파일: {result['file_path']}\n")
                f.write(f"원본 크기: {result['original_size']:,} 문자\n")
                f.write(f"원본 토큰: {result['original_tokens']:,}\n")
                f.write(f"요약 토큰: {result['summary_tokens']:,}\n")
                f.write(f"압축률: {result['compression_ratio']}%\n")
                f.write("=" * 50 + "\n\n")
                f.write(result['summary'])

    def summarize_email(self, email_data: Dict, summary_type: str = "detailed",
                       include_attachments: bool = True, only_attachments: bool = False) -> Dict:
        """
        파싱된 메일 데이터를 직접 요약

        Args:
            email_data: NaverMailParser에서 파싱된 이메일 데이터
            summary_type: 요약 타입 (brief, detailed, bullet, korean)
            include_attachments: 첨부파일 텍스트 포함 여부 (본문 + 첨부파일)
            only_attachments: True일 경우 첨부파일만 요약 (본문 제외)

        Returns:
            Dict: 요약 결과
        """
        try:
            # 이메일 내용 구성
            email_content_parts = []

            # 제목
            if 'subject' in email_data:
                email_content_parts.append(f"제목: {email_data['subject']}")

            # 발신자
            if 'sender' in email_data:
                email_content_parts.append(f"발신자: {email_data['sender']}")

            # 날짜
            if 'date' in email_data:
                email_content_parts.append(f"날짜: {email_data['date']}")

            email_content_parts.append("=" * 50)

            # 본문과 첨부파일 처리
            if 'body' in email_data:
                body_text = email_data['body']

                # 본문과 첨부파일 텍스트 분리
                if '=== 첨부파일:' in body_text:
                    body_parts = body_text.split('\n\n=== 첨부파일:')
                    body_only = body_parts[0]
                    attachment_text = '\n\n=== 첨부파일:'.join(body_parts[1:]) if len(body_parts) > 1 else ''

                    # 옵션에 따라 내용 선택
                    if only_attachments:
                        # 첨부파일만 요약
                        if attachment_text:
                            email_content_parts.append(f"\n[첨부파일 내용만 요약]\n=== 첨부파일:{attachment_text}")
                        else:
                            return {"error": "첨부파일 텍스트가 없습니다"}
                    elif include_attachments:
                        # 본문 + 첨부파일
                        email_content_parts.append(body_only)
                        if attachment_text:
                            email_content_parts.append(f"\n=== 첨부파일:{attachment_text}")
                    else:
                        # 본문만
                        email_content_parts.append(body_only)
                else:
                    # 첨부파일 구분자가 없는 경우
                    if only_attachments:
                        return {"error": "첨부파일 텍스트가 없습니다"}
                    email_content_parts.append(body_text)

            email_content = '\n'.join(email_content_parts)

            # 토큰 수 계산
            token_count = self.count_tokens(email_content)

            # 텍스트가 너무 긴 경우 분할
            if token_count > self.max_tokens - 1000:
                print("메일 내용이 길어 청크로 분할합니다...")
                chunks = self.split_text_by_tokens(email_content, max_chunk_tokens=3000)

                summaries = []
                for i, chunk in enumerate(chunks, 1):
                    print(f"청크 {i}/{len(chunks)} 요약 중...")
                    summary = self.summarize_chunk(chunk, summary_type)
                    summaries.append(summary)
                    time.sleep(1)

                combined_summary = "\n\n".join(summaries)
                if self.count_tokens(combined_summary) > 3000:
                    final_summary = self.summarize_chunk(combined_summary, summary_type)
                else:
                    final_summary = combined_summary
            else:
                final_summary = self.summarize_chunk(email_content, summary_type)

            # 요약 범위 표시
            summary_scope = "첨부파일만" if only_attachments else ("본문+첨부파일" if include_attachments else "본문만")

            # 결과 반환
            result = {
                "email_id": email_data.get('id', 'unknown'),
                "subject": email_data.get('subject', ''),
                "sender": email_data.get('sender', ''),
                "original_tokens": token_count,
                "summary": final_summary,
                "summary_tokens": self.count_tokens(final_summary),
                "compression_ratio": round(self.count_tokens(final_summary) / token_count * 100, 2),
                "summary_type": summary_type,
                "summary_scope": summary_scope,
                "included_attachments": include_attachments,
                "only_attachments": only_attachments
            }

            return result

        except Exception as e:
            return {"error": f"메일 요약 실패: {str(e)}"}

    def summarize_emails_batch(self, emails: List[Dict], summary_type: str = "detailed",
                               include_attachments: bool = True, only_attachments: bool = False,
                               delay: float = 1.0) -> List[Dict]:
        """
        여러 메일을 일괄 요약

        Args:
            emails: 파싱된 이메일 리스트
            summary_type: 요약 타입
            include_attachments: 첨부파일 텍스트 포함 여부 (본문 + 첨부파일)
            only_attachments: True일 경우 첨부파일만 요약
            delay: API 호출 간격 (초)

        Returns:
            List[Dict]: 요약 결과 리스트
        """
        results = []

        for i, email_data in enumerate(emails, 1):
            print(f"[{i}/{len(emails)}] 메일 요약 중: {email_data.get('subject', 'No Subject')[:50]}...")

            try:
                result = self.summarize_email(email_data, summary_type, include_attachments, only_attachments)
                results.append(result)

                if 'summary' in result:
                    print(f"✅ 완료 (압축률: {result['compression_ratio']}%, 범위: {result.get('summary_scope', 'N/A')})")
                else:
                    print(f"❌ 실패: {result.get('error', 'Unknown error')}")

                # API 호출 제한 방지
                if i < len(emails):
                    time.sleep(delay)

            except Exception as e:
                print(f"❌ 오류: {e}")
                results.append({"error": str(e), "email_id": email_data.get('id', 'unknown')})

        return results

    def summarize_selected_emails(self, parser: 'NaverMailParser', email_ids: List[str],
                                  summary_type: str = "detailed",
                                  include_attachments: bool = True,
                                  only_attachments: bool = False) -> List[Dict]:
        """
        선택된 메일들만 요약 (NaverMailParser 직접 사용)

        Args:
            parser: NaverMailParser 인스턴스
            email_ids: 요약할 이메일 ID 리스트
            summary_type: 요약 타입
            include_attachments: 첨부파일 텍스트 포함 여부 (본문 + 첨부파일)
            only_attachments: True일 경우 첨부파일만 요약

        Returns:
            List[Dict]: 요약 결과 리스트
        """

        results = []

        for i, email_id in enumerate(email_ids, 1):
            print(f"[{i}/{len(email_ids)}] 메일 ID {email_id} 가져오는 중...")

            try:
                # 메일 내용 가져오기
                email_data = parser.view_email_content(email_id)

                if not email_data:
                    print(f"❌ 메일을 찾을 수 없습니다: {email_id}")
                    results.append({"error": "메일을 찾을 수 없음", "email_id": email_id})
                    continue

                # 요약
                result = self.summarize_email(email_data, summary_type, include_attachments, only_attachments)
                results.append(result)

                if 'summary' in result:
                    print(f"✅ 완료 (압축률: {result['compression_ratio']}%, 범위: {result.get('summary_scope', 'N/A')})")
                else:
                    print(f"❌ 실패: {result.get('error', 'Unknown error')}")

                # API 호출 제한 방지
                if i < len(email_ids):
                    time.sleep(1.0)

            except Exception as e:
                print(f"❌ 오류: {e}")
                results.append({"error": str(e), "email_id": email_id})

        return results

    def get_email_body_and_attachments_separately(self, parser: 'NaverMailParser', email_id: str) -> Dict:
        """
        NaverMailParser를 사용하여 메일의 본문과 첨부파일을 명확히 분리

        Args:
            parser: NaverMailParser 인스턴스
            email_id: 메일 ID

        Returns:
            Dict: {
                'email_id': str,
                'subject': str,
                'sender': str,
                'date': str,
                'body_text': str,  # 순수 본문
                'attachments': list  # 첨부파일 정보 리스트 (extracted_text 포함)
            }
        """

        try:
            # 메일 전체 데이터 가져오기
            email_data = parser.view_email_content(email_id)

            if not email_data:
                return {"error": f"메일을 찾을 수 없습니다: {email_id}"}

            # 본문과 첨부파일 텍스트 분리
            body_text = email_data.get('body', '')
            body_only = body_text
            attachments_with_text = []

            # 첨부파일 구분자로 분리
            if '=== 첨부파일:' in body_text:
                parts = body_text.split('\n\n=== 첨부파일:')
                body_only = parts[0].strip()

                # 각 첨부파일 텍스트 추출
                for idx, part in enumerate(parts[1:], 1):
                    # 파일명과 내용 분리
                    lines = part.split('\n', 1)
                    filename = lines[0].strip().replace('===', '').strip()
                    content = lines[1].strip() if len(lines) > 1 else ''

                    attachments_with_text.append({
                        'index': idx,
                        'filename': filename,
                        'extracted_text': content
                    })

            # 첨부파일 메타데이터 추가
            if 'attachments' in email_data:
                for i, att_meta in enumerate(email_data['attachments']):
                    if i < len(attachments_with_text):
                        attachments_with_text[i].update(att_meta)

            return {
                'email_id': email_id,
                'subject': email_data.get('subject', ''),
                'sender': email_data.get('sender', ''),
                'date': email_data.get('date', ''),
                'recipient': email_data.get('recipient', ''),
                'body_text': body_only,
                'attachments': attachments_with_text,
                'has_attachments': len(attachments_with_text) > 0
            }

        except Exception as e:
            return {"error": f"메일 분리 실패: {str(e)}"}

    def summarize_email_from_parser(self, parser: 'NaverMailParser', email_id: str,
                                    summary_type: str = "detailed",
                                    summarize_body: bool = True,
                                    summarize_attachments: bool = False) -> Dict:
        """
        NaverMailParser를 사용하여 메일 파싱 후 본문/첨부파일 선택 요약

        Args:
            parser: NaverMailParser 인스턴스
            email_id: 메일 ID
            summary_type: 요약 타입 (brief, detailed, bullet, korean)
            summarize_body: True일 경우 본문 요약
            summarize_attachments: True일 경우 첨부파일 요약

        Returns:
            Dict: 요약 결과
        """

        try:
            # 메일 파싱 - 본문과 첨부파일 분리
            print(f"메일 파싱 중 (ID: {email_id})...")
            separated_data = self.get_email_body_and_attachments_separately(parser, email_id)

            if 'error' in separated_data:
                return separated_data

            results = {
                'email_id': separated_data['email_id'],
                'subject': separated_data['subject'],
                'sender': separated_data['sender'],
                'date': separated_data['date'],
                'has_attachments': separated_data['has_attachments']
            }

            # 본문 요약
            if summarize_body and separated_data['body_text'].strip():
                print("📝 본문 요약 중...")
                body_content = f"제목: {results['subject']}\n발신자: {results['sender']}\n{'='*50}\n{separated_data['body_text']}"

                body_token_count = self.count_tokens(body_content)
                body_summary = self.summarize_chunk(body_content, summary_type)

                results['body_summary'] = body_summary
                results['body_original_length'] = len(separated_data['body_text'])
                results['body_tokens'] = body_token_count
                results['body_summary_tokens'] = self.count_tokens(body_summary)
                results['body_compression_ratio'] = round(self.count_tokens(body_summary) / body_token_count * 100, 2)
                print(f"✅ 본문 요약 완료 (압축률: {results['body_compression_ratio']}%)")
            else:
                results['body_summary'] = None

            # 첨부파일 요약
            if summarize_attachments and separated_data['attachments']:
                attachment_count = len(separated_data['attachments'])
                print(f"📎 첨부파일 요약 중 ({attachment_count}개)...")
                attachment_summaries = []

                for att in separated_data['attachments']:
                    idx = att['index']
                    filename = att['filename']
                    extracted_text = att.get('extracted_text', '')

                    if not extracted_text.strip():
                        print(f"  ⚠️  첨부파일 {idx} ({filename}): 추출된 텍스트 없음")
                        attachment_summaries.append({
                            'index': idx,
                            'filename': filename,
                            'summary': '[텍스트를 추출할 수 없는 파일입니다]',
                            'original_tokens': 0,
                            'summary_tokens': 0
                        })
                        continue

                    print(f"  📄 첨부파일 {idx}/{attachment_count} ({filename}) 요약 중...")
                    att_content = f"첨부파일: {filename}\n{'='*50}\n{extracted_text}"
                    att_token_count = self.count_tokens(att_content)
                    att_summary = self.summarize_chunk(att_content, summary_type)

                    attachment_summaries.append({
                        'index': idx,
                        'filename': filename,
                        'summary': att_summary,
                        'original_length': len(extracted_text),
                        'original_tokens': att_token_count,
                        'summary_tokens': self.count_tokens(att_summary),
                        'compression_ratio': round(self.count_tokens(att_summary) / att_token_count * 100, 2) if att_token_count > 0 else 0
                    })
                    print(f"  ✅ 완료 (압축률: {attachment_summaries[-1]['compression_ratio']}%)")
                    time.sleep(0.5)  # API 제한 방지

                results['attachment_summaries'] = attachment_summaries
                results['attachment_count'] = len(attachment_summaries)
                print(f"✅ 전체 첨부파일 요약 완료")
            else:
                results['attachment_summaries'] = []
                results['attachment_count'] = 0

            # 전체 통합 요약 생성
            if summarize_body and summarize_attachments and results.get('body_summary') and results.get('attachment_summaries'):
                print("🔄 통합 요약 생성 중...")
                combined_parts = []

                combined_parts.append(f"[본문 요약]\n{results['body_summary']}")

                for att_sum in results['attachment_summaries']:
                    if att_sum['summary'] != '[텍스트를 추출할 수 없는 파일입니다]':
                        combined_parts.append(f"[첨부파일: {att_sum['filename']}]\n{att_sum['summary']}")

                results['combined_summary'] = '\n\n'.join(combined_parts)
                print("✅ 통합 요약 완료")

            # 전체 통계
            total_original_tokens = results.get('body_tokens', 0)
            total_summary_tokens = results.get('body_summary_tokens', 0)

            if results.get('attachment_summaries'):
                for att in results['attachment_summaries']:
                    total_original_tokens += att.get('original_tokens', 0)
                    total_summary_tokens += att.get('summary_tokens', 0)

            results['total_original_tokens'] = total_original_tokens
            results['total_summary_tokens'] = total_summary_tokens
            results['total_compression_ratio'] = round(total_summary_tokens / total_original_tokens * 100, 2) if total_original_tokens > 0 else 0

            return results

        except Exception as e:
            return {"error": f"요약 실패: {str(e)}"}

    def summarize_multiple_emails_from_parser(self, parser: 'NaverMailParser',
                                              criteria: str = 'ALL',
                                              limit: int = 5,
                                              summary_type: str = "detailed",
                                              summarize_body: bool = True,
                                              summarize_attachments: bool = False) -> List[Dict]:
        """
        NaverMailParser로 여러 메일 파싱 후 선택 요약

        Args:
            parser: NaverMailParser 인스턴스
            criteria: 검색 기준 ('ALL', 'UNSEEN', 'SEEN' 등)
            limit: 가져올 메일 개수
            summary_type: 요약 타입
            summarize_body: 본문 요약 여부
            summarize_attachments: 첨부파일 요약 여부

        Returns:
            List[Dict]: 요약 결과 리스트
        """

        try:
            # 메일 검색
            print(f"메일 검색 중 (기준: {criteria}, 개수: {limit})...")
            email_ids = parser.search_emails(criteria=criteria, limit=limit)

            if not email_ids:
                return []

            print(f"{len(email_ids)}개 메일 발견")

            results = []
            for i, email_id in enumerate(email_ids, 1):
                email_id_str = email_id.decode() if isinstance(email_id, bytes) else str(email_id)
                print(f"\n[{i}/{len(email_ids)}] 메일 처리 중 (ID: {email_id_str})...")

                result = self.summarize_email_from_parser(
                    parser,
                    email_id_str,
                    summary_type,
                    summarize_body,
                    summarize_attachments
                )

                results.append(result)

                # API 호출 제한 방지
                if i < len(email_ids):
                    time.sleep(1.0)

            return results

        except Exception as e:
            print(f"❌ 오류: {e}")
            return [{"error": str(e)}]
    
    def summarize_downloaded_attachment(self, attachment_path: str, summary_type: str = "detailed") -> Dict:
        """
        NaverMailParser로 다운로드 받은 첨부파일을 파싱하고 요약

        Args:
            attachment_path: 첨부파일 경로
            summary_type: 요약 타입 (brief, detailed, bullet, korean)

        Returns:
            Dict: 요약 결과
        """
        try:
            # NaverMailParser의 extract_text_from_file 사용
            parser = NaverMailParser(username="dummy", password="dummy")

            print(f"📄 첨부파일 텍스트 추출 중: {Path(attachment_path).name}")
            extracted_text = parser.extract_text_from_file(attachment_path)

            # 추출 실패 확인
            if extracted_text.startswith('[') and '실패' in extracted_text or '지원하지 않습니다' in extracted_text:
                return {
                    'file_path': attachment_path,
                    'filename': Path(attachment_path).name,
                    'error': extracted_text
                }

            # 토큰 수 계산
            token_count = self.count_tokens(extracted_text)
            print(f"📊 추출된 텍스트 토큰 수: {token_count:,}")

            # 텍스트가 너무 긴 경우 분할
            if token_count > self.max_tokens - 1000:
                print("텍스트가 길어 청크로 분할합니다...")
                chunks = self.split_text_by_tokens(extracted_text, max_chunk_tokens=3000)

                summaries = []
                for i, chunk in enumerate(chunks, 1):
                    print(f"청크 {i}/{len(chunks)} 요약 중...")
                    summary = self.summarize_chunk(chunk, summary_type)
                    summaries.append(summary)
                    time.sleep(1)

                combined_summary = "\n\n".join(summaries)
                if self.count_tokens(combined_summary) > 3000:
                    final_summary = self.summarize_chunk(combined_summary, summary_type)
                else:
                    final_summary = combined_summary
            else:
                print("단일 요약 생성 중...")
                final_summary = self.summarize_chunk(extracted_text, summary_type)

            # 결과 반환
            result = {
                'file_path': attachment_path,
                'filename': Path(attachment_path).name,
                'file_size': os.path.getsize(attachment_path),
                'extracted_text_length': len(extracted_text),
                'original_tokens': token_count,
                'summary': final_summary,
                'summary_tokens': self.count_tokens(final_summary),
                'compression_ratio': round(self.count_tokens(final_summary) / token_count * 100, 2) if token_count > 0 else 0,
                'summary_type': summary_type
            }

            print(f"✅ 요약 완료 (압축률: {result['compression_ratio']}%)")
            return result

        except Exception as e:
            return {
                'file_path': attachment_path,
                'filename': Path(attachment_path).name,
                'error': f"첨부파일 요약 실패: {str(e)}"
            }

    def summarize_email_attachments_from_path(self, email_folder_path: str, summary_type: str = "detailed") -> Dict:
        """
        NaverMailParser로 다운로드된 이메일 폴더의 모든 첨부파일을 파싱하고 요약

        Args:
            email_folder_path: 이메일 다운로드 폴더 경로 (예: downloads/email_123)
            summary_type: 요약 타입 (brief, detailed, bullet, korean)

        Returns:
            Dict: 전체 요약 결과
        """
        try:
            email_folder = Path(email_folder_path)

            if not email_folder.exists():
                return {'error': f'폴더를 찾을 수 없습니다: {email_folder_path}'}

            # 메타데이터 읽기
            metadata_file = email_folder / 'metadata.json'
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

            # 본문 읽기
            body_text = ""
            text_file = email_folder / 'body.txt'
            if text_file.exists():
                with open(text_file, 'r', encoding='utf-8') as f:
                    body_text = f.read()

            # 첨부파일 찾기 (body.txt, body.html, metadata.json 제외)
            attachments = []
            for file in email_folder.iterdir():
                if file.name not in ['body.txt', 'body.html', 'metadata.json'] and file.is_file():
                    attachments.append(file)

            if not attachments:
                return {
                    'email_id': metadata.get('id', 'unknown'),
                    'subject': metadata.get('subject', ''),
                    'attachment_count': 0,
                    'message': '첨부파일이 없습니다'
                }

            print(f"📧 이메일 폴더: {email_folder.name}")
            print(f"📎 첨부파일 {len(attachments)}개 발견")

            # 각 첨부파일 요약
            attachment_summaries = []
            for i, att_path in enumerate(attachments, 1):
                print(f"\n[{i}/{len(attachments)}] {att_path.name} 처리 중...")

                result = self.summarize_downloaded_attachment(str(att_path), summary_type)
                attachment_summaries.append(result)

                if i < len(attachments):
                    time.sleep(0.5)  # API 제한 방지

            # 전체 결과
            total_original_tokens = sum(r.get('original_tokens', 0) for r in attachment_summaries if 'error' not in r)
            total_summary_tokens = sum(r.get('summary_tokens', 0) for r in attachment_summaries if 'error' not in r)

            return {
                'email_id': metadata.get('id', 'unknown'),
                'subject': metadata.get('subject', ''),
                'sender': metadata.get('sender', ''),
                'date': metadata.get('date', ''),
                'folder_path': str(email_folder),
                'attachment_count': len(attachments),
                'attachment_summaries': attachment_summaries,
                'total_original_tokens': total_original_tokens,
                'total_summary_tokens': total_summary_tokens,
                'total_compression_ratio': round(total_summary_tokens / total_original_tokens * 100, 2) if total_original_tokens > 0 else 0,
                'summary_type': summary_type
            }

        except Exception as e:
            return {'error': f'이메일 첨부파일 요약 실패: {str(e)}'}

    def batch_summarize(self, input_dir: str, output_dir: str = None,
                       summary_type: str = "detailed", file_pattern: str = "*.txt"):
        """디렉토리 내 모든 텍스트 파일 일괄 요약"""
        input_path = Path(input_dir)
        output_path = Path(output_dir) if output_dir else input_path / "summaries"
        output_path.mkdir(exist_ok=True)

        txt_files = list(input_path.glob(file_pattern))

        if not txt_files:
            print(f"{input_dir}에서 {file_pattern} 파일을 찾을 수 없습니다.")
            return

        print(f"{len(txt_files)}개 파일 요약을 시작합니다...")

        results = []
        for i, file_path in enumerate(txt_files, 1):
            print(f"\n[{i}/{len(txt_files)}] {file_path.name} 요약 중...")

            output_file = output_path / f"{file_path.stem}_summary.txt"
            result = self.summarize_file(str(file_path), summary_type, str(output_file))

            if "error" not in result:
                print(f"✅ 완료: {output_file}")
                results.append(result)
            else:
                print(f"❌ 실패: {result['error']}")

        # 전체 결과 요약 저장
        summary_report = output_path / "batch_summary_report.json"
        with open(summary_report, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n일괄 요약 완료! 결과: {output_path}")

def main():
    """사용 예시"""
    import argparse
    
    parser = argparse.ArgumentParser(description='텍스트 파일 LLM 요약기')
    parser.add_argument('file_path', help='요약할 텍스트 파일 경로')
    parser.add_argument('--output', '-o', help='출력 파일 경로')
    parser.add_argument('--type', '-t', choices=['brief', 'detailed', 'bullet', 'korean'], 
                       default='detailed', help='요약 타입')
    parser.add_argument('--model', '-m', default='gpt-3.5-turbo', help='사용할 모델')
    parser.add_argument('--batch', '-b', help='디렉토리 일괄 처리')
    
    args = parser.parse_args()
    
    # API 키 확인
    if not os.getenv('OPENAI_API_KEY'):
        print("환경변수 OPENAI_API_KEY를 설정해주세요.")
        print("예: export OPENAI_API_KEY='your-api-key-here'")
        return
    
    summarizer = TextSummarizer(model=args.model)
    
    try:
        if args.batch:
            # 일괄 처리
            summarizer.batch_summarize(args.batch, summary_type=args.type)
        else:
            # 단일 파일 처리
            result = summarizer.summarize_file(args.file_path, args.type, args.output)
            
            if "error" in result:
                print(f"❌ {result['error']}")
            else:
                print(f"\n✅ 요약 완료!")
                print(f"압축률: {result['compression_ratio']}%")
                print(f"원본: {result['original_tokens']:,} 토큰 → 요약: {result['summary_tokens']:,} 토큰")
                print("\n" + "="*50)
                print(result['summary'])
                
                if args.output:
                    print(f"\n📁 결과 저장: {args.output}")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    # 직접 실행 예시
    # summarizer = TextSummarizer()
    # result = summarizer.summarize_file("example.txt", "korean", "summary.txt")
    # print(result)
    
    main()