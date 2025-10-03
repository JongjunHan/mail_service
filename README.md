# 네이버 메일 통합 웹 서비스

Flask 기반의 네이버 메일 관리 웹 애플리케이션입니다. 메일 조회, 본문/첨부파일 요약, 첨부파일 다운로드, 회신 기능을 제공합니다.

## 주요 기능

### 1. 메일박스 선택 및 조회
- **메일박스 선택**:
  - 받은편지함 (INBOX)
  - 보낸편지함 (INBOX/Sent)
  - 휴지통 (INBOX/Trash)
  - 스팸함 (INBOX/Spam)
- **메일 필터링**:
  - 전체 메일: 선택한 메일박스의 모든 메일
  - 안읽은 메일: 읽지 않은 메일만
  - 읽은 메일: 읽은 메일만
- 조회 개수 설정 (1~100개)
- 메일 목록 실시간 조회

### 2. 메일 상세 보기
- 발신자, 수신자, 날짜 정보
- 본문 텍스트 표시
- 첨부파일 목록 및 추출된 텍스트 미리보기
- **첨부파일 다운로드**: 각 첨부파일을 로컬로 다운로드 가능

### 3. 메일 요약 (OpenAI API)
#### 본문 요약
- 메일 본문 내용을 선택적으로 요약
- 체크박스로 본문 요약 여부 선택

#### 첨부파일 요약
- PDF, Word, Excel, PowerPoint 파일 내용 자동 추출 및 요약
- 체크박스로 첨부파일 요약 여부 선택
- 각 첨부파일별 개별 요약 제공

#### 요약 타입 선택
- **간단**: 핵심만 간략하게 요약
- **상세**: 자세한 요약 제공
- **목록**: 불릿 포인트 형식
- **한국어**: 한국어 최적화 요약

#### LLM 모델 선택
- **GPT-4o Mini** (기본, 빠르고 경제적)
- **GPT-4o** (최신 모델)
- **GPT-4 Turbo** (향상된 성능)
- **GPT-4** (고성능)
- **GPT-3.5 Turbo** (빠른 응답)

#### 요약 통계
- 원본 토큰 수
- 요약 토큰 수
- 압축률 표시

### 4. 메일 회신
- 선택한 메일에 대한 회신 작성
- 원본 메일 자동 인용
- Re: 접두사 자동 추가
- 발신자 이메일 자동 입력
- SMTP를 통한 메일 전송

### 5. 첨부파일 관리 및 요약
- **자동 다운로드**: 메일 조회 시 첨부파일 자동 다운로드 및 저장
- **텍스트 추출**: PDF, Word, Excel, PPT 파일의 텍스트 자동 추출
- **다운로드 기능**: 웹 UI에서 첨부파일을 로컬로 다운로드
- **개별 첨부파일 요약**: 다운로드된 첨부파일을 선택하여 개별 요약 가능
  - 각 첨부파일마다 "요약" 버튼 제공
  - 선택한 LLM 모델과 요약 타입으로 요약
  - 요약 결과 및 통계 표시
- **지원 형식**:
  - PDF (.pdf)
  - Word (.docx, .doc)
  - Excel (.xlsx, .xls)
  - PowerPoint (.pptx, .ppt)
  - 텍스트 (.txt, .csv, .log, .md, .json, .xml, .html)

## 시스템 요구사항

- Python 3.8 이상
- 네이버 메일 계정
- OpenAI API 키 (요약 기능 사용 시)

## 설치 방법

### 1. 의존성 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 네이버 메일 앱 비밀번호 발급

