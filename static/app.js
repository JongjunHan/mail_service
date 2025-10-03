// 네이버 메일 통합 웹 서비스 JavaScript (회신 기능 포함)

let currentEmailId = null;
let currentEmailData = null;

// 로그인 처리
async function handleLogin(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const openaiKey = document.getElementById('openaiKey').value;

    showLoading(true);

    try {
        const response = await fetch('/api/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, openai_key: openaiKey })
        });

        const result = await response.json();

        if (result.success) {
            showToast('연결 성공', 'success');
            document.getElementById('loginSection').style.display = 'none';
            document.getElementById('mainSection').style.display = 'grid';
            document.getElementById('headerActions').style.display = 'flex';
            document.getElementById('userInfo').textContent = username;
        } else {
            showToast('연결 실패: ' + result.error, 'error');
        }
    } catch (error) {
        showToast('오류: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// 메일 목록 조회
async function fetchEmails() {
    const mailbox = document.getElementById('mailboxSelect').value;
    const criteria = document.getElementById('mailFilter').value;
    const limit = document.getElementById('mailLimit').value;

    showLoading(true);

    // 현재 선택된 메일 초기화 (재조회 시)
    currentEmailId = null;
    currentEmailData = null;
    document.getElementById('summarizeBtn').disabled = true;
    document.getElementById('replyBtn').style.display = 'none';

    try {
        const response = await fetch('/api/fetch_emails', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mailbox, criteria, limit })
        });

        const result = await response.json();

        if (result.success) {
            renderEmailList(result.emails);
            showToast(`${result.count}개 메일 조회 완료`, 'success');

            // 메일 상세 패널 초기화
            document.getElementById('emailDetail').innerHTML = '<div class="empty-state"><p>메일을 선택하면 내용이 표시됩니다</p></div>';
            // 요약 패널 초기화
            document.getElementById('summaryContent').innerHTML = '<div class="empty-state"><p>메일을 선택하고 요약 버튼을 누르세요</p></div>';
        } else {
            showToast('조회 실패: ' + result.error, 'error');
        }
    } catch (error) {
        showToast('오류: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// 메일 목록 렌더링
function renderEmailList(emails) {
    const container = document.getElementById('emailList');

    if (emails.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>조회된 메일이 없습니다</p></div>';
        return;
    }

    container.innerHTML = emails.map(email => `
        <div class="email-item" onclick="selectEmail('${email.id}')">
            <div class="email-subject">${escapeHtml(email.subject)}</div>
            <div class="email-sender">${escapeHtml(email.sender)}</div>
            <div class="email-preview">${escapeHtml(email.body_preview)}</div>
            <div class="email-meta">
                <span class="email-date">${formatDate(email.date)}</span>
                ${email.has_attachments ? '<span class="badge">첨부 ' + email.attachment_count + '개</span>' : ''}
            </div>
        </div>
    `).join('');
}

// 메일 선택
async function selectEmail(emailId) {
    document.querySelectorAll('.email-item').forEach(item => {
        item.classList.remove('selected');
    });
    event.currentTarget.classList.add('selected');

    currentEmailId = emailId;
    showLoading(true);

    try {
        const response = await fetch('/api/get_email_detail', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email_id: emailId })
        });

        const result = await response.json();

        if (result.success) {
            currentEmailData = result.email;
            renderEmailDetail(result.email);
            document.getElementById('summarizeBtn').disabled = false;
            document.getElementById('replyBtn').style.display = 'block';
        } else {
            showToast('상세 조회 실패: ' + result.error, 'error');
        }
    } catch (error) {
        showToast('오류: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// 메일 상세 렌더링
function renderEmailDetail(email) {
    const container = document.getElementById('emailDetail');

    let html = `
        <div class="detail-header">
            <div class="detail-subject">${escapeHtml(email.subject)}</div>
            <div class="detail-info">
                <div class="info-row">
                    <span class="info-label">발신자</span>
                    <span>${escapeHtml(email.sender)}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">수신자</span>
                    <span>${escapeHtml(email.recipient || '-')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">날짜</span>
                    <span>${formatDate(email.date)}</span>
                </div>
            </div>
        </div>
    `;

    // 본문
    if (email.body_text) {
        html += `
            <div class="body-section">
                <div class="body-section-title">본문</div>
                <div class="body-text">${escapeHtml(email.body_text)}</div>
            </div>
        `;
    }

    // 첨부파일
    if (email.attachments && email.attachments.length > 0) {
        html += `
            <div class="body-section">
                <div class="body-section-title">첨부파일 (${email.attachments.length}개)</div>
                <div class="attachment-list">
        `;

        email.attachments.forEach(att => {
            html += `
                <div class="attachment-item">
                    <div class="attachment-header">
                        <strong>${escapeHtml(att.filename)}</strong>
                        <div class="attachment-actions">
                            <button class="btn-download" onclick="downloadAttachment('${currentEmailId}', '${escapeHtml(att.filename)}')">다운로드</button>
                            <button class="btn-summarize" onclick="summarizeAttachment('${currentEmailId}', '${escapeHtml(att.filename)}')">요약</button>
                        </div>
                    </div>
                    ${att.extracted_text ? '<div class="attachment-text">' + escapeHtml(att.extracted_text.substring(0, 500)) + '...</div>' : ''}
                </div>
            `;
        });

        html += '</div></div>';
    }

    container.innerHTML = html;
}

// 첨부파일 다운로드
async function downloadAttachment(emailId, filename) {
    showLoading(true);

    try {
        const response = await fetch('/api/download_attachment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email_id: emailId,
                filename: filename
            })
        });

        if (response.ok) {
            // Blob으로 변환하여 다운로드
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showToast('다운로드 완료', 'success');
        } else {
            const result = await response.json();
            showToast('다운로드 실패: ' + result.error, 'error');
        }
    } catch (error) {
        showToast('오류: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// 첨부파일 요약
async function summarizeAttachment(emailId, filename) {
    showLoading(true);

    try {
        const summaryType = document.getElementById('summaryType').value;
        const model = document.getElementById('modelSelect').value;

        const response = await fetch('/api/summarize_attachment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email_id: emailId,
                filename: filename,
                summary_type: summaryType,
                model: model
            })
        });

        const result = await response.json();

        if (result.success) {
            // 요약 결과를 요약 패널에 표시
            renderAttachmentSummary(result.summary, filename);
            showToast('첨부파일 요약 완료', 'success');
        } else {
            showToast('요약 실패: ' + result.error, 'error');
        }
    } catch (error) {
        showToast('오류: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// 첨부파일 요약 결과 렌더링
function renderAttachmentSummary(summary, filename) {
    const container = document.getElementById('summaryContent');

    let html = `
        <div class="summary-section">
            <div class="summary-section-title">첨부파일 요약: ${escapeHtml(filename)}</div>
            <div class="summary-text">${escapeHtml(summary.summary || '요약 내용 없음')}</div>
        </div>
    `;

    // 통계 정보
    if (summary.original_tokens) {
        html += `
            <div class="summary-stats">
                <div class="stat-item">
                    <div class="stat-label">원본 토큰</div>
                    <div class="stat-value">${(summary.original_tokens || 0).toLocaleString()}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">요약 토큰</div>
                    <div class="stat-value">${(summary.summary_tokens || 0).toLocaleString()}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">압축률</div>
                    <div class="stat-value">${summary.compression_ratio || 0}%</div>
                </div>
            </div>
        `;
    }

    container.innerHTML = html;
}

// 메일 요약
async function summarizeEmail() {
    if (!currentEmailId) {
        showToast('메일을 먼저 선택하세요', 'error');
        return;
    }

    const summaryType = document.getElementById('summaryType').value;
    const summarizeBody = document.getElementById('summarizeBody').checked;
    const summarizeAttachments = document.getElementById('summarizeAttachments').checked;
    const model = document.getElementById('modelSelect').value;

    if (!summarizeBody && !summarizeAttachments) {
        showToast('최소 하나 이상 선택하세요', 'error');
        return;
    }

    showLoading(true);

    try {
        const response = await fetch('/api/summarize_email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email_id: currentEmailId,
                summary_type: summaryType,
                summarize_body: summarizeBody,
                summarize_attachments: summarizeAttachments,
                model: model
            })
        });

        const result = await response.json();

        if (result.success) {
            renderSummary(result.summary);
            showToast('요약 완료', 'success');
        } else {
            showToast('요약 실패: ' + result.error, 'error');
        }
    } catch (error) {
        showToast('오류: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// 요약 결과 렌더링
function renderSummary(summary) {
    const container = document.getElementById('summaryContent');
    let html = '';

    // 본문 요약
    if (summary.body_summary) {
        html += `
            <div class="summary-section">
                <div class="summary-section-title">본문 요약</div>
                <div class="summary-text">${escapeHtml(summary.body_summary)}</div>
            </div>
        `;
    }

    // 첨부파일 요약
    if (summary.attachment_summaries && summary.attachment_summaries.length > 0) {
        summary.attachment_summaries.forEach(att => {
            html += `
                <div class="summary-section">
                    <div class="summary-section-title">첨부: ${escapeHtml(att.filename)}</div>
                    <div class="summary-text">${escapeHtml(att.summary)}</div>
                </div>
            `;
        });
    }

    // 통합 요약
    if (summary.combined_summary) {
        html += `
            <div class="summary-section">
                <div class="summary-section-title">통합 요약</div>
                <div class="summary-text">${escapeHtml(summary.combined_summary)}</div>
            </div>
        `;
    }

    // 통계
    html += `
        <div class="summary-stats">
            <div class="stat-item">
                <div class="stat-label">원본 토큰</div>
                <div class="stat-value">${(summary.total_original_tokens || 0).toLocaleString()}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">요약 토큰</div>
                <div class="stat-value">${(summary.total_summary_tokens || 0).toLocaleString()}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">압축률</div>
                <div class="stat-value">${summary.total_compression_ratio || 0}%</div>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

// 회신 모달 열기
function openReplyModal() {
    if (!currentEmailData) {
        showToast('메일을 먼저 선택하세요', 'error');
        return;
    }

    // 발신자 이메일 추출
    const senderEmail = extractEmail(currentEmailData.sender);

    // 회신 제목 생성 (Re: 접두사)
    let replySubject = currentEmailData.subject;
    if (!replySubject.toLowerCase().startsWith('re:')) {
        replySubject = 'Re: ' + replySubject;
    }

    // 원본 메일 인용
    const originalBody = `\n\n--- 원본 메일 ---\n발신자: ${currentEmailData.sender}\n날짜: ${currentEmailData.date}\n제목: ${currentEmailData.subject}\n\n${currentEmailData.body_text || ''}`;

    // 모달 필드 설정
    document.getElementById('replyTo').value = senderEmail;
    document.getElementById('replySubject').value = replySubject;
    document.getElementById('replyBody').value = originalBody;

    // 모달 표시
    document.getElementById('replyModal').classList.add('active');
}

// 회신 모달 닫기
function closeReplyModal() {
    document.getElementById('replyModal').classList.remove('active');
    document.getElementById('replyForm').reset();
}

// 회신 전송
async function sendReply(event) {
    event.preventDefault();

    const toEmail = document.getElementById('replyTo').value;
    const subject = document.getElementById('replySubject').value;
    const body = document.getElementById('replyBody').value;

    showLoading(true);

    try {
        const response = await fetch('/api/reply_email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                to_email: toEmail,
                subject: subject,
                body: body
            })
        });

        const result = await response.json();

        if (result.success) {
            showToast('회신 전송 완료', 'success');
            closeReplyModal();
        } else {
            showToast('회신 실패: ' + result.error, 'error');
        }
    } catch (error) {
        showToast('오류: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// 로그아웃
async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        location.reload();
    } catch (error) {
        showToast('로그아웃 오류: ' + error.message, 'error');
    }
}

// 유틸리티 함수
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast show ' + type;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '-';
    try {
        const date = new Date(dateString);
        return date.toLocaleString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return dateString;
    }
}

function extractEmail(emailString) {
    if (!emailString) return '';

    // 이메일 주소 추출 (예: "이름 <email@example.com>" -> "email@example.com")
    const match = emailString.match(/<(.+?)>/);
    if (match) {
        return match[1];
    }

    // 이메일 형식인지 확인
    if (emailString.includes('@')) {
        return emailString.trim();
    }

    return emailString;
}