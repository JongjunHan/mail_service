// 네이버 메일 웹 서비스 JavaScript v2.0
// 첨부파일 텍스트 추출 및 선택적 요약 기능 포함

let connected = false;
let currentEmailId = null;

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeEventHandlers();
    checkStatus();
});

// 탭 초기화
function initializeTabs() {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;
            switchTab(targetTab);
        });
    });
}

// 탭 전환
function switchTab(targetTab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    document.querySelector(`[data-tab="${targetTab}"]`).classList.add('active');
    document.getElementById(targetTab).classList.add('active');
}

// 이벤트 핸들러 초기화
function initializeEventHandlers() {
    document.getElementById('connectForm').addEventListener('submit', handleConnect);
    document.getElementById('disconnectBtn').addEventListener('click', handleDisconnect);
    document.getElementById('fetchBtn').addEventListener('click', handleFetchEmails);
    document.getElementById('sendForm').addEventListener('submit', handleSendEmail);
    document.getElementById('workflowForm').addEventListener('submit', handleWorkflow);
    document.getElementById('modalClose').addEventListener('click', closeModal);

    document.getElementById('emailModal').addEventListener('click', (e) => {
        if (e.target.id === 'emailModal') closeModal();
    });

    document.getElementById('summaryModal').addEventListener('click', (e) => {
        if (e.target.id === 'summaryModal') closeSummaryModal();
    });
}

// 상태 확인
async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        if (data.success && data.connected) {
            connected = true;
            updateConnectionStatus(true);
            showMainSection();
        } else {
            connected = false;
            updateConnectionStatus(false);
        }
    } catch (error) {
        console.error('상태 확인 실패:', error);
        updateConnectionStatus(false);
    }
}

// 연결 상태 업데이트
function updateConnectionStatus(isConnected) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    if (isConnected) {
        statusDot.classList.add('connected');
        statusText.textContent = '연결됨';
    } else {
        statusDot.classList.remove('connected');
        statusText.textContent = '연결 안됨';
    }
}

// 메인 섹션 표시/숨기기
function showMainSection() {
    document.getElementById('mainSection').style.display = 'block';
}

function hideMainSection() {
    document.getElementById('mainSection').style.display = 'none';
}

// 연결 처리
async function handleConnect(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const openaiKey = document.getElementById('openaiKey').value;

    const connectBtn = document.getElementById('connectBtn');
    connectBtn.disabled = true;
    connectBtn.textContent = '연결 중...';

    try {
        const response = await fetch('/api/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: username,
                password: password,
                openai_key: openaiKey
            })
        });

        const data = await response.json();

        if (data.success) {
            connected = true;
            updateConnectionStatus(true);
            showMainSection();
            showAlert('연결 성공', 'success', 'alertBox');

            connectBtn.style.display = 'none';
            document.getElementById('disconnectBtn').style.display = 'inline-block';
        } else {
            showAlert(data.error || '연결 실패', 'error', 'alertBox');
        }
    } catch (error) {
        showAlert('연결 중 오류 발생: ' + error.message, 'error', 'alertBox');
    } finally {
        connectBtn.disabled = false;
        connectBtn.textContent = '연결하기';
    }
}