1. 네이버 로그인 후 [https://nid.naver.com/user2/help/myInfo?lang=ko_KR](https://nid.naver.com/user2/help/myInfo?lang=ko_KR) 접속
2. 보안 설정 → 앱 비밀번호 관리
3. 새 앱 비밀번호 발급 (IMAP/SMTP 용)
4. 발급받은 비밀번호 저장 (재확인 불가)

### 3. OpenAI API 키 발급 (선택사항)

1. [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys) 접속
2. Create new secret key 클릭
3. API 키 복사 및 보관

## 실행 방법

### 서비스 시작

```bash
python app.py
```

또는

```bash
python3 app.py
```

### 웹 브라우저 접속

서비스 시작 후 브라우저에서 다음 주소로 접속:

```
http://localhost:5000
```

또는 같은 네트워크의 다른 기기에서:

```
http://[서버IP]:5000
```

## 사용 방법

### 1. 로그인
1. **네이버 아이디** 입력 (예: example@naver.com)
2. **앱 비밀번호** 입력 (네이버 계정 비밀번호가 아님!)
3. **OpenAI API 키** 입력 (요약 기능 사용 시, 선택사항)
4. "연결하기" 버튼 클릭

### 2. 메일 조회
1. **메일박스 선택**:
   - 받은편지함: 받은 메일
   - 보낸편지함: 보낸 메일
   - 휴지통: 삭제된 메일
   - 스팸함: 스팸 메일
2. **필터 선택**:
   - 전체 메일: 모든 메일 조회
   - 안읽은 메일: 읽지 않은 메일만
   - 읽은 메일: 읽은 메일만
3. **조회 개수** 입력 (1~100)
4. "조회" 버튼 클릭
5. 왼쪽 패널에 메일 목록 표시

### 3. 메일 상세 보기
1. 메일 목록에서 원하는 메일 클릭
2. 가운데 패널에 상세 내용 표시:
   - 발신자, 수신자, 날짜
   - 본문 내용
   - 첨부파일 목록 (있는 경우)

### 4. 첨부파일 다운로드 및 요약
1. 메일 상세 화면에서 첨부파일 목록 확인
2. **다운로드**: 각 첨부파일 옆의 "다운로드" 버튼 클릭
   - 브라우저 다운로드 폴더에 파일 저장
3. **개별 첨부파일 요약**: "요약" 버튼 클릭
   - 현재 선택된 요약 타입과 LLM 모델 사용
   - 첨부파일 내용만 개별적으로 요약
   - 요약 결과가 오른쪽 요약 패널에 표시됨

### 5. 메일 요약
1. 메일 선택 후 오른쪽 요약 패널에서 옵션 선택:
   - **본문 체크박스**: 메일 본문 요약 여부
   - **첨부파일 체크박스**: 첨부파일 요약 여부
   - **요약 타입**: 간단/상세/목록/한국어 중 선택
   - **LLM 모델**: 사용할 GPT 모델 선택
2. "요약" 버튼 클릭
3. 요약 결과 및 통계 확인:
   - 본문 요약 (선택한 경우)
   - 첨부파일별 요약 (선택한 경우)
   - 통합 요약 (본문+첨부파일 모두 선택한 경우)
   - 토큰 통계 및 압축률

### 6. 메일 회신
1. 메일 선택 후 "회신" 버튼 클릭
2. 회신 모달 창에서:
   - **받는사람**: 자동으로 발신자 이메일 입력됨
   - **제목**: "Re:" 접두사가 자동으로 추가됨
   - **본문**: 원본 메일이 자동으로 인용됨
3. 회신 내용 작성
4. "전송" 버튼 클릭

### 7. 로그아웃
- 우측 상단의 "로그아웃" 버튼 클릭
- 연결이 종료되고 로그인 화면으로 이동

## 프로젝트 구조

```
claude-test/
├── app.py                         # Flask 웹 서버
├── lib/                           # 핵심 라이브러리
│   ├── __init__.py               # 패키지 초기화
│   ├── naver_mail_parser.py      # IMAP 메일 파싱 및 첨부파일 처리
│   ├── naver_smtp_sender.py      # SMTP 메일 발송
│   ├── text_summarizer.py        # OpenAI 요약 (첨부파일 파싱 포함)
│   └── naver_mail_suite.py       # 통합 인터페이스
├── templates/
│   └── index.html                # 메인 웹 페이지
├── static/
│   ├── style.css                 # 스타일시트
│   └── app.js                    # 프론트엔드 로직
├── downloads/                    # 첨부파일 다운로드 폴더 (자동 생성)
├── requirements.txt              # 의존성 패키지
└── README.md                     # 이 파일
```

## API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/` | GET | 메인 페이지 |
| `/api/connect` | POST | 메일 서버 연결 |
| `/api/select_mailbox` | POST | 메일박스 선택 |
| `/api/fetch_emails` | POST | 메일 목록 조회 |
| `/api/get_email_detail` | POST | 메일 상세 조회 |
| `/api/summarize_email` | POST | 메일 요약 (본문+첨부파일) |
| `/api/summarize_attachment` | POST | 개별 첨부파일 요약 |
| `/api/reply_email` | POST | 메일 회신 전송 |
| `/api/download_attachment` | POST | 첨부파일 다운로드 |
| `/api/logout` | POST | 로그아웃 |

## 기술 스택

### 백엔드
- **Python 3.8+**
- **Flask 3.0+**: 웹 프레임워크
- **OpenAI API 1.0+**: LLM 요약
- **imaplib**: IMAP 프로토콜 (메일 수신)
- **smtplib**: SMTP 프로토콜 (메일 발송)

### 프론트엔드
- **HTML5**
- **CSS3** (Custom Variables)
- **Vanilla JavaScript** (ES6+)
- **Fetch API**: 비동기 통신

### 라이브러리
- **python-docx**: Word 파일 처리
- **openpyxl**: Excel 파일 처리
- **PyPDF2**: PDF 파일 처리
- **python-pptx**: PowerPoint 파일 처리
- **BeautifulSoup4**: HTML 파싱
- **tiktoken**: 토큰 계산

## 보안 주의사항

### 1. 앱 비밀번호 관리
- 앱 비밀번호는 네이버 계정 비밀번호가 **아닙니다**
- 외부에 노출되지 않도록 주의하세요
- 정기적으로 비밀번호를 변경하세요

### 2. OpenAI API 키 관리
- API 키는 절대 공개 저장소에 커밋하지 마세요
- 사용량 제한 및 모니터링을 설정하세요
- `.env` 파일 사용을 권장합니다

### 3. HTTPS 사용 권장
- 프로덕션 환경에서는 반드시 HTTPS를 사용하세요
- 리버스 프록시 (nginx, Apache) 설정 권장
- Let's Encrypt로 무료 SSL 인증서 발급 가능

### 4. 방화벽 설정
- 필요한 포트만 개방:
  - 993 (IMAP SSL)
  - 587 (SMTP TLS)
  - 5000 (Flask 개발 서버, 프로덕션은 변경 권장)

## 문제 해결

### 메일 서버 연결 실패
**증상**: "메일 서버 연결 실패" 오류 메시지

**해결 방법**:
1. 네이버 앱 비밀번호가 올바른지 확인
2. 네이버 계정의 IMAP/SMTP 설정 활성화 확인
3. 방화벽에서 포트 993(IMAP), 587(SMTP) 허용 확인
4. 인터넷 연결 상태 확인

### 요약 기능 오류
**증상**: "OpenAI API 키가 설정되지 않았습니다" 또는 요약 실패

**해결 방법**:
1. OpenAI API 키가 유효한지 확인
2. API 사용량 한도 확인 (https://platform.openai.com/usage)
3. 인터넷 연결 상태 확인
4. OpenAI API 서비스 상태 확인

### 회신 전송 실패
**증상**: "회신 전송 실패" 오류 메시지

**해결 방법**:
1. SMTP 서버 연결 상태 확인
2. 받는사람 이메일 주소 형식 확인
3. 네이버 앱 비밀번호 재확인
4. 네이버 SMTP 일일 발송 제한 확인

### 첨부파일 다운로드 실패
**증상**: 다운로드 버튼 클릭 시 오류

**해결 방법**:
1. 메일을 먼저 조회했는지 확인 (첨부파일 다운로드 필요)
2. `downloads/` 폴더 권한 확인
3. 디스크 공간 확인
4. 브라우저 다운로드 설정 확인

### 첨부파일 텍스트 추출 실패
**증상**: 첨부파일 요약 시 "텍스트를 추출할 수 없는 파일입니다"

**해결 방법**:
1. 파일 형식이 지원되는지 확인 (PDF, Word, Excel, PPT, 텍스트)
2. 파일이 암호화되지 않았는지 확인
3. 파일이 손상되지 않았는지 확인
4. 필요한 라이브러리가 설치되어 있는지 확인:
   ```bash
   pip install PyPDF2 python-docx openpyxl python-pptx
   ```

## 성능 최적화

### 메일 조회 최적화
- 한 번에 너무 많은 메일을 조회하지 마세요 (권장: 10~20개)
- `download_full=True` 옵션은 필요할 때만 사용

### 요약 최적화
- 긴 메일은 요약 시간이 오래 걸릴 수 있습니다
- GPT-4o Mini 모델이 가장 빠르고 경제적입니다
- 첨부파일 요약은 선택적으로 사용

### 네트워크 최적화
- 안정적인 네트워크 환경에서 사용
- VPN 사용 시 성능 저하 가능

## 개발 환경 설정

### 개발 모드 실행
```bash
export FLASK_ENV=development
python app.py
```

### 디버그 모드
`app.py` 파일에서 `debug=True` 설정

### 환경 변수 사용
```bash
# .env 파일 생성
NAVER_USERNAME=your_id@naver.com
NAVER_PASSWORD=your_app_password
OPENAI_API_KEY=your_openai_key

# 환경 변수 로드
python-dotenv 설치 후 app.py에서 로드
```

## 프로덕션 배포

### WSGI 서버 사용 (Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Nginx 리버스 프록시 설정
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### systemd 서비스 등록
```ini
[Unit]
Description=Naver Mail Suite
After=network.target

[Service]
User=your-user
WorkingDirectory=/path/to/claude-test
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

## 라이선스

이 프로젝트는 개인 사용 목적으로 제작되었습니다.

## 기여

이슈 및 풀 리퀘스트를 환영합니다.

## 연락처

문의사항이 있으시면 이슈를 등록해주세요.

## 업데이트 내역

### v2.3.0 (2025-10-02)
- **메일박스 선택 기능 추가**: 받은편지함, 보낸편지함, 휴지통, 스팸함
- **개별 첨부파일 요약 기능**: 각 첨부파일마다 개별 요약 버튼 제공
- 첨부파일 다운로드 기능
- 다운로드된 첨부파일 직접 파싱 및 요약
- LLM 모델 선택 기능 (GPT-4o Mini, GPT-4o, GPT-4 Turbo, GPT-4, GPT-3.5 Turbo)
- 메일 회신 기능
- OpenAI API 1.0.0+ 지원
- 첨부파일 텍스트 추출 (PDF, Word, Excel, PPT)

### v2.1.0
- 본문/첨부파일 선택적 요약 기능 추가
- 통합 요약 기능 추가

### v2.0.0
- Flask 웹 UI 초기 버전
- 메일 조회, 상세보기, 요약 기능
- 네이버 IMAP/SMTP 통합

### v1.0.0
- CLI 버전 초기 릴리즈