// 연결 해제 처리
async function handleDisconnect() {
    try {
        const response = await fetch('/api/disconnect', { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            connected = false;
            updateConnectionStatus(false);
            hideMainSection();
            showAlert('연결 해제됨', 'info', 'alertBox');

            document.getElementById('connectBtn').style.display = 'inline-block';
            document.getElementById('disconnectBtn').style.display = 'none';
            document.getElementById('connectForm').reset();
        }
    } catch (error) {
        showAlert('연결 해제 중 오류 발생', 'error', 'alertBox');
    }
}

// 메일 가져오기 처리
async function handleFetchEmails() {
    if (!connected) {
        showAlert('먼저 연결해주세요', 'error', 'alertBox');
        return;
    }

    const limit = document.getElementById('emailLimit').value;
    const criteria = document.getElementById('emailCriteria').value;
    const fetchBtn = document.getElementById('fetchBtn');
    const container = document.getElementById('emailListContainer');

    fetchBtn.disabled = true;
    fetchBtn.textContent = '가져오는 중...';

    const criteriaText = criteria === 'ALL' ? '전체 메일' :
                        criteria === 'UNSEEN' ? '안읽은 메일' : '읽은 메일';
    container.innerHTML = `<div class="empty-state"><p>${criteriaText}을 가져오는 중...<br>첨부파일 텍스트 추출 중...</p></div>`;

    try {
        const response = await fetch('/api/fetch-emails', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                limit: parseInt(limit),
                criteria: criteria
            })
        });

        const data = await response.json();

        if (data.success) {
            displayEmails(data.emails, criteriaText);
        } else {
            container.innerHTML = '<div class="empty-state"><p>' + (data.error || '메일 가져오기 실패') + '</p></div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="empty-state"><p>오류 발생: ' + error.message + '</p></div>';
    } finally {
        fetchBtn.disabled = false;
        fetchBtn.textContent = '메일 가져오기';
    }
}

// 메일 목록 표시
function displayEmails(emails, filterText) {
    const container = document.getElementById('emailListContainer');

    if (!emails || emails.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>메일이 없습니다</p></div>';
        return;
    }

    const emailListHTML = emails.map(email => `
        <div class="email-item" onclick="viewEmail('${email.id}')">
            <div class="email-header">
                <div class="email-subject">${escapeHtml(email.subject || '제목 없음')}</div>
                <div class="email-date">${formatDate(email.date)}</div>
            </div>
            <div class="email-sender">${escapeHtml(email.sender || '발신자 없음')}</div>
            <div class="email-preview">${escapeHtml(truncate(email.body || '', 100))}</div>
            <div class="email-meta">
                ${email.has_attachments ? `<span class="attachment-badge">첨부파일 ${email.attachment_count}개</span>` : ''}
                ${email.has_extracted_attachments ? `<span class="attachment-badge" style="background: var(--blue-500);">텍스트 추출됨</span>` : ''}
            </div>
        </div>
    `).join('');

    container.innerHTML = `
        <div style="margin-bottom: 1rem; color: var(--gray-600); font-size: 0.875rem;">
            ${filterText} <span class="filter-badge">${emails.length}개</span>
        </div>
        <div class="email-list">${emailListHTML}</div>
    `;
}

// 메일 상세 보기
async function viewEmail(emailId) {
    currentEmailId = emailId;
    const modal = document.getElementById('emailModal');
    const modalBody = document.getElementById('modalBody');
    const modalFooter = document.getElementById('modalFooter');

    modalBody.innerHTML = '<p>로딩 중...</p>';
    modalFooter.innerHTML = '';
    modal.classList.add('active');

    try {
        const response = await fetch(`/api/email/${emailId}`);
        const data = await response.json();

        if (data.success) {
            displayEmailDetail(data.email);
        } else {
            modalBody.innerHTML = '<p>' + (data.error || '메일을 불러올 수 없습니다') + '</p>';
        }
    } catch (error) {
        modalBody.innerHTML = '<p>오류 발생: ' + error.message + '</p>';
    }
}

// 메일 상세 내용 표시
function displayEmailDetail(email) {
    const modalBody = document.getElementById('modalBody');
    const modalFooter = document.getElementById('modalFooter');

    let attachmentsHTML = '';
    if (email.attachments && email.attachments.length > 0) {
        const attachmentItems = email.attachments.map(att => `
            <div class="attachment-item">
                <div class="attachment-info">
                    <div class="attachment-name">${escapeHtml(att.filename)}</div>
                    <div class="attachment-size">${formatBytes(att.size)}</div>
                    ${att.extracted_text ? '<span class="extracted-badge">텍스트 추출됨</span>' : ''}
                </div>
                <button class="attachment-download" onclick="downloadAttachment('${email.id}', '${escapeHtml(att.filename)}')">
                    다운로드
                </button>
            </div>
        `).join('');

        attachmentsHTML = `
            <div class="attachments-section">
                <div class="attachments-title">첨부파일 (${email.attachments.length}개)</div>
                <div class="attachment-list">${attachmentItems}</div>
            </div>
        `;
    }

    modalBody.innerHTML = `
        <div class="email-detail-header">
            <div class="email-detail-title">${escapeHtml(email.subject || '제목 없음')}</div>
            <div class="email-detail-meta">
                <div class="meta-row">
                    <div class="meta-label">발신자</div>
                    <div class="meta-value">${escapeHtml(email.sender || '')}</div>
                </div>
                <div class="meta-row">
                    <div class="meta-label">수신자</div>
                    <div class="meta-value">${escapeHtml(email.recipient || '')}</div>
                </div>
                <div class="meta-row">
                    <div class="meta-label">날짜</div>
                    <div class="meta-value">${formatDate(email.date)}</div>
                </div>
            </div>
        </div>
        <div class="email-body">${escapeHtml(email.body || '')}</div>
        ${attachmentsHTML}
    `;

    // 요약 버튼 추가
    const hasAttachments = email.attachments && email.attachments.length > 0;
    const hasExtractedText = email.has_extracted_attachments || false;

    modalFooter.innerHTML = `
        <div style="display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; width: 100%;">
            <select class="form-select" id="modalSummaryType" style="width: 150px;">
                <option value="brief">간단 요약</option>
                <option value="detailed">상세 요약</option>
                <option value="bullet">불렛 포인트</option>
                <option value="korean" selected>한국어 요약</option>
            </select>
            ${hasExtractedText ? `
            <div style="display: flex; gap: 0.75rem; border-left: 1px solid var(--gray-300); padding-left: 1rem;">
                <label class="radio-label">
                    <input type="radio" name="summaryScope" value="body" checked>
                    본문만
                </label>
                <label class="radio-label">
                    <input type="radio" name="summaryScope" value="all">
                    본문+첨부파일
                </label>
                <label class="radio-label">
                    <input type="radio" name="summaryScope" value="attachments">
                    첨부파일만
                </label>
            </div>
            ` : ''}
            <button class="btn btn-summarize" onclick="summarizeCurrentEmail()" style="margin-left: auto;">
                이 메일 요약하기
            </button>
        </div>
    `;
}

// 현재 메일 요약하기
async function summarizeCurrentEmail() {
    if (!currentEmailId) {
        alert('메일을 선택해주세요');
        return;
    }

    const summaryType = document.getElementById('modalSummaryType').value;

    // 라디오 버튼으로 범위 선택
    const scopeRadios = document.querySelectorAll('input[name="summaryScope"]');
    let selectedScope = 'body'; // 기본값
    scopeRadios.forEach(radio => {
        if (radio.checked) selectedScope = radio.value;
    });

    // 선택에 따라 파라미터 설정
    let includeAttachments = false;
    let onlyAttachments = false;
    let scopeText = '본문만';

    if (selectedScope === 'all') {
        includeAttachments = true;
        onlyAttachments = false;
        scopeText = '본문+첨부파일';
    } else if (selectedScope === 'attachments') {
        includeAttachments = false;
        onlyAttachments = true;
        scopeText = '첨부파일만';
    } else {
        includeAttachments = false;
        onlyAttachments = false;
        scopeText = '본문만';
    }

    const summaryModal = document.getElementById('summaryModal');
    const summaryModalBody = document.getElementById('summaryModalBody');

    summaryModalBody.innerHTML = `<p>요약 중...<br><small>${scopeText}</small></p>`;
    summaryModal.classList.add('active');

    try {
        const response = await fetch('/api/summarize-email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email_id: currentEmailId,
                summary_type: summaryType,
                include_attachments: includeAttachments,
                only_attachments: onlyAttachments
            })
        });

        const data = await response.json();

        if (data.success) {
            summaryModalBody.innerHTML = `
                <div class="summary-content">
                    ${escapeHtml(data.summary)}
                </div>
                <div class="summary-meta">
                    <div class="summary-meta-item">
                        <span class="summary-meta-label">압축률</span>
                        <span>${data.compression_ratio}%</span>
                    </div>
                    <div class="summary-meta-item">
                        <span class="summary-meta-label">원본 토큰</span>
                        <span>${data.original_tokens}</span>
                    </div>
                    <div class="summary-meta-item">
                        <span class="summary-meta-label">요약 토큰</span>
                        <span>${data.summary_tokens}</span>
                    </div>
                    <div class="summary-meta-item">
                        <span class="summary-meta-label">요약 범위</span>
                        <span>${data.summary_scope || scopeText}</span>
                    </div>
                </div>
            `;
        } else {
            summaryModalBody.innerHTML = `<p>오류: ${data.error}</p>`;
        }
    } catch (error) {
        summaryModalBody.innerHTML = `<p>오류 발생: ${error.message}</p>`;
    }
}

// 요약 모달 닫기
function closeSummaryModal() {
    document.getElementById('summaryModal').classList.remove('active');
}

// 첨부파일 다운로드
function downloadAttachment(emailId, filename) {
    window.open(`/api/download/${emailId}/${encodeURIComponent(filename)}`, '_blank');
}

// 모달 닫기
function closeModal() {
    document.getElementById('emailModal').classList.remove('active');
    currentEmailId = null;
}

// 메일 발송 처리
async function handleSendEmail(e) {
    e.preventDefault();

    if (!connected) {
        showAlert('먼저 연결해주세요', 'error', 'sendAlertBox');
        return;
    }

    const toEmails = document.getElementById('toEmails').value;
    const ccEmails = document.getElementById('ccEmails').value;
    const subject = document.getElementById('subject').value;
    const body = document.getElementById('body').value;

    const form = document.getElementById('sendForm');
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = '전송 중...';

    try {
        const response = await fetch('/api/send-email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                to_emails: toEmails,
                cc_emails: ccEmails,
                subject: subject,
                body: body
            })
        });

        const data = await response.json();

        if (data.success) {
            showAlert('메일이 전송되었습니다', 'success', 'sendAlertBox');
            form.reset();
        } else {
            showAlert(data.error || '메일 전송 실패', 'error', 'sendAlertBox');
        }
    } catch (error) {
        showAlert('메일 전송 중 오류 발생: ' + error.message, 'error', 'sendAlertBox');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = '메일 전송';
    }
}

// 통합 워크플로우 처리
async function handleWorkflow(e) {
    e.preventDefault();

    if (!connected) {
        showAlert('먼저 연결해주세요', 'error', 'workflowAlertBox');
        return;
    }

    const workflowTo = document.getElementById('workflowTo').value;
    const workflowCriteria = document.getElementById('workflowCriteria').value;
    const workflowLimit = document.getElementById('workflowLimit').value;
    const summaryType = document.getElementById('summaryType').value;
    const workflowSubject = document.getElementById('workflowSubject').value;

    const form = document.getElementById('workflowForm');
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = '처리 중... (첨부파일 텍스트 포함)';

    try {
        const response = await fetch('/api/workflow', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                to_emails: [workflowTo],
                criteria: workflowCriteria,
                limit: parseInt(workflowLimit),
                summary_type: summaryType,
                subject: workflowSubject
            })
        });

        const data = await response.json();

        if (data.success) {
            showAlert('통합 작업이 완료되었습니다 (첨부파일 텍스트 포함)', 'success', 'workflowAlertBox');
        } else {
            showAlert(data.error || '통합 작업 실패', 'error', 'workflowAlertBox');
        }
    } catch (error) {
        showAlert('통합 작업 중 오류 발생: ' + error.message, 'error', 'workflowAlertBox');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = '가져오기 + 요약 + 전송';
    }
}

// 알림 표시
function showAlert(message, type, containerId) {
    const container = document.getElementById(containerId);
    const alertClass = `alert alert-${type}`;

    container.innerHTML = `<div class="${alertClass}">${escapeHtml(message)}</div>`;

    setTimeout(() => {
        container.innerHTML = '';
    }, 5000);
}

// 유틸리티 함수
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncate(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function formatDate(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) {
            return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
        } else if (diffDays < 7) {
            return diffDays + '일 전';
        } else {
            return date.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });
        }
    } catch (error) {
        return dateString;
    }
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}