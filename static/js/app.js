
var chatMessages, chatInput, btnSend;
var isLoading = false;
var currentUser = null;
var authToken = localStorage.getItem('tradeMasterToken') || null;
var regIdentity = 'seller';
var emailFilter = 'all';

// Helper: return auth headers for all API calls
function getAuthHeaders() {
    var h = {'Content-Type': 'application/json'};
    if (authToken) h['Authorization'] = 'Bearer ' + authToken;
    return h;
}

var allEmails = [];
var currentLang = (localStorage.getItem('tradeMasterLang') || 'zh');

// ===== i18n System =====
var I18N = {
    zh: {
        appTitle: '外贸通', authLoginTitle: '登录您的账号', authRegisterTitle: '创建新账号',
        emailLabel: '邮箱地址', passwordLabel: '密码', phoneLabel: '联系电话', companyLabel: '公司名称（选填）',
        productLabel: '主营产品', identityLabel: '选择身份',
        sellerLabel: '我是销售', sellerDesc: '找买家 / 写开发信 / 客户跟进',
        bossLabel: '我是老板', bossDesc: '看数据 / 管团队 / 分析趋势',
        btnLogin: '登 录', btnRegister: '注 册',
        noAccount: '还没有账号？', hasAccount: '已有账号？',
        lnkRegister: '立即注册', lnkLogin: '立即登录',
        emailPlaceholder: 'your@email.com', phonePlaceholder: '13800138000',
        companyPlaceholder: '深圳XX科技有限公司', productPlaceholder: '例如：LED灯具',
        emailBox: '📧 邮件箱', btnLogout: '退出', btnClear: '清空',
        welcomeTitle: '👋 欢迎使用外贸通', welcomeDesc: '我是您的智能外贸业务助理',
        quickSearch: '🔍 搜索买家', quickRate: '💱 查询汇率', quickDesc: '📝 商品描述',
        quickSlogan: '🎯 广告语', quickHelp: '❓ 帮助',
        quickSearchPrompt: '帮我搜索电子产品相关的买家',
        quickRatePrompt: '美元兑人民币的汇率是多少？',
        quickDescPrompt: '帮我为便携式加湿器生成商品描述',
        quickSloganPrompt: '为夏日防晒衣生成几条广告语',
        quickHelpPrompt: '帮助', inputPlaceholder: '输入您的问题...',
        filterAll: '全部', filterSent: '已发送', filterReplied: '已回复', filterPending: '待跟进',
        noEmails: '暂无邮件', noMatch: '无匹配邮件',
        statusSent: '已发送', statusReplied: '已回复', statusBounced: '已退回', statusNoReply: '未回复',
        today: '今天', yesterday: '昨天', daysAgo: '天前',
        btnReplied: '已回复', btnBounced: '已退回', btnFollowUp: '跟进',
        badgeBoss: '老板', badgeSeller: '销售',
        networkError: '网络错误，请稍后重试', timeoutError: '请求超时，请简化问题后重试',
        emailGenerated: '📧 邮件内容', copyEmail: '📋 复制全部', openMail: '📋 复制并打开',
        copied: '✅ 已复制！粘贴到邮件中发送', opened: '✅ 已打开，请粘贴发送', copiedToast: '✅ 已复制',
        copyAnswer: '📋 复制回答', regenerate: '🔄 重新生成', copiedAnswer: '✅ 已复制',
        sessionCleared: '会话已清空，我们可以开始新的对话了！',
        followUpPrompt: '帮我给 {name} 写一封跟进邮件，原主题：{subject}',
        allDone: '✓ 全部完成',
    },
    en: {
        appTitle: 'TradeMaster', authLoginTitle: 'Login to your account', authRegisterTitle: 'Create a new account',
        emailLabel: 'Email Address', passwordLabel: 'Password', phoneLabel: 'Phone Number', companyLabel: 'Company Name (optional)',
        productLabel: 'Main Product', identityLabel: 'Select Role',
        sellerLabel: 'I am a Sales Rep', sellerDesc: 'Find buyers / Write emails / Follow up',
        bossLabel: 'I am a Boss', bossDesc: 'View data / Manage team / Analyze trends',
        btnLogin: 'Login', btnRegister: 'Register',
        noAccount: "Don't have an account?", hasAccount: 'Already have an account?',
        lnkRegister: 'Register now', lnkLogin: 'Login now',
        emailPlaceholder: 'your@email.com', phonePlaceholder: '13800138000',
        companyPlaceholder: 'Shenzhen XX Tech Co., Ltd.', productPlaceholder: 'e.g. LED Lighting',
        emailBox: '📧 Mailbox', btnLogout: 'Logout', btnClear: 'Clear',
        welcomeTitle: '👋 Welcome to TradeMaster', welcomeDesc: 'Your intelligent foreign trade assistant',
        quickSearch: '🔍 Find Buyers', quickRate: '💱 Exchange Rate', quickDesc: '📝 Product Desc',
        quickSlogan: '🎯 Slogans', quickHelp: '❓ Help',
        quickSearchPrompt: 'Help me find electronics buyers',
        quickRatePrompt: 'What is the USD to CNY exchange rate?',
        quickDescPrompt: 'Generate a product description for a portable humidifier',
        quickSloganPrompt: 'Generate slogans for summer sun-protective clothing',
        quickHelpPrompt: 'Help', inputPlaceholder: 'Type your question...',
        filterAll: 'All', filterSent: 'Sent', filterReplied: 'Replied', filterPending: 'Pending',
        noEmails: 'No emails yet', noMatch: 'No matching emails',
        statusSent: 'Sent', statusReplied: 'Replied', statusBounced: 'Bounced', statusNoReply: 'No Reply',
        today: 'Today', yesterday: 'Yesterday', daysAgo: 'd ago',
        btnReplied: 'Replied', btnBounced: 'Bounced', btnFollowUp: 'Follow Up',
        badgeBoss: 'Boss', badgeSeller: 'Sales',
        networkError: 'Network error, please try again', timeoutError: 'Request timed out',
        emailGenerated: '📧 Email Ready', copyEmail: '📋 Copy Email', openMail: '✉️ Open Mail Client',
        copied: '✅ Copied! Paste into your email client', opened: '✅ Opened, paste and send', copiedToast: '✅ Copied',
        copyAnswer: '📋 Copy Answer', regenerate: '🔄 Regenerate', copiedAnswer: '✅ Copied',
        sessionCleared: 'Session cleared. Starting a new conversation!',
        followUpPrompt: 'Help me write a follow-up email to {name}, original subject: {subject}',
        allDone: '✓ All done',
    }
};

function t(key) { return (I18N[currentLang] || I18N['zh'])[key] || key; }

function _updateAuthLabels() {
    var isReg = document.getElementById('registerForm').style.display !== 'none';
    document.getElementById('authSubtitle').textContent = isReg ? t('authRegisterTitle') : t('authLoginTitle');
    document.getElementById('btnLogin').textContent = t('btnLogin');
    document.getElementById('btnRegister').textContent = t('btnRegister');
    document.getElementById('loginEmail').placeholder = t('emailPlaceholder');
    document.getElementById('regEmail').placeholder = t('emailPlaceholder');
    document.getElementById('regPhone').placeholder = t('phonePlaceholder');
    document.getElementById('regCompany').placeholder = t('companyPlaceholder');
    document.getElementById('regProduct').placeholder = t('productPlaceholder');
    // Login form labels
    var lfLabels = document.querySelectorAll('#loginForm label');
    if (lfLabels[0]) lfLabels[0].textContent = t('emailLabel');
    if (lfLabels[1]) lfLabels[1].textContent = t('passwordLabel');
    // Register form labels
    var rfLabels = document.querySelectorAll('#registerForm label');
    if (rfLabels[0]) rfLabels[0].textContent = t('emailLabel');
    if (rfLabels[1]) rfLabels[1].textContent = t('passwordLabel');
    if (rfLabels[2]) rfLabels[2].textContent = t('phoneLabel');
    if (rfLabels[3]) rfLabels[3].textContent = t('companyLabel');
    if (rfLabels[4]) rfLabels[4].textContent = t('productLabel');
    if (rfLabels[5]) rfLabels[5].textContent = t('identityLabel');
    // Identity cards
    document.querySelector('#cardSeller .id-label').textContent = t('sellerLabel');
    document.querySelector('#cardSeller .id-desc').textContent = t('sellerDesc');
    document.querySelector('#cardBoss .id-label').textContent = t('bossLabel');
    document.querySelector('#cardBoss .id-desc').textContent = t('bossDesc');
    // Switch links text (text nodes before <a>)
    var lfSwitch = document.querySelector('#loginForm .auth-switch');
    if (lfSwitch && lfSwitch.childNodes[0]) lfSwitch.childNodes[0].textContent = t('noAccount');
    var lfLink = document.getElementById('lnkRegister');
    if (lfLink) lfLink.textContent = t('lnkRegister');
    var rfSwitch = document.querySelector('#registerForm .auth-switch');
    if (rfSwitch && rfSwitch.childNodes[0]) rfSwitch.childNodes[0].textContent = t('hasAccount');
    var rfLink = document.getElementById('lnkLogin');
    if (rfLink) rfLink.textContent = t('lnkLogin');
}

function renderWelcomeMessage(container) {
    var w = container || document.querySelector('.welcome-message');
    if (!w) return;
    w.innerHTML = '<h2>' + t('welcomeTitle') + '</h2>' +
        '<p>' + t('welcomeDesc') + '</p>' +
        '<div class="quick-actions">' +
            '<button class="quick-btn" data-action="' + t('quickSearchPrompt') + '">' + t('quickSearch') + '</button>' +
            '<button class="quick-btn" data-action="' + t('quickRatePrompt') + '">' + t('quickRate') + '</button>' +
            '<button class="quick-btn" data-action="' + t('quickDescPrompt') + '">' + t('quickDesc') + '</button>' +
            '<button class="quick-btn" data-action="' + t('quickSloganPrompt') + '">' + t('quickSlogan') + '</button>' +
            '<button class="quick-btn" data-action="' + t('quickHelpPrompt') + '">' + t('quickHelp') + '</button>' +
        '</div>';
    w.querySelectorAll('.quick-btn').forEach(function(btn) {
        btn.addEventListener('click', function() { sendQuickAction(this.dataset.action); });
    });
}

function applyLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('tradeMasterLang', lang);
    var zhBtn = document.getElementById('langZH2'); if(zhBtn) zhBtn.className = 'lang-mini-btn' + (lang === 'zh' ? ' active' : '');
    var enBtn = document.getElementById('langEN2'); if(enBtn) enBtn.className = 'lang-mini-btn' + (lang === 'en' ? ' active' : '');

    // Auth panel
    _updateAuthLabels();

    // Header
    var h1 = document.querySelector('.chat-header h1');
    if (h1) h1.innerHTML = '<span>&#x1f310;</span> ' + t('appTitle');
    document.getElementById('chatInput').placeholder = t('inputPlaceholder');
    document.getElementById('btnLogout').textContent = t('btnLogout');
    document.getElementById('btnClear').textContent = t('btnClear');

    // Email panel
    document.querySelectorAll('.email-filter-tab').forEach(function(tb, i) {
        var keys = ['filterAll','filterSent','filterReplied','filterPending'];
        if (i < keys.length) tb.textContent = t(keys[i]);
    });

    // Welcome message
    renderWelcomeMessage();

    // Re-render email list
    renderEmailList();
    updateUserBar();
}

document.addEventListener('DOMContentLoaded', function() {
    chatMessages = document.getElementById('chatMessages');
    chatInput = document.getElementById('chatInput');
    btnSend = document.getElementById('btnSend');

    // Auth buttons
    document.getElementById('btnLogin').addEventListener('click', doLogin);
    document.getElementById('btnDemoLogin').addEventListener('click', function(){
        document.getElementById('loginEmail').value = 'demo@trademaster.com';
        document.getElementById('loginPassword').value = 'demo2024';
        doLogin();
    });
    document.getElementById('btnRegister').addEventListener('click', doRegister);
    document.getElementById('lnkRegister').addEventListener('click', showRegister);
    document.getElementById('lnkLogin').addEventListener('click', showLogin);
    // Enter key for auth password fields
    document.getElementById('loginPassword').addEventListener('keydown', function(e) { if (e.key === 'Enter') doLogin(); });
    document.getElementById('regPassword').addEventListener('keydown', function(e) { if (e.key === 'Enter') doRegister(); });
    document.getElementById('cardSeller').addEventListener('click', function(){selectIdentity('seller')});
    document.getElementById('cardBoss').addEventListener('click', function(){selectIdentity('boss')});
    document.getElementById('btnLogout').addEventListener('click', doLogout);
    document.getElementById('btnToggleEmail').addEventListener('click', toggleEmailPanel);
    document.getElementById('btnToggleContacts').addEventListener('click', toggleContactPanel);
    document.getElementById('btnUpload').addEventListener('click', function(){ document.getElementById('fileInput').click(); });
    document.getElementById('btnExcelUpload').addEventListener('click', function(){ document.getElementById('excelInput').click(); });
    initSidebar();
    initDoll();
    // Retry queue
    updateRetryBadge();
    updateApiStatus();  // 初始检查API状态
    if (getFailedQueue().length > 0) {
        setTimeout(function(){ showRetryQueueMsg(); }, 1000);
        setTimeout(function(){ processRetryQueue(); }, 3000);
    }
    document.getElementById('btnSmtpSettings').addEventListener('click', openSmtpSettings);
    document.getElementById('btnSmtpSave').addEventListener('click', saveSmtpSettings);
    document.getElementById('btnSmtpTest').addEventListener('click', testSmtpSettings);
    document.getElementById('btnSmtpClose').addEventListener('click', closeSmtpSettings);
    // Click overlay to close
    document.getElementById('smtpOverlay').addEventListener('click', function(e) { if (e.target === this) closeSmtpSettings(); });

    // Language toggle
    var zh2 = document.getElementById('langZH2'); if(zh2) zh2.addEventListener('click', function() { applyLanguage('zh'); });
    var en2 = document.getElementById('langEN2'); if(en2) en2.addEventListener('click', function() { applyLanguage('en'); });
    applyLanguage(currentLang);

    // Email filter tabs
    document.querySelectorAll('.email-filter-tab').forEach(function(tab) {
        tab.addEventListener('click', function() { filterEmails(this.dataset.filter); });
    });

    // Quick action buttons
    document.querySelectorAll('.quick-btn').forEach(function(btn) {
        btn.addEventListener('click', function() { sendQuickAction(this.dataset.action); });
    });

    // Chat input
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
    btnSend.addEventListener('click', sendMessage);

    // Auto-login
    try {
        var saved = localStorage.getItem('tradeMasterUser');
        if (saved) {
            currentUser = JSON.parse(saved);
            showAuthOverlay(false);
            updateUserBar();
            document.getElementById('emailPanel').classList.add('open');
            loadEmailBox();
            loadDashboard();
        } else {
            showAuthOverlay(true);
        }
    } catch(e) { showAuthOverlay(true); }
});

// ===== Auth Functions =====
function selectIdentity(id) {
    regIdentity = id;
    document.getElementById('cardSeller').className = 'identity-card' + (id === 'seller' ? ' selected' : '');
    document.getElementById('cardBoss').className = 'identity-card' + (id === 'boss' ? ' selected' : '');
}

function showRegister() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
    _updateAuthLabels();
}

function showLogin() {
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('loginForm').style.display = 'block';
    _updateAuthLabels();
}

function showAuthOverlay(show) {
    document.getElementById('authOverlay').style.display = show ? 'flex' : 'none';
}

function updateUserBar() {
    if (!currentUser) return;
    document.getElementById('userBar').style.display = 'flex';
    document.getElementById('btnLogout').style.display = 'inline-block';
    document.getElementById('userEmailDisplay').textContent = currentUser.email;
    document.getElementById('userBadge').textContent = currentUser.identity === 'boss' ? t('badgeBoss') : t('badgeSeller');
    document.getElementById('userIdentityIcon').textContent = currentUser.identity === 'boss' ? '\u{1f454}' : '\u{1f9d1}‍\u{1f4bc}';
}

async function doLogin() {
    var email = document.getElementById('loginEmail').value.trim();
    var password = document.getElementById('loginPassword').value.trim();
    var errEl = document.getElementById('loginError');
    if (!email) { errEl.textContent = '请输入邮箱地址'; errEl.style.display = 'block'; return; }
    if (!password) { errEl.textContent = '请输入密码'; errEl.style.display = 'block'; return; }
    errEl.style.display = 'none';
    try {
        var resp = await fetch('/api/login', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({email: email, password: password})
        });
        var data = await resp.json();
        if (data.success) {
            currentUser = data.user;
            if (data.token) { authToken = data.token; localStorage.setItem('tradeMasterToken', data.token); }
            localStorage.setItem('tradeMasterUser', JSON.stringify(currentUser));
            showAuthOverlay(false);
            updateUserBar();
            document.getElementById("emailPanel").classList.add("open");
            loadEmailBox();
            loadDashboard();
            loadSidebarData();
            chatInput.focus();
        } else {
            errEl.textContent = data.error || '登录失败';
            errEl.style.display = 'block';
        }
    } catch(e) {
        errEl.textContent = t('networkError');
        errEl.style.display = 'block';
    }
}

async function doRegister() {
    var email = document.getElementById('regEmail').value.trim();
    var password = document.getElementById('regPassword').value.trim();
    var phone = document.getElementById('regPhone').value.trim();
    var company = document.getElementById('regCompany').value.trim();
    var product = document.getElementById('regProduct').value.trim();
    var errEl = document.getElementById('regError');
    if (!email || email.indexOf('@') < 0) { errEl.textContent = '请输入有效的邮箱地址'; errEl.style.display = 'block'; return; }
    if (!password || password.length < 6) { errEl.textContent = '密码长度不能少于6位'; errEl.style.display = 'block'; return; }
    if (!phone) { errEl.textContent = '请输入联系电话'; errEl.style.display = 'block'; return; }
    if (!product) { errEl.textContent = '请输入主营产品'; errEl.style.display = 'block'; return; }
    errEl.style.display = 'none';
    try {
        var resp = await fetch('/api/register', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({email: email, password: password, phone: phone, company: company, product: product, identity: regIdentity})
        });
        var data = await resp.json();
        if (data.success) {
            currentUser = data.user;
            if (data.token) { authToken = data.token; localStorage.setItem('tradeMasterToken', data.token); }
            localStorage.setItem('tradeMasterUser', JSON.stringify(currentUser));
            showAuthOverlay(false);
            updateUserBar();
            document.getElementById("emailPanel").classList.add("open");
            loadEmailBox();
            chatInput.focus();
        } else {
            errEl.textContent = data.error || '注册失败';
            errEl.style.display = 'block';
        }
    } catch(e) {
        errEl.textContent = t('networkError');
        errEl.style.display = 'block';
    }
}

function doLogout() {
    currentUser = null;
    authToken = null;
    localStorage.removeItem('tradeMasterUser');
    localStorage.removeItem('tradeMasterToken');
    document.getElementById('userBar').style.display = 'none';
    document.getElementById('btnLogout').style.display = 'none';
    showAuthOverlay(true);
    chatMessages.innerHTML = '';
    var div = document.createElement('div');
    div.className = 'welcome-message';
    chatMessages.appendChild(div);
    renderWelcomeMessage(div);
}

// ===== Email Panel =====
function toggleEmailPanel() {
    var panel = document.getElementById('emailPanel');
    panel.classList.toggle('open');
    if (panel.classList.contains('open')) loadEmailBox();
}

// ===== SMTP Settings =====
function openSmtpSettings() {
    document.getElementById('smtpOverlay').classList.add('show');
    document.getElementById('smtpMsg').className = 'smtp-msg';
    // Load existing config
    fetch('/api/email/smtp_settings').then(function(r){return r.json();}).then(function(d){
        if(d.success){
            document.getElementById('smtpEmail').value = d.config.smtp_email || '';
            document.getElementById('smtpSenderName').value = d.config.sender_name || '';
            document.getElementById('smtpPassword').value = '';
            if(d.config.has_password){
                document.getElementById('smtpPassword').placeholder = '已保存（留空则保持原密码）';
            }
        }
    }).catch(function(){});
}

function closeSmtpSettings() {
    document.getElementById('smtpOverlay').classList.remove('show');
}

function showSmtpMsg(type, text) {
    var el = document.getElementById('smtpMsg');
    el.className = 'smtp-msg ' + type;
    el.textContent = text;
}

function saveSmtpSettings() {
    var email = document.getElementById('smtpEmail').value.trim();
    var pwd = document.getElementById('smtpPassword').value.trim();
    var name = document.getElementById('smtpSenderName').value.trim();
    if (!email || email.indexOf('@') < 0) { showSmtpMsg('error', '请输入有效的邮箱地址'); return; }
    if (!pwd) { showSmtpMsg('error', '请输入授权码'); return; }
    showSmtpMsg('info', '保存中...');
    fetch('/api/email/smtp_settings', {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({smtp_email: email, smtp_password: pwd, sender_name: name})
    }).then(function(r){return r.json();}).then(function(d){
        if(d.success) { showSmtpMsg('success', '✅ ' + d.message + ' — 现在可以用 TradeMaster 发送邮件了！'); }
        else { showSmtpMsg('error', d.error || '保存失败'); }
    });
}

function testSmtpSettings() {
    var email = document.getElementById('smtpEmail').value.trim();
    var pwd = document.getElementById('smtpPassword').value.trim();
    var name = document.getElementById('smtpSenderName').value.trim();
    if (!email || email.indexOf('@') < 0) { showSmtpMsg('error', '请输入有效的邮箱地址'); return; }
    if (!pwd) { showSmtpMsg('error', '请输入授权码'); return; }
    showSmtpMsg('info', '正在通过 SMTP 发送测试邮件...');
    fetch('/api/email/smtp_test', {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({smtp_email: email, smtp_password: pwd, sender_name: name})
    }).then(function(r){return r.json();}).then(function(d){
        if(d.success) { showSmtpMsg('success', '✅ 测试邮件已发送至 ' + email + '，请检查收件箱！'); }
        else { showSmtpMsg('error', '❌ ' + (d.error || '发送失败')); }
    }).catch(function(){ showSmtpMsg('error', '网络错误，请重试'); });
}

function filterEmails(filter) {
    emailFilter = filter;
    document.querySelectorAll('.email-filter-tab').forEach(function(t) {
        t.classList.toggle('active', t.dataset.filter === filter);
    });
    renderEmailList();
}

var _emailRefreshTimer = null;

async function loadEmailBox() {
    if (!currentUser) return;
    try {
        var resp = await fetch('/api/emails/sent', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({user_email: currentUser.email})
        });
        var data = await resp.json();
        if (data.success) {
            allEmails = data.emails || [];
            renderEmailList();
            updateEmailBadge();
            loadEmailStats();
        }
    } catch(e) {}
    // 自动刷新：每2分钟同步一次收件箱
    if (_emailRefreshTimer) clearInterval(_emailRefreshTimer);
    _emailRefreshTimer = setInterval(function(){
        if (document.getElementById('emailPanel').classList.contains('open')) {
            syncInboxSilent();
        }
    }, 120000);
}

function syncInboxSilent() {
    if (!currentUser) return;
    fetch('/api/email/sync', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({user_email: currentUser.email})
    }).then(function(r){return r.json()}).then(function(d){
        if (d.success && d.replies && d.replies.length > 0) {
            updateEmailBadge();
        }
        loadEmailBox();  // Always refresh after sync
    }).catch(function(){});
}

async function loadEmailStats() {
    if (!currentUser) return;
    try {
        var resp = await fetch('/api/email/stats', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({user_email: currentUser.email})
        });
        var data = await resp.json();
        if (data.success && data.stats) {
            var s = data.stats;
            document.getElementById('esTotal').textContent = s.total || 0;
            document.getElementById('esOpened').textContent = (s.opened || 0) + '/' + (s.total_opens || 0);
            document.getElementById('esReplied').textContent = s.replied || 0;
            document.getElementById('esPending').textContent = s.pending || 0;
            document.getElementById('esBounced').textContent = s.bounced || 0;
            document.getElementById('esRate').textContent = (s.open_rate || 0) + '%';
        }
    } catch(e) {}
}

function updateEmailBadge() {
    var badge = document.getElementById('emailBadge');
    var now = new Date();
    var pending = 0;
    allEmails.forEach(function(e) {
        if (e.status === 'sent' || e.status === 'no_reply') {
            var days = (now - new Date(e.sent_at.replace(' ', 'T'))) / 86400000;
            if (days >= 1) pending++;
        }
    });
    badge.textContent = pending;
    badge.className = 'badge' + (pending > 0 ? ' show' : '');
}

function renderEmailList() {
    var list = document.getElementById('emailList');
    var filtered = allEmails;
    var now = new Date();
    if (emailFilter === 'sent') filtered = allEmails.filter(function(e) { return e.status === 'sent' || e.status === 'no_reply'; });
    else if (emailFilter === 'replied') filtered = allEmails.filter(function(e) { return e.status === 'replied'; });
    else if (emailFilter === 'pending') {
        filtered = allEmails.filter(function(e) {
            if (e.status !== 'sent' && e.status !== 'no_reply') return false;
            return (now - new Date(e.sent_at.replace(' ', 'T'))) / 86400000 >= 1;
        });
    }
    filtered.sort(function(a, b) { return new Date(b.sent_at.replace(' ', 'T')) - new Date(a.sent_at.replace(' ', 'T')); });

    list.innerHTML = '';
    if (filtered.length === 0) {
        var emptyDiv = document.createElement('div');
        emptyDiv.style.cssText = 'text-align:center;padding:30px;color:#a3bfd8;font-size:13px';
        emptyDiv.textContent = allEmails.length === 0 ? t('noEmails') : t('noMatch');
        list.appendChild(emptyDiv);
        return;
    }

    var statusLabel = {
        sent: t('statusSent'), replied: t('statusReplied'),
        bounced: t('statusBounced'), no_reply: t('statusNoReply')
    };
    var intentLabels = {inquiry:'Inquiry',price_negotiation:'Price',sample_request:'Sample',order_confirmed:'Order',rejection:'Rejected',logistics:'Logistics',after_sales:'AfterSale',other:'Other'};

    filtered.forEach(function(e, i) {
        var st = e.status || 'sent';
        var days = Math.floor((now - new Date(e.sent_at.replace(' ', 'T'))) / 86400000);
        var timeStr = days === 0 ? t('today') : days === 1 ? t('yesterday') : days + t('daysAgo');

        var item = document.createElement('div');
        item.className = 'email-item';
        item.addEventListener('click', (function(idx) { return function() { toggleEmailDetail(idx); }; })(i));

        // Status badge
        var badge = document.createElement('span');
        badge.className = 'ei-status ' + st;
        badge.textContent = statusLabel[st] || st;
        item.appendChild(badge);

        // To
        var toSpan = document.createElement('span');
        toSpan.className = 'ei-to';
        toSpan.textContent = e.to_name || e.to;
        item.appendChild(toSpan);

        // Opened indicator
        if ((e.opened_count || 0) > 0) {
            var opened = document.createElement('span');
            opened.className = 'ei-opened';
            opened.style.cssText = 'color:#5bba8a;font-size:10px;margin-left:4px';
            opened.innerHTML = '&#x1f441; ' + e.opened_count;
            item.appendChild(opened);
        }

        // Intent badge
        if (e.intent) {
            var ibadge = document.createElement('span');
            ibadge.className = 'ei-intent ' + e.intent;
            ibadge.textContent = intentLabels[e.intent] || e.intent;
            item.appendChild(ibadge);
        }

        // Subject
        var subj = document.createElement('span');
        subj.className = 'ei-subject';
        subj.textContent = e.subject || '';
        item.appendChild(subj);

        // Date
        var dateSpan = document.createElement('span');
        dateSpan.className = 'ei-date';
        dateSpan.textContent = timeStr;
        item.appendChild(dateSpan);

        // Detail panel
        var detail = document.createElement('div');
        detail.className = 'ei-detail';
        detail.addEventListener('click', function(ev) { ev.stopPropagation(); });

        var toLine = document.createElement('div');
        toLine.innerHTML = '<b>To:</b> ' + (e.to || '');
        detail.appendChild(toLine);

        var subjLine = document.createElement('div');
        subjLine.innerHTML = '<b>Subject:</b> ' + (e.subject || '');
        detail.appendChild(subjLine);

        var preview = document.createElement('div');
        preview.style.cssText = 'color:#999;margin:4px 0';
        preview.textContent = e.body_preview || '';
        detail.appendChild(preview);

        // Tracking note
        if (e.tracking_id) {
            var tn = document.createElement('div');
            tn.style.cssText = 'font-size:10px;color:#aaa;margin-top:3px';
            tn.innerHTML = '&#x1f4cd; ' + e.tracking_id + ' | &#x1f441; ' + (e.opened_count||0) + 'x' + (e.opened_at ? ' (' + e.opened_at.substr(0,16) + ')' : '');
            detail.appendChild(tn);
        }

        // Action buttons
        var actions = document.createElement('div');
        actions.className = 'ei-actions';

        var btnReply = document.createElement('button');
        btnReply.className = 'ei-btn';
        btnReply.textContent = t('btnReplied');
        btnReply.addEventListener('click', (function(to) { return function() { markEmailStatus(to, 'replied'); }; })(e.to));
        actions.appendChild(btnReply);

        var btnBounce = document.createElement('button');
        btnBounce.className = 'ei-btn';
        btnBounce.textContent = t('btnBounced');
        btnBounce.addEventListener('click', (function(to) { return function() { markEmailStatus(to, 'bounced'); }; })(e.to));
        actions.appendChild(btnBounce);

        var btnFollow = document.createElement('button');
        btnFollow.className = 'ei-btn';
        btnFollow.textContent = t('btnFollowUp');
        btnFollow.addEventListener('click', (function(to, name, subj) { return function() { followUpEmail(to, name, subj); }; })(e.to, e.to_name || '', e.subject || ''));
        actions.appendChild(btnFollow);

        detail.appendChild(actions);
        item.appendChild(detail);
        list.appendChild(item);
    });
}

function toggleEmailDetail(i) {
    var items = document.querySelectorAll('.email-item');
    // Close all other expanded items
    items.forEach(function(item, idx) {
        if (idx !== i) item.classList.remove('expanded');
    });
    items[i].classList.toggle('expanded');
}

async function markEmailStatus(to_email, status) {
    if (!currentUser) return;
    try {
        await fetch('/api/emails/status', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({user_email: currentUser.email, to_email: to_email, status: status})
        });
        loadEmailBox();
    } catch(e) {}
}

function followUpEmail(to, name, subject) {
    var prompt = t('followUpPrompt').replace('{name}', name || to).replace('{subject}', subject);
    chatInput.value = prompt;
    chatInput.focus();
}

// ===== Chat Functions =====
function sendQuickAction(text) {
    if (text === '__add_to_contacts__') {
        showQuickAddContact();
        return;
    }
    chatInput.value = text;
    sendMessage();
}

function showQuickAddContact() {
    var name = prompt('请输入公司名称：', '');
    if (!name) return;
    var email = prompt('邮箱（没有可留空）：', '');
    var website = prompt('网站（没有可留空）：', '');
    var country = prompt('国家（如 Germany）：', '');
    if (currentUser) {
        addBuyerToContacts(name, email || '', website || '', country || '', '手动添加');
    } else {
        alert('请先登录后再添加客户');
    }
}

async function clearChat() {
    var payload = {session_id: currentUser ? currentUser.email : 'default'};
    if (currentUser) payload.user_email = currentUser.email;
    await fetch('/api/clear', {method: 'POST', headers: getAuthHeaders(), body: JSON.stringify(payload)});
    chatMessages.innerHTML = '';
    var div = document.createElement('div');
    div.className = 'welcome-message';
    chatMessages.appendChild(div);
    renderWelcomeMessage(div);
}

function addMessage(role, content, toolCalls) {
    var welcome = chatMessages.querySelector('.welcome-message');
    if (welcome) welcome.remove();
    var div = document.createElement('div');
    div.className = 'message ' + role;
    div.innerHTML = '<div class="msg-avatar">' + (role === 'user' ? '\u{1f464}' : '\u{1f916}') + '</div>' +
        '<div class="msg-content">' + formatMarkdown(content) + '</div>';
    chatMessages.appendChild(div);
    smartScroll();
}

function addTypingIndicator() {
    var welcome = chatMessages.querySelector('.welcome-message');
    if (welcome) welcome.remove();
    var div = document.createElement('div');
    div.className = 'message assistant';
    div.id = 'typingMsg';
    div.innerHTML = '<div class="msg-avatar">\u{1f916}</div>' +
        '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    chatMessages.appendChild(div);
    smartScroll();
}

function removeTypingIndicator() {
    var el = document.getElementById('typingMsg');
    if (el) el.remove();
}

// ===== Markdown Renderer =====
function formatMarkdown(text) {
    if (!text) return '';
    text = text.trim().replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    text = text.replace(/^#{1,6}\s+/gm, '');
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    var parts = text.split(/\n\n+/);
    var result = [];
    var olBuffer = [];  // 缓存连续的编号段落，合并为一个 <ol>
    function flushOL() {
        if (olBuffer.length > 0) {
            var items = [];
            for (var k = 0; k < olBuffer.length; k++) {
                var lines = olBuffer[k].split('\n');
                for (var j = 0; j < lines.length; j++) {
                    items.push('<li>' + lines[j].replace(/^\d+\.\s*/, '') + '</li>');
                }
            }
            result.push('<ol>' + items.join('') + '</ol>');
            olBuffer = [];
        }
    }
    for (var i = 0; i < parts.length; i++) {
        var p = parts[i].trim();
        if (!p) { flushOL(); continue; }
        if (/^---$/.test(p)) { flushOL(); result.push('<hr>'); continue; }
        if (/^> /.test(p)) { flushOL(); result.push('<blockquote>' + p.replace(/^> /gm, '') + '</blockquote>'); continue; }
        if (/^- .+/.test(p)) {
            flushOL();
            result.push('<ul>' + p.split('\n').map(function(l) { return '<li>' + l.replace(/^- /, '') + '</li>'; }).join('') + '</ul>');
            continue;
        }
        if (/^\d+\. .+/.test(p)) {
            olBuffer.push(p);
            continue;
        }
        flushOL();
        p = p.replace(/\n/g, '<br>');
        result.push('<p>' + p + '</p>');
    }
    flushOL();  // 末尾编号列表
    return result.join('');
}

// ===== Failed Request Retry Queue =====
function _qKey() { return 'tradeMasterFailedQueue'; }

function getFailedQueue() {
    try { return JSON.parse(localStorage.getItem(_qKey()) || '[]'); }
    catch(e) { return []; }
}

function addToRetryQueue(question) {
    var q = getFailedQueue();
    q.push({question: question, date: new Date().toLocaleString('zh-CN'), timestamp: Date.now()});
    if (q.length > 20) q = q.slice(-20); // 最多保留20条
    localStorage.setItem(_qKey(), JSON.stringify(q));
    updateRetryBadge();
}

function removeFromRetryQueue(index) {
    var q = getFailedQueue();
    q.splice(index, 1);
    localStorage.setItem(_qKey(), JSON.stringify(q));
    updateRetryBadge();
}

function updateRetryBadge() {
    var badge = document.getElementById('retryBadge');
    if (!badge) return;
    var count = getFailedQueue().length;
    badge.textContent = count;
    badge.style.display = count > 0 ? 'inline-block' : 'none';
}

function showRetryQueueMsg() {
    var q = getFailedQueue();
    if (q.length === 0) return;
    var msg = '📋 重试队列中有 ' + q.length + ' 条待发送问题（API恢复后自动重试）：';
    q.forEach(function(item, i) {
        msg += '\n' + (i+1) + '. [' + item.date + '] ' + item.question.substring(0, 60);
    });
    addMessage('assistant', msg);
}

// Auto-retry when API recovers
var _retryTimer = null;
var _lastApiSuccess = Date.now();

function markApiSuccess() {
    _lastApiSuccess = Date.now();
    // API恢复正常，检查重试队列
    setTimeout(function() { processRetryQueue(); }, 2000);
}

function markApiFailed() {
    // API失败后，启动定时检查
    if (_retryTimer) return;
    _retryTimer = setInterval(function() {
        if (getFailedQueue().length === 0) { clearInterval(_retryTimer); _retryTimer = null; return; }
        // 尝试 ping health 端点
        fetch('/api/health').then(function(r){return r.json()}).then(function(d){
            if (d.status === 'ok' && getFailedQueue().length > 0) {
                clearInterval(_retryTimer); _retryTimer = null;
                processRetryQueue();
            }
        }).catch(function(){});
    }, 30000); // 每30秒检查一次
}

async function processRetryQueue() {
    var q = getFailedQueue();
    if (q.length === 0 || isLoading) return;
    addMessage('assistant', '🔄 API已恢复，正在重试 ' + q.length + ' 条待发送问题...');
    // 逐条重试
    for (var i = q.length - 1; i >= 0; i--) {
        var item = q[i];
        var datedQuestion = '以下问题于 ' + item.date + ' 提出，请回答：' + item.question;
        try {
            await sendMessageStream(datedQuestion);
            removeFromRetryQueue(i);
        } catch(e) {
            // 仍然失败，停止重试
            addMessage('assistant', '⚠️ 第' + (i+1) + '条问题重试失败，剩余 ' + (i+1) + ' 条待重试。');
            break;
        }
    }
    updateRetryBadge();
}

// ===== Streaming Chat =====
async function sendMessage() {
    var message = chatInput.value.trim();
    if (!message || isLoading) return;
    isLoading = true;
    btnSend.disabled = true;
    chatInput.value = '';
    chatInput.style.height = 'auto';
    addMessage('user', message);
    scrollToBottom();  // 滚动到最新消息
    addTypingIndicator();
    sessionStorage.setItem('lastQuestion', message);
    // 保存搜索偏好（买家搜索/展会/汇率等关键词）
    if (/搜索|买家|buyer|展会|汇率|开发信|询盘|进口商|分销商/.test(message)) {
        saveSearchPreference(message);
    }
    try {
        await sendMessageStream(message);
    } catch(e) {
        removeTypingIndicator();
        try { await sendMessageFallback(message); }
        catch(e2) {
            removeTypingIndicator();
            // 加入重试队列
            addToRetryQueue(message);
            addMessage('assistant', '❌ API暂时不可用，问题已加入重试队列。\n\n📋 问题：「' + message.substring(0, 80) + '」\n⏰ 提问时间：' + new Date().toLocaleString('zh-CN') + '\n🔄 系统将在API恢复后自动重试，也可稍后手动重新发送。');
            markApiFailed();
        }
    } finally {
        isLoading = false;
        btnSend.disabled = false;
        chatInput.focus();
    }
}

async function sendMessageFallback(message) {
    var resp = await fetch('/api/chat', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({message: message, session_id: currentUser ? currentUser.email : 'default', user_email: currentUser ? currentUser.email : ''})
    });
    var data = await resp.json();
    if (data.error) { addMessage('assistant', '❌ ' + data.error); throw new Error(data.error); }
    addMessage('assistant', data.reply, data.tool_calls);
    markApiSuccess();
}

async function sendMessageStream(message) {
    var controller = new AbortController();
    var timeoutId = setTimeout(function() { controller.abort(); }, 30000);

    var resp = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({message: message, session_id: currentUser ? currentUser.email : 'default', user_email: currentUser ? currentUser.email : ''}),
        signal: controller.signal
    });
    if (!resp.ok) { clearTimeout(timeoutId); throw new Error('HTTP ' + resp.status); }

    removeTypingIndicator();
    var msgDiv = createStreamMessage();
    var fullText = '';
    var toolCalls = [];
    var lastTc = null;
    var tracker = msgDiv.querySelector('.progress-tracker');

    var reader = resp.body.getReader();
    var decoder = new TextDecoder();
    var buffer = '';

    try {
        while (true) {
            var result = await reader.read();
            clearTimeout(timeoutId);
            if (result.done) break;
            buffer += decoder.decode(result.value, {stream: true});
            var lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (var i = 0; i < lines.length; i++) {
                var line = lines[i];
                if (!line.startsWith('data: ')) continue;
                try { var event = JSON.parse(line.slice(6)); }
                catch(e) { continue; }

                switch (event.type) {
                    case 'agent':
                        // Show which agent is active
                        var agentBadge = msgDiv.querySelector('.agent-badge');
                        if (!agentBadge) {
                            agentBadge = document.createElement('div');
                            agentBadge.className = 'agent-badge';
                            msgDiv.querySelector('.msg-content').insertBefore(agentBadge, msgDiv.querySelector('.stream-text'));
                        }
                        agentBadge.textContent = event.agent;
                        agentBadge.style.display = 'block';
                        break;
                    case 'thinking':
                        break;
                    case 'text':
                        fullText += event.content;
                        updateStreamText(msgDiv, fullText);
                        break;
                    case 'tool_call':
                        lastTc = {tool: event.tool, label: event.label, args: event.args, step: event.step, result: null};
                        toolCalls.push(lastTc);
                        addProgressStep(tracker, event.label || event.tool, event.detail, event.tool + '_' + event.step);
                        break;
                    case 'tool_result':
                        var tc = lastTc;
                        for (var j = toolCalls.length - 1; j >= 0; j--) {
                            if (toolCalls[j].tool === event.tool && !toolCalls[j].result) { tc = toolCalls[j]; break; }
                        }
                        if (tc) { tc.result = event.result; tc.summary = event.summary; }
                        markProgressDone(tracker, event.tool + '_' + event.step, event.summary);
                        lastTc = null;
                        break;
                    case 'evaluation':
                        renderEvaluationCard(msgDiv, event, fullText);
                        break;
                    case 'text_improved':
                        fullText += event.content;
                        updateStreamText(msgDiv, fullText);
                        break;
                    case 'error':
                        fullText += '\n' + event.message;
                        updateStreamText(msgDiv, fullText);
                        break;
                    case 'done':
                        break;
                }
            }
            timeoutId = setTimeout(function() { controller.abort(); }, 30000);
        }
    } catch(e) {
        if (e.name === 'AbortError' && !fullText) fullText = t('timeoutError');
        else if (e.name !== 'AbortError') throw e;
    }
    clearTimeout(timeoutId);
    finalizeStreamMessage(msgDiv, fullText, toolCalls);
}

function createStreamMessage() {
    var welcome = chatMessages.querySelector('.welcome-message');
    if (welcome) welcome.remove();
    var div = document.createElement('div');
    div.className = 'message assistant';
    div.id = 'streamMsg';
    div.innerHTML = '<div class="msg-avatar">\u{1f916}</div>' +
        '<div class="msg-content streaming">' +
            '<div class="progress-tracker" style="display:none"></div>' +
            '<div class="stream-text"></div>' +
            '<span class="stream-spinner"></span>' +
        '</div>';
    chatMessages.appendChild(div);
    return div;
}

function addProgressStep(tracker, label, detail, stepId) {
    if (!tracker) return;
    tracker.style.display = 'block';
    var sid = stepId.replace(/[^a-zA-Z0-9]/g, '_');
    var existing = document.getElementById('ps_' + sid);
    if (existing) {
        existing.className = 'progress-step working';
        existing.querySelector('.ps-status').innerHTML = '<span class="mini-spinner"></span> ' + (detail || 'Working...');
        return;
    }
    var el = document.createElement('div');
    el.className = 'progress-step working';
    el.id = 'ps_' + sid;
    el.innerHTML = '<div class="ps-icon">...</div>' +
        '<div class="ps-content"><div class="ps-label">' + label + '</div><div class="ps-summary"></div></div>' +
        '<div class="ps-status"><span class="mini-spinner"></span> ' + (detail || 'Working...') + '</div>';
    tracker.appendChild(el);
    smartScroll();
}

function markProgressDone(tracker, stepId, summary) {
    var el = document.getElementById('ps_' + stepId.replace(/[^a-zA-Z0-9]/g, '_'));
    if (!el) return;
    el.className = 'progress-step done';
    el.querySelector('.ps-icon').textContent = 'OK';
    el.querySelector('.ps-status').textContent = t('allDone');
    if (summary) el.querySelector('.ps-summary').textContent = summary;
    smartScroll();
}

function markAllProgressDone(tracker) {
    if (!tracker) return;
    tracker.querySelectorAll('.progress-step.working').forEach(function(el) {
        el.className = 'progress-step done';
        el.querySelector('.ps-icon').textContent = 'OK';
        el.querySelector('.ps-status').textContent = t('allDone');
    });
    if (!tracker.querySelector('.progress-all-done')) {
        var footer = document.createElement('div');
        footer.className = 'progress-all-done';
        footer.textContent = t('allDone');
        tracker.appendChild(footer);
    }
}

function smartScroll() {
    // Auto-scroll to bottom (always, so user sees latest Q&A)
    var el = chatMessages;
    el.scrollTop = el.scrollHeight;
}

function scrollToBottom() {
    // Force scroll — called when user sends a message
    var el = chatMessages;
    setTimeout(function() { el.scrollTop = el.scrollHeight; }, 100);
}

function updateStreamText(msgDiv, text) {
    var area = msgDiv.querySelector('.stream-text');
    if (area) area.innerHTML = formatMarkdown(text);
    smartScroll();
}

function addAnswerToolbar(msgDiv, text) {
    var content = msgDiv.querySelector('.msg-content');
    if (!content) return;

    var toolbar = document.createElement('div');
    toolbar.className = 'answer-toolbar';
    toolbar.style.cssText = 'display:flex;gap:6px;margin-top:10px;padding-top:8px;border-top:1px solid #f0f0f0;';

    // Copy button
    var copyBtn = document.createElement('button');
    copyBtn.textContent = t('copyAnswer');
    copyBtn.style.cssText = 'padding:4px 10px;border:1px solid #d0e2f2;background:#fff;color:#6989a8;border-radius:6px;font-size:11px;cursor:pointer;font-family:inherit;';
    copyBtn.onclick = function() {
        var plainText = text.replace(/<[^>]*>/g, '').replace(/&[^;]+;/g, '');
        if (navigator.clipboard) {
            navigator.clipboard.writeText(plainText).then(function() {
                copyBtn.textContent = t('copiedAnswer'); copyBtn.style.color = '#5bba8a';
                setTimeout(function() { copyBtn.textContent = t('copyAnswer'); copyBtn.style.color = '#6989a8'; }, 2000);
            });
        }
    };
    toolbar.appendChild(copyBtn);

    // Regenerate button
    var redoBtn = document.createElement('button');
    redoBtn.textContent = t('regenerate');
    redoBtn.style.cssText = 'padding:4px 10px;border:1px solid #d0e2f2;background:#fff;color:#6989a8;border-radius:6px;font-size:11px;cursor:pointer;font-family:inherit;';
    redoBtn.onclick = function() {
        var q = sessionStorage.getItem('lastQuestion');
        if (q) { chatInput.value = q; sendMessage(); }
    };
    toolbar.appendChild(redoBtn);

    content.appendChild(toolbar);
}

function finalizeStreamMessage(msgDiv, text, toolCalls) {
    // 标记 API 成功
    markApiSuccess();
    // 停止旋转器
    var content = msgDiv.querySelector('.msg-content');
    if (content) { content.classList.remove('streaming'); content.classList.add('stream-done'); }
    markAllProgressDone(msgDiv.querySelector('.progress-tracker'));
    updateStreamText(msgDiv, text);
    appendContextActions(msgDiv.querySelector('.msg-content'), text, toolCalls);
    addAnswerToolbar(msgDiv, text);

    // Show inline email composer for send_email results
    if (toolCalls) {
        toolCalls.forEach(function(tc) {
            if (tc.tool === 'send_email' && tc.result && tc.result.success) {
                renderEmailActions(msgDiv.querySelector('.msg-content'), tc.result);
            }
        });
    }

    // Evaluation disabled - removed autoEvaluate call

    msgDiv.removeAttribute('id');
    smartScroll();
}

function autoEvaluate(msgDiv, question, answer) {
    fetch('/api/evaluate', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({question: question, answer: answer})
    }).then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.success && data.evaluation) {
            renderEvaluationCard(msgDiv, data.evaluation, answer);
        }
    }).catch(function() {});
}

// ===== Context Actions =====
function appendContextActions(container, text, toolCalls) {
    var actions = [];
    var added = {};

    function add(label, action) {
        if (!added[label]) { added[label] = true; actions.push({label: label, action: action}); }
    }

    // Detect companies from bold text
    var companies = [];
    var m = text.match(/\*\*([^*]{2,40})\*\*/g);
    if (m) {
        m.forEach(function(b) {
            var name = b.replace(/\*\*/g, '').trim();
            if (!/^[一-鿿]{1,3}$/.test(name) && !/进口|分销|采购|建议|市场|类别|类型|领域|开发信/.test(name)) {
                companies.push(name);
            }
        });
    }

    // Detect keyword from tool calls
    var keyword = '';
    if (toolCalls) {
        toolCalls.forEach(function(tc) {
            if (tc.args && tc.args.keyword) keyword = tc.args.keyword;
            if (tc.args && tc.args.currency) keyword = tc.args.currency;
        });
    }

    if (companies.length > 0) {
        add('📊 分析 ' + companies[0], '分析一下 ' + companies[0]);
        add('✉️ 给 ' + companies[0] + ' 写开发信', '给 ' + companies[0] + ' 写一封开发信');
    }
    if (keyword) add('🔍 更多 ' + keyword + ' 买家', '帮我搜索更多 ' + keyword + ' 的买家');
    if (/邮件|开发信|email/i.test(text)) add('📧 发送邮件', '帮我发送这封邮件');
    if (actions.length === 0) {
        add('🔍 搜索买家', '帮我搜索相关产品的买家');
        add('💱 查询汇率', '美元兑人民币汇率');
    }
    // Add "加入待联系" button for buyer results
    if (companies.length > 0) {
        actions.push({label: '📋 加入待联系', action: '__add_to_contacts__'});
    }
    if (actions.length > 5) actions = actions.slice(0, 5);

    var div = document.createElement('div');
    div.className = 'context-actions';
    actions.forEach(function(a) {
        var btn = document.createElement('button');
        btn.className = 'context-action-btn';
        btn.textContent = a.label;
        btn.addEventListener('click', function() { sendQuickAction(a.action); });
        div.appendChild(btn);
    });
    container.appendChild(div);
    smartScroll();
}

// ===== Email Actions =====
function renderEvaluationCard(msgDiv, evalData, fullText) {
    var content = msgDiv.querySelector('.msg-content');
    if (!content) return;

    // Remove existing eval card if any
    var existing = content.querySelector('.eval-card');
    if (existing) existing.remove();

    var scores = evalData.scores || {};
    var strengths = evalData.strengths || [];
    var weaknesses = evalData.weaknesses || [];
    var suggestion = evalData.suggestion || '';
    var error = evalData.error || '';
    var overall = parseFloat(scores.overall) || 5;

    if (error) {
        var errDiv = document.createElement('div');
        errDiv.className = 'eval-error';
        errDiv.textContent = error;
        content.appendChild(errDiv);
        return;
    }

    // Build score bars
    var dims = [
        {key: 'relevance', label: '相关'},
        {key: 'accuracy', label: '准确'},
        {key: 'completeness', label: '完整'},
        {key: 'practicality', label: '实用'},
        {key: 'language', label: '语言'},
        {key: 'overall', label: '综合'},
    ];

    var scoreBars = '';
    dims.forEach(function(d) {
        var val = parseFloat(scores[d.key]) || 0;
        var w = Math.round(val * 10);
        var cls = val >= 8 ? 'hi' : val >= 6 ? 'mid' : 'low';
        scoreBars += '<div class="eval-score-row">' +
            '<span class="eval-score-label">' + d.label + '</span>' +
            '<div class="eval-score-bar"><div class="eval-score-fill ' + cls + '" style="width:' + w + '%"></div></div>' +
            '<span class="eval-score-val">' + val.toFixed(1) + '</span>' +
            '</div>';
    });

    var badgeClass = overall >= 8 ? 'good' : overall >= 6 ? 'ok' : 'poor';
    var badgeText = overall >= 8 ? t('evalGood') : overall >= 6 ? t('evalOk') : t('evalPoor');

    // Build strengths/weaknesses lists
    var strList = strengths.length > 0
        ? '<ul>' + strengths.map(function(s) { return '<li>' + s + '</li>'; }).join('') + '</ul>'
        : '<p style="color:#a3bfd8">-</p>';
    var weakList = weaknesses.length > 0
        ? '<ul>' + weaknesses.map(function(w) { return '<li>' + w + '</li>'; }).join('') + '</ul>'
        : '<p style="color:#a3bfd8">-</p>';

    var html = '<div class="eval-card">' +
        '<div class="eval-header">' +
            '<span class="eval-title">' + t('evalTitle') + '</span>' +
            '<span class="eval-badge ' + badgeClass + '">' + badgeText + ' ' + overall.toFixed(1) + '</span>' +
        '</div>' +
        '<div class="eval-body">' +
            '<div class="eval-scores">' + scoreBars + '</div>' +
            '<div class="eval-lists">' +
                '<div class="eval-strengths"><h4>' + t('evalStrengths') + '</h4>' + strList + '</div>' +
                '<div class="eval-weaknesses"><h4>' + t('evalWeaknesses') + '</h4>' + weakList + '</div>' +
            '</div>';

    if (suggestion) {
        html += '<div class="eval-suggestion"><strong>' + t('evalSuggestion') + ':</strong> ' + suggestion + '</div>';
    }

    html += '<div class="eval-actions">' +
        '<button class="eval-keep-btn" onclick="triggerKimiEval(this)" style="background:#6c5ce7;color:#fff;border-color:#6c5ce7">🤖 Kimi 深度评价</button>';
    if (overall < 8.0) {
        html += '<button class="eval-keep-btn" onclick="triggerImprove(this)" style="background:#5ba0d9;color:#fff;border-color:#5ba0d9;margin-left:6px">' + t('evalImprove') + '</button>';
    }
    html += '</div>';

    html += '</div></div>';

    // Insert before stream-text content area
    var textArea = content.querySelector('.stream-text');
    if (textArea) {
        textArea.insertAdjacentHTML('beforebegin', html);
    } else {
        content.insertAdjacentHTML('beforeend', html);
    }

    smartScroll();
}

function keepOriginalAnswer() {} // deprecated

function triggerKimiEval(btn) {
    btn.textContent = '🤖 Kimi 评价中...'; btn.disabled = true;
    var question = sessionStorage.getItem('lastQuestion') || '';
    var msgEl = btn.closest('.message');
    var textArea = msgEl ? msgEl.querySelector('.stream-text') : null;
    var answer = textArea ? textArea.textContent : '';

    if (!question || !answer) { btn.textContent = 'Error'; btn.disabled = false; return; }

    // Step 1: Kimi 深度评价
    fetch('/api/evaluate/kimi', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({question: question, answer: answer})
    }).then(function(r) { return r.json(); })
    .then(function(data) {
        if (!data.success || !data.evaluation || data.evaluation.error) {
            btn.textContent = 'Kimi 不可用';
            setTimeout(function() { btn.textContent = '🤖 Kimi 深度评价'; btn.disabled = false; }, 3000);
            return;
        }

        // Remove existing eval card, render Kimi card
        var existing = msgEl.querySelector('.eval-card');
        if (existing) existing.remove();
        renderKimiEvalCard(msgEl, data.evaluation);

        // Step 2: 如果 Kimi 建议改进 (overall < 8)，自动触发改进
        var evalData = data.evaluation;
        var overall = parseFloat((evalData.scores || {}).overall || 0);
        if (evalData.need_improve || overall < 8.0) {
            // 更新按钮状态
            btn.textContent = '🤖 自动改进中...';

            // 用 Kimi 的建议作为 feedback 传给改进端点
            var kimiScores = evalData.scores || {};
            var kimiOverall = parseFloat(kimiScores.overall || 0);
            var kimiSuggestion = evalData.suggestion || '';
            var kimiStrengths = (evalData.strengths || []).join('; ');
            var kimiWeaknesses = (evalData.weaknesses || []).join('; ');
            var feedback = 'Kimi 深度评价结果（满分10分）：\\n' +
                '综合评分: ' + kimiOverall.toFixed(1) + '/10\\n' +
                '相关度: ' + (kimiScores.relevance || '?') + ' | 准确度: ' + (kimiScores.accuracy || '?') + '\\n' +
                '完整性: ' + (kimiScores.completeness || '?') + ' | 实用性: ' + (kimiScores.practicality || '?') + '\\n' +
                '语言质量: ' + (kimiScores.language || '?') + '\\n' +
                '优点: ' + kimiStrengths + '\\n' +
                '缺点: ' + kimiWeaknesses + '\\n' +
                '改进建议: ' + kimiSuggestion + '\\n\\n' +
                '请基于以上 Kimi 评价反馈，重新回答用户的原始问题：' + question;

            fetch('/api/evaluate/improve', {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    question: question, answer: answer,
                    session_id: currentUser ? currentUser.email : 'default',
                    user_email: currentUser ? currentUser.email : '',
                    kimi_feedback: feedback
                })
            }).then(function(r) {
                if (!r.ok) { btn.textContent = '🤖 改进完成'; btn.disabled = false; return; }
                var reader = r.body.getReader();
                var decoder = new TextDecoder(); var buffer = '';
                var msgContent = msgEl.querySelector('.msg-content');

                // Create improved section
                var divider = document.createElement('div');
                divider.className = 'improved-divider';
                divider.innerHTML = '<span>🤖 Kimi 改进版回答</span>';
                msgContent.appendChild(divider);

                var improvedArea = document.createElement('div');
                improvedArea.className = 'stream-text-kimi';
                msgContent.appendChild(improvedArea);

                function readKimi() {
                    reader.read().then(function(result) {
                        if (result.done) { btn.textContent = '🤖 改进完成'; btn.disabled = false; return; }
                        buffer += decoder.decode(result.value, {stream: true});
                        var lines = buffer.split('\\n'); buffer = lines.pop() || '';
                        lines.forEach(function(line) {
                            if (!line.startsWith('data: ')) return;
                            try { var e = JSON.parse(line.slice(6)); } catch(err) { return; }
                            if (e.type === 'text_improved') {
                                improvedArea.innerHTML = formatMarkdown((improvedArea.textContent || '') + e.content);
                                smartScroll();
                            }
                        });
                        readKimi();
                    }).catch(function() { btn.textContent = '🤖 改进完成'; btn.disabled = false; });
                }
                readKimi();
            }).catch(function() {
                btn.textContent = '🤖 改进失败'; btn.disabled = false;
            });
        } else {
            btn.textContent = '🤖 Kimi 评价完成';
            btn.disabled = false;
        }
    }).catch(function() {
        btn.textContent = '🤖 重试'; btn.disabled = false;
    });
}

function renderKimiEvalCard(msgEl, evalData) {
    var content = msgEl.querySelector('.msg-content');
    if (!content) return;

    var error = evalData.error || '';
    var scores = evalData.scores || {};
    var strengths = evalData.strengths || [];
    var weaknesses = evalData.weaknesses || [];
    var suggestion = evalData.suggestion || '';
    var overall = parseFloat(scores.overall) || 5;

    if (error) {
        var errDiv = document.createElement('div');
        errDiv.className = 'eval-error';
        errDiv.textContent = 'Kimi: ' + error;
        content.appendChild(errDiv);
        return;
    }

    var dims = [
        {key: 'relevance', label: '相关度'}, {key: 'accuracy', label: '准确度'},
        {key: 'completeness', label: '完整性'}, {key: 'practicality', label: '实用性'},
        {key: 'language', label: '语言'}, {key: 'overall', label: '综合'}
    ];

    var scoreBars = '';
    dims.forEach(function(d) {
        var val = parseFloat(scores[d.key]) || 0;
        var w = Math.round(val * 10);
        var cls = val >= 8 ? 'hi' : val >= 6 ? 'mid' : 'low';
        scoreBars += '<div class=\"eval-score-row\"><span class=\"eval-score-label\">' + d.label + '</span>' +
            '<div class=\"eval-score-bar\"><div class=\"eval-score-fill ' + cls + '\" style=\"width:' + w + '%\"></div></div>' +
            '<span class=\"eval-score-val\">' + val.toFixed(1) + '</span></div>';
    });

    var badgeClass = overall >= 8 ? 'good' : overall >= 6 ? 'ok' : 'poor';
    var badgeText = overall >= 8 ? 'Good' : overall >= 6 ? 'OK' : 'Poor';
    var strList = strengths.length > 0 ? '<ul>' + strengths.map(function(s){return '<li>'+s+'</li>';}).join('') + '</ul>' : '<p style=\"color:#a3bfd8\">-</p>';
    var weakList = weaknesses.length > 0 ? '<ul>' + weaknesses.map(function(w){return '<li>'+w+'</li>';}).join('') + '</ul>' : '<p style=\"color:#a3bfd8\">-</p>';

    var html = '<div class=\"eval-card\" style=\"border-color:#6c5ce7\">' +
        '<div class=\"eval-header\" style=\"background:#f5f3ff\">' +
            '<span class=\"eval-title\">🤖 Kimi 深度评价</span>' +
            '<span class=\"eval-badge ' + badgeClass + '\">' + badgeText + ' ' + overall.toFixed(1) + '</span>' +
        '</div><div class=\"eval-body\">' +
            '<div class=\"eval-scores\">' + scoreBars + '</div>' +
            '<div class=\"eval-lists\">' +
                '<div class=\"eval-strengths\"><h4>✅ Strengths</h4>' + strList + '</div>' +
                '<div class=\"eval-weaknesses\"><h4>⚠️ Weaknesses</h4>' + weakList + '</div>' +
            '</div>';
    if (suggestion) {
        html += '<div class=\"eval-suggestion\"><strong>💡 Suggestion:</strong> ' + suggestion + '</div>';
    }
    html += '</div></div>';

    var textArea = content.querySelector('.stream-text');
    if (textArea) {
        textArea.insertAdjacentHTML('beforebegin', html);
    } else {
        content.insertAdjacentHTML('beforeend', html);
    }
    smartScroll();
}

function triggerImprove(btn) {
    btn.textContent = t('evalImproving'); btn.disabled = true;
    var question = sessionStorage.getItem('lastQuestion') || '';
    var msgEl = btn.closest('.message');
    var textArea = msgEl ? msgEl.querySelector('.stream-text') : null;
    var answer = textArea ? textArea.textContent : '';

    if (!question || !answer) { btn.textContent = t('networkError'); return; }

    fetch('/api/evaluate/improve', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
            question: question, answer: answer,
            session_id: currentUser ? currentUser.email : 'default',
            user_email: currentUser ? currentUser.email : ''
        })
    }).then(function(r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        var reader = r.body.getReader();
        var decoder = new TextDecoder(); var buffer = '';
        var improvedText = '';
        var msgContent = msgEl.querySelector('.msg-content');
        if (!msgContent) return;

        // Create improved section
        var divider = document.createElement('div');
        divider.className = 'improved-divider';
        divider.innerHTML = '<span>GAN Improved Answer</span>';
        msgContent.appendChild(divider);

        var improvedArea = document.createElement('div');
        improvedArea.className = 'stream-text-improved';
        msgContent.appendChild(improvedArea);

        function read() {
            reader.read().then(function(result) {
                if (result.done) { btn.textContent = t('evalImproved'); return; }
                buffer += decoder.decode(result.value, {stream: true});
                var lines = buffer.split('\n'); buffer = lines.pop() || '';
                lines.forEach(function(line) {
                    if (!line.startsWith('data: ')) return;
                    try { var e = JSON.parse(line.slice(6)); } catch(err) { return; }
                    if (e.type === 'evaluation') {
                        var card = msgContent.querySelector('.eval-card');
                        if (card) card.remove();
                        renderEvaluationCard(msgEl, e, answer);
                    }
                    if (e.type === 'text_improved') {
                        improvedText += e.content;
                        improvedArea.innerHTML = formatMarkdown(improvedText);
                        smartScroll();
                    }
                });
                read();
            }).catch(function() { btn.textContent = t('allDone'); });
        }
        read();
    }).catch(function(e) {
        btn.textContent = t('evalRetry');
        btn.disabled = false;
    });
}

function renderEmailActions(container, info) {
    var div = document.createElement('div');
    div.className = 'email-actions';

    var isVerified = info.email_verified !== false;
    var verifiedBanner = isVerified ? '' :
        '<div class="ea-warning">' +
            '<strong>⚠️ 未验证邮箱</strong> — 此邮箱为基于域名推测，退信风险高。' +
            '建议先通过 <a href="https://hunter.io/email-verifier" target="_blank">Hunter.io</a> / ' +
            '<a href="https://snov.io/email-verifier" target="_blank">Snov.io</a> 验证后再发送。' +
        '</div>';

    // Header: title + verification status + To/Subject summary
    div.innerHTML = '<div class="ea-title">' +
            (isVerified ? '📧 邮件内容' : '📧 邮件内容 ⚠️未验证') +
        '</div>' +
        verifiedBanner +
        '<div class="ea-info">' +
            '<span>📨 <b>' + (info.to_email || '') + '</b></span>' +
            '<span>📌 <b>' + (info.subject || '') + '</b></span>' +
        '</div>' +
        '<div class="ea-field"><label>收件人</label><input class="ea-to" value="' + (info.to_email || '') + '"></div>' +
        '<div class="ea-field"><label>主题</label><input class="ea-subject" value="' + (info.subject || '') + '"></div>' +
        '<div class="ea-field"><label>邮件正文（可直接编辑）</label><textarea class="ea-body">' + (info.body || '') + '</textarea></div>' +
        '<div class="ea-row">' +
            '<button class="ea-copy">📋 复制到剪贴板</button>' +
            '<button class="ea-smtp-send">📨 SMTP直发</button>' +
            '<button class="ea-sent-manual">✋ 我已手动发送</button>' +
        '</div>' +
        '<div class="ea-status" style="display:none"></div>' +
        '<div class="ea-followup-hint" style="display:none"></div>';

    // Check SMTP config and hide button if not configured
    var smtpBtn = div.querySelector('.ea-smtp-send');
    fetch('/api/email/smtp_settings').then(function(r){return r.json()}).then(function(d){
        if (!d.success || !d.config || !d.config.has_password) {
            smtpBtn.style.display = 'none';
        }
    }).catch(function(){ smtpBtn.style.display = 'none'; });

    // Copy button
    div.querySelector('.ea-copy').addEventListener('click', function() {
        var to = div.querySelector('.ea-to').value;
        var subject = div.querySelector('.ea-subject').value;
        var body = div.querySelector('.ea-body').value;
        var text = 'To: ' + to + '\nSubject: ' + subject + '\n\n' + body;
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(function() {
                this.textContent = '✅ 已复制';
                this.style.background = '#5bba8a';
                setTimeout(function() { this.textContent = '📋 复制到剪贴板'; this.style.background = '#5ba0d9'; }.bind(this), 2000);
            }.bind(this));
        } else {
            var ta = document.createElement('textarea');
            ta.value = text; ta.style.position = 'fixed'; ta.style.left = '-9999px';
            document.body.appendChild(ta); ta.select();
            document.execCommand('copy'); document.body.removeChild(ta);
            this.textContent = '✅ 已复制';
            this.style.background = '#5bba8a';
            setTimeout(function() { this.textContent = '📋 复制到剪贴板'; this.style.background = '#5ba0d9'; }.bind(this), 2000);
        }
    });

    // SMTP Send button
    div.querySelector('.ea-smtp-send').addEventListener('click', function() {
        var btn = this;
        var statusEl = div.querySelector('.ea-status');
        var to = div.querySelector('.ea-to').value;
        var subject = div.querySelector('.ea-subject').value;
        var body = div.querySelector('.ea-body').value;

        if (!to || to.indexOf('@') < 0) {
            statusEl.style.display = 'block'; statusEl.style.color = '#e87070';
            statusEl.textContent = '请输入有效的收件人邮箱'; return;
        }

        btn.textContent = '⏳ 发送中...'; btn.disabled = true;
        statusEl.style.display = 'block'; statusEl.style.color = '#86a8c8';
        statusEl.textContent = '正在通过SMTP发送...';

        fetch('/api/email/smtp_send', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                to_email: to, subject: subject, body: body,
                to_name: (info.to_name || ''), user_email: currentUser ? currentUser.email : ''
            })
        }).then(function(r) { return r.json(); })
        .then(function(d) {
            if (d.success) {
                btn.textContent = '✅ 已发送'; btn.disabled = false;
                btn.style.background = '#5bba8a';
                statusEl.style.display = 'block'; statusEl.style.color = '#5bba8a';
                var msg = '✅ ' + (d.message || '发送成功');
                if (d.delivered === null) {
                    msg += ' ⚠️ QQ邮箱已接受，但最终送达需以收件方确认为准。如退信会发到你的QQ邮箱。';
                }
                statusEl.textContent = msg;
                // 显示跟进提示
                showFollowupHint(div, to);
                if (typeof loadEmailBox === 'function') setTimeout(loadEmailBox, 500);
            } else {
                btn.textContent = '📨 重试'; btn.disabled = false;
                statusEl.style.display = 'block'; statusEl.style.color = '#e87070';
                statusEl.textContent = '❌ ' + (d.error || '发送失败');
                if (d.hint) statusEl.textContent += ' — ' + d.hint;
            }
        }).catch(function(e) {
            btn.textContent = '📨 重试'; btn.disabled = false;
            statusEl.style.display = 'block'; statusEl.style.color = '#e87070';
            statusEl.textContent = '❌ 网络错误，请重试';
        });
    });

    // Manual sent button
    div.querySelector('.ea-sent-manual').addEventListener('click', function() {
        if (!currentUser) { this.textContent = '⚠️ 请先登录'; return; }
        var btn = this;
        var to = div.querySelector('.ea-to').value;
        var subject = div.querySelector('.ea-subject').value;
        var body = div.querySelector('.ea-body').value;
        var statusEl = div.querySelector('.ea-status');

        btn.textContent = '⏳ 记录中...'; btn.disabled = true;

        fetch('/api/send_email', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                to_email: to, subject: subject, body: body,
                to_name: (info.to_name || ''), user_email: currentUser.email
            })
        }).then(function(r) { return r.json(); })
        .then(function(d) {
            if (d.success) {
                btn.textContent = '✅ 已记录'; btn.disabled = false;
                btn.style.background = '#5bba8a';
                statusEl.style.display = 'block'; statusEl.style.color = '#5bba8a';
                statusEl.textContent = '✅ 发送已记录 | 追踪ID: ' + (d.tracking_id || 'N/A');
                showFollowupHint(div, to);
                if (typeof loadEmailBox === 'function') setTimeout(loadEmailBox, 800);
            } else {
                btn.textContent = '✋ 我已手动发送'; btn.disabled = false;
                statusEl.style.display = 'block'; statusEl.style.color = '#e87070';
                statusEl.textContent = '❌ 记录失败，请重试';
            }
        }).catch(function(e) {
            btn.textContent = '✋ 我已手动发送'; btn.disabled = false;
            statusEl.style.display = 'block'; statusEl.style.color = '#e87070';
            statusEl.textContent = '❌ 网络错误，请重试';
        });
    });

    container.appendChild(div);
    smartScroll();
}

// ============================================================
// 客户跟进面板 (Contact Pipeline)
// ============================================================
var contactFilter = 'all';
var allContacts = [];

function toggleContactPanel() {
    var panel = document.getElementById('contactPanel');
    var isOpen = panel.classList.contains('open');
    if (isOpen) { panel.classList.remove('open'); return; }
    panel.classList.add('open');
    document.getElementById('emailPanel').classList.remove('open');
    loadContactBox();
}

function loadContactBox() {
    if (!currentUser) return;
    fetch('/api/contacts/list', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({user_email: currentUser.email, status: (contactFilter !== 'all' ? contactFilter : '')})
    }).then(function(r){return r.json()}).then(function(d){
        if (!d.success) return;
        allContacts = d.contacts;
        renderContactList(d.contacts);
        renderContactStats(d);
        document.getElementById('contactBadge').textContent = d.due_reminders || 0;
        if (d.due_reminders > 0) document.getElementById('contactBadge').classList.add('show');
        else document.getElementById('contactBadge').classList.remove('show');
    });
}

function renderContactStats(d) {
    if (!d.stats) return;
    document.getElementById('csTotal').textContent = d.stats.total || 0;
    document.getElementById('csPending').textContent = d.stats.pending || 0;
    document.getElementById('csContacted').textContent = d.stats.contacted || 0;
    document.getElementById('csReplied').textContent = d.stats.replied || 0;
    document.getElementById('csReminder').textContent = d.due_reminders || 0;
}

function renderContactList(contacts) {
    var list = document.getElementById('contactList');
    if (!contacts || contacts.length === 0) {
        list.innerHTML = '<div style="text-align:center;padding:12px;color:#a3bfd8;font-size:12px">暂无客户 — 搜索买家后可加入待联系</div>';
        return;
    }
    var html = '';
    contacts.forEach(function(c) {
        var statusLabel = {'pending':'待联系','contacted':'已联系','replied':'已回复','negotiating':'洽谈中','ordered':'已成交','closed':'已关闭','invalid':'无效'};
        var statusColor = {'pending':'#fff3e0','contacted':'#e3f2fd','replied':'#e8f5e9','negotiating':'#f3e5f5','ordered':'#e8f5e9','closed':'#f5f5f5','invalid':'#ffebee'};
        var methodIcon = {'email':'📧','linkedin':'💼','phone':'📞','whatsapp':'💬','tradeshow':'🎪','website_form':'🌐','other':'📌'};
        var isDue = (document.getElementById('contactBadge').classList.contains('show') && c.status === 'pending' && c.next_remind_at);
        html += '<div class="email-item' + (isDue?'':'') + '" style="' + (isDue?'border-left:3px solid #ff9800;':'') + '">' +
            '<span class="ei-status" style="background:' + (statusColor[c.status]||'#f5f5f5') + ';color:#555">' + (statusLabel[c.status]||c.status) + '</span>' +
            '<span class="ei-to">' + (c.company_name || 'Unknown') + '</span>' +
            '<span style="font-size:10px;color:#999">' + (methodIcon[c.contact_method]||'📌') + '</span>' +
            '<span style="font-size:10px;color:#999">' + (c.country||'') + '</span>' +
            '<span class="ei-date">' + (c.created_at||'').slice(0,10) + '</span>' +
            '<div class="ei-detail">' +
                (c.email ? '<div>📧 ' + c.email + '</div>' : '') +
                (c.website ? '<div>🌐 ' + c.website + '</div>' : '') +
                (c.contact_person ? '<div>👤 ' + c.contact_person + '</div>' : '') +
                (c.notes ? '<div>📝 ' + c.notes + '</div>' : '') +
                '<div class="ei-actions">' +
                    '<button class="ei-btn" onclick="updateContactStatus(' + c.id + ',\'contacted\')">✓ 已联系</button>' +
                    '<button class="ei-btn" onclick="updateContactStatus(' + c.id + ',\'replied\')">✓ 已回复</button>' +
                    '<button class="ei-btn" onclick="updateContactStatus(' + c.id + ',\'ordered\')">🎉 已成交</button>' +
                    '<button class="ei-btn" onclick="updateContactStatus(' + c.id + ',\'closed\')">✕ 关闭</button>' +
                    '<button class="ei-btn" style="color:#e87070" onclick="deleteContact(' + c.id + ')">🗑</button>' +
                '</div>' +
            '</div>' +
        '</div>';
    });
    list.innerHTML = html;
    // Click to expand
    list.querySelectorAll('.email-item').forEach(function(item){
        item.addEventListener('click', function(e){
            if (e.target.tagName === 'BUTTON') return;
            this.classList.toggle('expanded');
        });
    });
}

function updateContactStatus(cid, status) {
    if (!currentUser) return;
    fetch('/api/contacts/update', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({user_email: currentUser.email, contact_id: cid, status: status})
    }).then(function(r){return r.json()}).then(function(d){
        if (d.success) loadContactBox();
    });
}

function deleteContact(cid) {
    if (!currentUser || !confirm('确定删除该客户？')) return;
    fetch('/api/contacts/delete', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({user_email: currentUser.email, contact_id: cid})
    }).then(function(r){return r.json()}).then(function(d){
        if (d.success) loadContactBox();
    });
}

// Add buyer to contacts from agent response
function addBuyerToContacts(companyName, email, website, country, source) {
    if (!currentUser) { alert('请先登录'); return; }
    fetch('/api/contacts/add', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
            user_email: currentUser.email,
            company_name: companyName,
            email: email || '',
            website: website || '',
            country: country || '',
            source: source || 'Agent推荐',
            contact_method: email ? 'email' : 'linkedin',
            notes: email ? '' : '无邮箱，需通过LinkedIn或官网联系'
        })
    }).then(function(r){return r.json()}).then(function(d){
        if (d.success) {
            var badge = document.getElementById('contactBadge');
            badge.textContent = (parseInt(badge.textContent)||0) + 1;
            badge.classList.add('show');
            alert('✅ 已加入待联系列表');
        } else {
            alert('❌ ' + (d.error || '添加失败'));
        }
    });
}

// Contact panel filter tabs
document.addEventListener('DOMContentLoaded', function() {
    var contactTabs = document.querySelectorAll('#contactPanel .email-filter-tab');
    contactTabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            contactTabs.forEach(function(t){t.classList.remove('active')});
            this.classList.add('active');
            contactFilter = this.getAttribute('data-filter');
            loadContactBox();
        });
    });
});

// ===== Dashboard =====
function loadDashboard() {
    if (!currentUser) return;
    fetch('/api/dashboard', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({user_email: currentUser.email})
    }).then(function(r){return r.json()}).then(function(d){
        if (!d.success) return;
        renderDashboard(d);
    }).catch(function(){});
}

function renderDashboard(d) {
    var welcome = document.getElementById('welcomeMessage');
    if (welcome) welcome.style.display = 'none';
    var panel = document.getElementById('dashboardPanel');
    if (!panel) return;
    panel.style.display = 'block';

    var user = d.user || {};
    var stats = d.stats || {};
    var shows = d.tradeshows || [];
    var certs = d.certifications || [];
    var tips = d.market_tips || [];

    var html = '<div class="dashboard">';

    // User + Product bar
    html += '<div class="db-user-bar">' +
        '👋 <b>' + (user.email||'') + '</b>' +
        (user.product ? ' | 主营：<span class="db-product">' + user.product + '</span>' : '') +
        (user.company ? ' | ' + user.company : '') +
        '</div>';

    // Workflow Tracker
    html += '<div class="db-section"><h3>🔄 贸易工作流</h3>';
    html += '<div class="wf-tracker" id="wfTracker">';
    var stages = [
        {id:1,icon:'🔍',name:'市场调研',desc:'搜索买家+分析市场'},
        {id:2,icon:'📋',name:'合规审查',desc:'认证+法规检查'},
        {id:3,icon:'✉️',name:'商务沟通',desc:'开发信+报价+询盘'},
        {id:4,icon:'✅',name:'成交交付',desc:'合同+物流+跟进'}
    ];
    stages.forEach(function(s,i){
        html += '<div class="wf-stage active" onclick=\"updateWorkflowStage('+s.id+')\" title=\"点击标记完成\">' +
            '<div class="wf-stage-icon">' + s.icon + '</div>' +
            '<div class="wf-stage-name">' + s.name + '</div>' +
            '<div class="wf-stage-desc">' + s.desc + '</div>' +
            (i<3?'<div class="wf-stage-arrow">→</div>':'') +
            '</div>';
    });
    html += '</div></div>';

    // Stats
    html += '<div class="db-stats">' +
        '<div class="db-stat"><div class="db-stat-val">' + (stats.total_contacts||0) + '</div><div class="db-stat-lbl">客户总数</div></div>' +
        '<div class="db-stat"><div class="db-stat-val" style="color:#f0a040">' + (stats.pending_contacts||0) + '</div><div class="db-stat-lbl">待联系</div></div>' +
        '<div class="db-stat"><div class="db-stat-val" style="color:#5ba0d9">' + (stats.contacted||0) + '</div><div class="db-stat-lbl">已联系</div></div>' +
        '<div class="db-stat"><div class="db-stat-val" style="color:#5bba8a">' + (stats.replied||0) + '</div><div class="db-stat-lbl">已回复</div></div>' +
        '<div class="db-stat"><div class="db-stat-val" style="color:#e87070">' + (stats.due_reminders||0) + '</div><div class="db-stat-lbl">需提醒</div></div>' +
        '</div>';

    // Pending email follow-ups
    var pendingEmails = stats.pending_email_list || [];
    if (pendingEmails.length > 0) {
        html += '<div class="db-section"><h3>📧 待跟进邮件</h3>';
        pendingEmails.forEach(function(e){
            html += '<div class="db-tradeshow" style="border-left-color:#f0a040">' +
                '<div class="ts-name">📨 ' + (e.subject||'无主题') + '</div>' +
                '<div class="ts-meta">收件人: ' + (e.to||'?') + ' | ' + (e.days_ago||'?') + '天前</div>' +
                '<div class="ts-tip">💡 超过1天未回复，建议跟进</div>' +
                '</div>';
        });
        html += '</div>';
    }

    // Trade shows
    html += '<div class="db-section"><h3>📅 ' + (user.product||'产品') + ' 相关展销会</h3>';
    if (shows.length === 0) {
        html += '<div class="db-empty">未匹配到专属展会，建议关注广交会和环球资源展</div>';
    } else {
        shows.forEach(function(s){
            html += '<div class="db-tradeshow">' +
                '<div class="ts-name">' + s.name + ' (' + (s.name_cn||'') + ')</div>' +
                '<div class="ts-meta">📍 ' + s.location + ' | 📅 ' + s.date + ' | 👥 ' + s.scale + '</div>' +
                '<div class="ts-meta">🎯 ' + s.focus + '</div>' +
                (s.tip ? '<div class="ts-tip">💡 ' + s.tip + '</div>' : '') +
                (s.url ? '<div class="ts-meta">🔗 <a href="' + s.url + '" target="_blank">' + s.url + '</a></div>' : '') +
                '</div>';
        });
    }
    html += '</div>';

    // Certifications
    if (certs.length > 0) {
        html += '<div class="db-section"><h3>📋 出口认证要求</h3>';
        certs.forEach(function(c){
            html += '<span class="db-cert' + (c.required?' required':'') + '">' +
                c.name + (c.required?' ⚠️强制':'') + ' | ' + c.cost + ' | ' + c.time +
                '</span> ';
        });
        html += '</div>';
    }

    // Market tips
    if (tips.length > 0) {
        html += '<div class="db-section"><h3>📊 市场洞察</h3>';
        tips.forEach(function(t){
            html += '<div class="db-tip">' + t + '</div>';
        });
        html += '</div>';
    }

    html += '<div class="quick-actions" style="margin-top:10px">' +
        '<button class="quick-btn" data-action="帮我搜索' + (user.product||'产品') + '相关的买家">🔍 搜索买家</button>' +
        '<button class="quick-btn" data-action="给' + (user.product||'产品') + '写一封英文开发信，介绍产品卖点">✉️ 写开发信</button>' +
        '<button class="quick-btn" data-action="美元兑人民币的汇率是多少">💱 查询汇率</button>' +
        '<button class="quick-btn" data-action="为' + (user.product||'产品') + '生成几条创意广告语">🎯 广告语</button>' +
        '</div>';

    html += '</div>';
    panel.innerHTML = html;

    // Re-bind quick action buttons
    panel.querySelectorAll('.quick-btn').forEach(function(btn){
        btn.addEventListener('click', function(){
            var action = this.getAttribute('data-action');
            if (action) sendQuickAction(action);
        });
    });
}

// ===== User Preferences (跨会话记忆) =====
function saveSearchPreference(query) {
    if (!currentUser) return;
    fetch('/api/preferences', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({user_email: currentUser.email, update: true, search_query: query})
    }).catch(function(){});
}

// ===== Sidebar =====
function initSidebar() {
    document.getElementById('sidebarToggle').addEventListener('click', function(){
        var sb = document.getElementById('sidebar');
        var isOpen = sb.classList.contains('open');
        if (isOpen) { sb.classList.remove('open'); this.classList.remove('shifted'); }
        else { sb.classList.add('open'); this.classList.add('shifted'); }
    });
    document.getElementById('btnSidebarClose').addEventListener('click', function(){
        document.getElementById('sidebar').classList.remove('open');
        document.getElementById('sidebarToggle').classList.remove('shifted');
    });
}

function loadSidebarData() {
    if (!currentUser || !currentUser.product) return;
    var toggle = document.getElementById('sidebarToggle');

    // 首次登录自动展开侧边栏
    if (!sessionStorage.getItem('sidebarShown')) {
        setTimeout(function() {
            document.getElementById('sidebar').classList.add('open');
            toggle.classList.add('shifted');
            sessionStorage.setItem('sidebarShown', '1');
        }, 1000);
    }

    fetch('/api/dashboard', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({user_email: currentUser.email})
    }).then(function(r){return r.json()}).then(function(d){
        if (!d.success) return;
        renderSidebar(d);
    });
}

function renderSidebar(d) {
    var body = document.getElementById('sidebarBody');
    var html = '';
    var shows = d.tradeshows || [];
    var certs = d.certifications || [];
    var tips = d.market_tips || [];
    var stats = d.stats || {};
    var product = (d.user && d.user.product) || '产品';

    // Stats
    html += '<div class="sb-section open"><div class="sb-section-header" onclick="toggleSBSection(this)">' +
        '📊 客户概览 <span class="sb-arrow">▶</span></div><div class="sb-section-body">' +
        '<div class="sb-stat-row">' +
        '<div class="sb-stat-mini"><div class="sv">'+(stats.total_contacts||0)+'</div><div class="sl">总客户</div></div>' +
        '<div class="sb-stat-mini"><div class="sv" style="color:var(--orange)">'+(stats.pending_contacts||0)+'</div><div class="sl">待联系</div></div>' +
        '<div class="sb-stat-mini"><div class="sv" style="color:var(--green)">'+(stats.replied||0)+'</div><div class="sl">已回复</div></div>' +
        '</div></div></div>';

    // Trade shows
    html += '<div class="sb-section open"><div class="sb-section-header" onclick="toggleSBSection(this)">' +
        '📅 ' + product + ' 展销会 <span class="sb-arrow">▶</span></div><div class="sb-section-body">';
    if (shows.length === 0) {
        html += '<div style="color:var(--text4);padding:4px 0">暂无匹配展会，建议关注广交会</div>';
    } else {
        shows.forEach(function(s){
            html += '<div class="sb-item">' +
                '<div class="sbi-name">' + s.name + '</div>' +
                '<div class="sbi-meta">📍 ' + s.location + ' | 📅 ' + s.date + '</div>' +
                '<div class="sbi-meta">👥 ' + s.scale + ' | 🎯 ' + (s.focus||'') + '</div>' +
                (s.tip ? '<div class="sbi-tip">💡 ' + s.tip + '</div>' : '') +
                (s.url ? '<div class="sbi-link">🔗 <a href="' + s.url + '" target="_blank">' + s.url + '</a></div>' : '') +
                '</div>';
        });
    }
    html += '</div></div>';

    // Certifications
    if (certs.length > 0) {
        html += '<div class="sb-section"><div class="sb-section-header" onclick="toggleSBSection(this)">' +
            '📋 出口认证要求 <span class="sb-arrow">▶</span></div><div class="sb-section-body">';
        certs.forEach(function(c){
            html += '<span class="sb-badge ' + (c.required?'required':'optional') + '">' +
                c.name + (c.required?' ⚠️强制':'') + '</span> ' +
                '<span style="font-size:10px;color:var(--text4)">' + c.cost + ' | ' + c.time + '</span><br>';
        });
        html += '</div></div>';
    }

    // Market tips
    if (tips.length > 0) {
        html += '<div class="sb-section"><div class="sb-section-header" onclick="toggleSBSection(this)">' +
            '📊 市场洞察 <span class="sb-arrow">▶</span></div><div class="sb-section-body">';
        tips.forEach(function(t){
            html += '<div style="padding:3px 0;font-size:11px;color:var(--accent2);line-height:1.5">💡 ' + t + '</div>';
        });
        html += '</div></div>';
    }

    body.innerHTML = html;
}

function toggleSBSection(header) {
    var section = header.parentElement;
    section.classList.toggle('open');
}

// ===== API Live-Dot (Hub-inspired) =====
function updateApiStatus() {
    var dot = document.getElementById('apiLiveDot');
    if (!dot) return;
    fetch('/api/health').then(function(r){return r.json()}).then(function(d){
        if (d.status === 'ok') { dot.classList.remove('offline'); dot.title = 'AI服务在线'; }
        else { dot.classList.add('offline'); dot.title = 'AI服务异常'; }
    }).catch(function(){ dot.classList.add('offline'); dot.title = '无法连接'; });
}
setInterval(updateApiStatus, 30000); // 每30秒检查一次

// ===== File Upload =====
function handleFileUpload(event) {
    var file = event.target.files[0];
    if (!file) return;
    if (!currentUser) { alert('请先登录'); return; }

    var formData = new FormData();
    formData.append('file', file);
    formData.append('user_email', currentUser.email);

    addMessage('assistant', '📎 正在解析 ' + file.name + '...');

    fetch('/api/upload/manual', {
        method: 'POST',
        body: formData
    }).then(function(r){return r.json()}).then(function(d){
        if (d.success) {
            // 清除会话，让下次对话加载手册
            fetch('/api/clear', {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({user_email: currentUser.email, session_id: currentUser.email})
            }).then(function(){
                addMessage('assistant', '✅ ' + d.message + '\n\n📄 预览：' + d.preview + '\n\n💡 产品手册已加载！之后的开发信、广告语、商品描述都将基于此手册内容生成。');
            });
        } else {
            addMessage('assistant', '❌ ' + (d.error || '上传失败'));
        }
    }).catch(function(e){
        addMessage('assistant', '❌ 上传失败：网络错误');
    });

    // 重置 input 以便重新选择同一文件
    event.target.value = '';
}

// ===== Excel Upload & Bulk Email =====
function handleExcelUpload(event) {
    var file = event.target.files[0];
    if (!file) return;
    if (!currentUser) { alert('请先登录'); return; }

    addMessage('assistant', '📋 正在解析 ' + file.name + '...');
    var formData = new FormData();
    formData.append('file', file);
    formData.append('user_email', currentUser.email);

    fetch('/api/upload/excel', {method:'POST',body:formData})
    .then(function(r){return r.json()})
    .then(function(d){
        if (d.success) {
            renderExcelTable(d);
        } else {
            addMessage('assistant', '❌ ' + (d.error || '解析失败'));
        }
    }).catch(function(e){
        addMessage('assistant', '❌ 上传失败：网络错误');
    });
    event.target.value = '';
}

function renderExcelTable(data) {
    var companies = data.companies || [];
    if (companies.length === 0) return;

    var html = '<div class="excel-panel">';
    html += '<div class="excel-header">📋 ' + data.message + '</div>';
    html += '<div class="excel-table-wrap"><table class="excel-table"><thead><tr>';
    html += '<th><input type="checkbox" id=\"excelSelectAll\" onchange=\"toggleSelectAll(this)\"></th>';
    var cols = ['company_name','email','contact_person','phone','country','product_interest'];
    var colLabels = ['公司名','邮箱','联系人','电话','国家','产品'];
    for (var i=0; i<cols.length; i++) {
        html += '<th>' + colLabels[i] + '</th>';
    }
    html += '<th>操作</th></tr></thead><tbody>';

    companies.forEach(function(c, idx) {
        html += '<tr>';
        html += '<td><input type=\"checkbox\" class=\"excel-cb\" data-idx=\"' + idx + '\"></td>';
        for (var j=0; j<cols.length; j++) {
            html += '<td>' + (c[cols[j]] || '') + '</td>';
        }
        html += '<td><button class=\"ei-btn\" onclick=\"emailOneCompany(' + idx + ')\">✉️ 发邮件</button></td>';
        html += '</tr>';
    });

    html += '</tbody></table></div>';
    html += '<div class="excel-actions">';
    html += '<button class="quick-btn" onclick="emailSelectedCompanies()">✉️ 批量发邮件（选中）</button>';
    html += '<button class="quick-btn" onclick="addAllToContacts()">📋 全部加入待联系</button>';
    html += '</div>';
    html += '</div>';

    // Store companies data globally
    window._excelCompanies = companies;

    var div = document.createElement('div');
    div.innerHTML = html;
    chatMessages.appendChild(div);
    smartScroll();
}

function toggleSelectAll(cb) {
    document.querySelectorAll('.excel-cb').forEach(function(c){ c.checked = cb.checked; });
}

function getSelectedCompanies() {
    var selected = [];
    document.querySelectorAll('.excel-cb:checked').forEach(function(cb){
        var idx = parseInt(cb.getAttribute('data-idx'));
        if (window._excelCompanies && window._excelCompanies[idx]) {
            selected.push(window._excelCompanies[idx]);
        }
    });
    return selected;
}

function emailOneCompany(idx) {
    var c = window._excelCompanies && window._excelCompanies[idx];
    if (!c) return;
    var prompt = '给 ' + (c.company_name || '客户') + ' 写一封开发信';
    if (c.product_interest) prompt += '，推荐产品：' + c.product_interest;
    if (c.country) prompt += '，目标市场：' + c.country;
    prompt += '。联系人：' + (c.contact_person || '采购经理');
    chatInput.value = prompt + '\n收件邮箱：' + (c.email || '请补充邮箱');
    chatInput.focus();
    scrollToBottom();
}

function emailSelectedCompanies() {
    var selected = getSelectedCompanies();
    if (selected.length === 0) { alert('请先勾选要发邮件的公司'); return; }
    var msg = '请为以下 ' + selected.length + ' 家公司分别撰写个性化开发信：\n';
    selected.forEach(function(c, i) {
        msg += (i+1) + '. ' + (c.company_name || 'Unknown') + ' — ' + (c.email || '无邮箱') + ' — ' + (c.country || '') + ' — ' + (c.product_interest || '') + '\n';
    });
    chatInput.value = msg;
    sendMessage();
}

function addAllToContacts() {
    var selected = getSelectedCompanies();
    var list = selected.length > 0 ? selected : (window._excelCompanies || []);
    if (list.length === 0) { alert('无厂家数据'); return; }
    var count = 0;
    list.forEach(function(c){
        if (!c.company_name && !c.email) return;
        addBuyerToContacts(
            c.company_name || c.email,
            c.email || '',
            c.website || '',
            c.country || '',
            'Excel导入'
        );
        count++;
    });
    alert('✅ 已添加 ' + count + ' 个客户到待联系列表');
    if (typeof loadContactBox === 'function') setTimeout(loadContactBox, 500);
}

// ===== Mood Doll (Simplified) =====
var moodDoll = JSON.parse(localStorage.getItem('tradeMasterDoll') || 'null') || {id:'cheerful_bear',name:'乐乐熊',emoji:'🧸'};
var moodLastInteraction = Date.now();
var moodGreeted = false;
var moodDrag = null;
var moodTimer = null;
var moodIdleTimer = null;

// Pet reactions for single click
var PET_REACTIONS = ['嘻~', '(*^▽^*)', '抱抱~', '嘿！', '嗯？', '嘻嘻', '❤️', '☺️'];

// Proactive idle messages
var IDLE_MESSAGES = [
    '在忙吗？记得抬头看看窗外哦~ 🌿',
    '你已经很久没动了呢，要不要伸个懒腰？',
    '我还在哦~ 有什么想聊的吗？',
    '工作再忙也要记得喝水呀 💧',
    '悄悄告诉你：你做得很好！',
    '休息一下也没关系的~',
    '嘿！我在这里陪着你呢 ✨',
    '要不要和我聊聊天？我一直在哦~',
];

function initDoll() {
    var doll = document.getElementById('moodDoll');
    var head = document.getElementById('moodHead');

    // Drag
    doll.addEventListener('mousedown', function(e){
        if (e.detail >= 2) return;
        moodDrag = {x: e.clientX - doll.offsetLeft, y: e.clientY - doll.offsetTop};
        document.addEventListener('mousemove', onDollDrag);
        document.addEventListener('mouseup', onDollDragEnd);
    });

    // Double-click name → rename
    var nameEl = document.getElementById('moodName');
    if (nameEl) {
        nameEl.addEventListener('dblclick', function(e){
            e.stopPropagation();
            var newName = prompt('给你的玩偶起个名字吧：', moodDoll.customName || moodDoll.name);
            if (newName && newName.trim()) {
                moodDoll.customName = newName.trim();
                localStorage.setItem('tradeMasterDoll', JSON.stringify(moodDoll));
                updateMoodUI();
                addMoodChatMsg('好的！以后我就叫' + moodDoll.customName + '啦~', false);
            }
        });
        nameEl.style.cursor = 'pointer';
        nameEl.title = '双击改名';
    }

    // Single click → pet reaction (on head)
    if (head) {
        head.addEventListener('click', function(e){
            if (e.detail === 2) return;
            e.stopPropagation();
            petDoll();
        });
        // Double click → open chat
        head.addEventListener('dblclick', function(e){
            e.stopPropagation();
            openMoodChat();
        });
    }

    // Chat buttons
    document.getElementById('moodSendBtn').addEventListener('click', sendMoodMsg);
    document.getElementById('moodInput').addEventListener('keydown', function(e){ if(e.key==='Enter') sendMoodMsg(); });
    document.getElementById('moodCloseChat').addEventListener('click', function(){
        var chat = document.getElementById('moodChat');
        chat.style.display = 'none';
        // Reset position to default
        chat.style.right = '20px';
        chat.style.bottom = '110px';
        chat.style.left = 'auto';
        chat.style.top = 'auto';
    });
    function openPicker() {
        var overlay = document.getElementById('moodPickerOverlay');
        overlay.style.display = 'flex';
        loadMoodPicker();
    }
    document.getElementById('moodChangeBtn').addEventListener('click', openPicker);
    document.getElementById('moodPickerClose').addEventListener('click', function(){
        document.getElementById('moodPickerOverlay').style.display = 'none';
    });
    document.getElementById('moodPickerOverlay').addEventListener('click', function(e){
        if (e.target === this) this.style.display = 'none';
    });
    document.querySelectorAll('.mood-chat-quick button').forEach(function(b){
        b.addEventListener('click', function(){
            document.getElementById('moodInput').value = this.getAttribute('data-msg');
            sendMoodMsg();
        });
    });

    updateMoodUI();

    // Auto-greet after 3 seconds
    setTimeout(function(){
        if (!moodGreeted && Date.now() - moodLastInteraction > 2500) { showMoodCloud('auto'); moodGreeted = true; }
    }, 3000);

    // Track page-wide user activity
    function resetIdleTimer() {
        moodLastInteraction = Date.now();
    }
    document.addEventListener('mousemove', resetIdleTimer, {passive:true});
    document.addEventListener('keydown', resetIdleTimer, {passive:true});
    document.addEventListener('click', resetIdleTimer, {passive:true});
    document.addEventListener('scroll', resetIdleTimer, {passive:true});

    // Proactive idle interaction: every 90 seconds check
    moodIdleTimer = setInterval(function(){
        var idle = Date.now() - moodLastInteraction;
        var cloud = document.getElementById('moodCloud');
        if (idle > 90000 && !(cloud.style.display === 'block')) {
            var msg = IDLE_MESSAGES[Math.floor(Math.random() * IDLE_MESSAGES.length)];
            showMoodCloudText(msg);
            moodLastInteraction = Date.now();
        }
        // Random idle animation every ~60s
        if (Math.random() < 0.3) {
            var doll = document.getElementById('moodDoll');
            doll.classList.add('bounce');
            setTimeout(function(){ doll.classList.remove('bounce'); }, 500);
        }
    }, 90000);
}

function onDollDrag(e) {
    var doll = document.getElementById('moodDoll');
    doll.style.right = 'auto'; doll.style.bottom = 'auto';
    doll.style.left = (e.clientX - moodDrag.x) + 'px';
    doll.style.top = (e.clientY - moodDrag.y) + 'px';
    // Also update chat position if open
    var chat = document.getElementById('moodChat');
    if (chat.style.display === 'flex') {
        var dollRect = doll.getBoundingClientRect();
        chat.style.left = Math.max(10, dollRect.right - 260) + 'px';
        chat.style.top = Math.max(10, dollRect.top - 290) + 'px';
    }
}
function onDollDragEnd() {
    document.removeEventListener('mousemove', onDollDrag);
    document.removeEventListener('mouseup', onDollDragEnd);
}

function petDoll() {
    var doll = document.getElementById('moodDoll');
    doll.classList.remove('petted'); void doll.offsetWidth; doll.classList.add('petted');
    var reaction = PET_REACTIONS[Math.floor(Math.random() * PET_REACTIONS.length)];
    showMoodCloudText(reaction);
    setTimeout(function(){ document.getElementById('moodCloud').style.display = 'none'; }, 2000);
    moodLastInteraction = Date.now();
}

function openMoodChat() {
    var chat = document.getElementById('moodChat');
    var doll = document.getElementById('moodDoll');
    var dollRect = doll.getBoundingClientRect();
    // Position chat relative to doll
    chat.style.right = 'auto';
    chat.style.bottom = 'auto';
    chat.style.left = (dollRect.right - 260) + 'px';
    chat.style.top = (dollRect.top - 290) + 'px';
    // Ensure chat stays in viewport
    if (parseInt(chat.style.left) < 10) chat.style.left = '10px';
    if (parseInt(chat.style.top) < 10) chat.style.top = '10px';
    chat.style.display = 'flex';
    if (!moodGreeted) { showMoodCloud('auto'); moodGreeted = true; }
    moodLastInteraction = Date.now();
}

function showMoodCloud(type) {
    fetch('/api/doll/greet', {method:'POST',headers:{'Content-Type':'application/json'},
        body: JSON.stringify({doll_id:moodDoll.id, type:type})
    }).then(function(r){return r.json()}).then(function(d){
        if (d.success) showMoodCloudText(d.greeting);
    }).catch(function(){ showMoodCloudText('嗨~今天怎么样呀？'); });
}

function showMoodCloudText(text) {
    var cloud = document.getElementById('moodCloud');
    document.getElementById('moodCloudText').textContent = text;
    cloud.style.display = 'block';
    cloud.style.animation = 'none'; void cloud.offsetWidth;
    cloud.style.animation = 'moodCloudIn .4s ease';
    // Auto-hide after 6 seconds (shorter for idle messages)
    setTimeout(function(){ cloud.style.display = 'none'; }, 6000);
}

function addMoodChatMsg(text, isUser) {
    var c = document.getElementById('moodChatMsgs');
    var d = document.createElement('div');
    d.className = 'doll-msg' + (isUser ? ' user' : '');
    d.innerHTML = '<span class=\"doll-msg-text\">' + text + '</span>';
    c.appendChild(d); c.scrollTop = c.scrollHeight;
}

function sendMoodMsg() {
    var input = document.getElementById('moodInput');
    var msg = input.value.trim();
    if (!msg) return;
    addMoodChatMsg(msg, true);
    input.value = '';
    moodLastInteraction = Date.now();
    // Show typing indicator
    var c = document.getElementById('moodChatMsgs');
    var typing = document.createElement('div');
    typing.className = 'doll-msg doll-typing'; typing.id = 'moodTyping';
    typing.innerHTML = '<span class=\"doll-msg-text\" style=\"color:var(--text4);font-style:italic\">嗯...</span>';
    c.appendChild(typing); c.scrollTop = c.scrollHeight;
    fetch('/api/doll/chat', {method:'POST',headers:{'Content-Type':'application/json'},
        body: JSON.stringify({message:msg, doll_id:moodDoll.id})
    }).then(function(r){return r.json()}).then(function(d){
        var t = document.getElementById('moodTyping'); if(t) t.remove();
        moodLastInteraction = Date.now();
        addMoodChatMsg(d.success ? d.reply : '唔...走神了~', false);
    }).catch(function(){
        var t = document.getElementById('moodTyping'); if(t) t.remove();
        addMoodChatMsg('呀，网络不好~', false);
    });
}

function loadMoodPicker() {
    // Static fallback dolls in case API fails
    var STATIC_DOLLS = [
        {id:'cheerful_bear',name:'乐乐熊',emoji:'🧸'},
        {id:'wise_cat',name:'智智猫',emoji:'🐱'},
        {id:'gentle_bunny',name:'柔柔兔',emoji:'🐰'},
        {id:'cool_fox',name:'酷酷狐',emoji:'🦊'},
        {id:'sleepy_sloth',name:'困困树懒',emoji:'🦥'},
    ];

    function renderCards(dolls) {
        var grid = document.getElementById('moodPickerGrid');
        grid.innerHTML = '';
        var isDark = document.body.classList.contains('dark');
        var borderColor = isDark ? '#475569' : '#d0d9e2';
        var bgColor = isDark ? '#1e293b' : '#f8fafc';
        var accentColor = isDark ? '#60a5fa' : '#4f8cff';
        var accentBg = isDark ? '#1e3a5f' : '#eaf3fb';

        dolls.forEach(function(doll){
            var card = document.createElement('div');
            var selected = doll.id === moodDoll.id;
            card.style.cssText = 'display:inline-block;padding:14px 8px;margin:4px;border:2px solid ' + (selected ? accentColor : borderColor) + ';border-radius:50%;cursor:pointer;text-align:center;width:80px;height:80px;background:' + (selected ? accentBg : bgColor) + ';transition:all .2s;display:flex;flex-direction:column;align-items:center;justify-content:center';
            card.innerHTML = '<span style=\"font-size:32px;display:block\">' + doll.emoji + '</span><span style=\"font-size:10px;font-weight:700;color:#1e293b;margin-top:2px\">' + doll.name + '</span>';

            card.addEventListener('mouseenter', function(){ if(!this.classList.contains('selected')){this.style.borderColor=accentColor;this.style.transform='translateY(-2px)';} });
            card.addEventListener('mouseleave', function(){ if(!this.classList.contains('selected')){this.style.borderColor=borderColor;this.style.transform='none';} });

            card.addEventListener('click', function(){
                grid.querySelectorAll('div').forEach(function(c){
                    c.style.borderColor = borderColor;
                    c.style.background = bgColor;
                });
                card.style.borderColor = accentColor;
                card.style.background = accentBg;
                moodDoll = doll;
                moodDoll.customName = null;  // 换玩偶时清除自定义名
                localStorage.setItem('tradeMasterDoll', JSON.stringify(moodDoll));
                updateMoodUI();
                document.getElementById('moodChatMsgs').innerHTML = '';
                addMoodChatMsg('嗨~我是' + doll.name + '！双击我的名字可以给我改名哦~', false);
                moodGreeted = false;
                setTimeout(function(){ showMoodCloud('auto'); moodGreeted = true; }, 500);
            });
            grid.appendChild(card);
        });
    }

    fetch('/api/doll/list').then(function(r){return r.json()}).then(function(d){
        if (d.success && d.dolls && d.dolls.length > 0) {
            renderCards(d.dolls);
        } else {
            renderCards(STATIC_DOLLS);
        }
    }).catch(function(){
        renderCards(STATIC_DOLLS);
    });
}

var DOLL_THEMES = {cheerful_bear:'bear',wise_cat:'cat',gentle_bunny:'bunny',cool_fox:'fox',sleepy_sloth:'sloth'};

function updateMoodUI() {
    document.getElementById('moodHead').textContent = moodDoll.emoji;
    var displayName = moodDoll.customName || moodDoll.name;
    document.getElementById('moodName').textContent = displayName;
    document.getElementById('moodChatTitle').textContent = moodDoll.emoji + ' ' + displayName;
    // Set body theme
    var body = document.getElementById('moodBody');
    body.className = 'mood-body theme-' + (DOLL_THEMES[moodDoll.id] || 'bear');
}

function updateWorkflowStage(stage) {
    if (!currentUser) return;
    fetch('/api/workflow/update', {
        method:'POST',headers:{'Content-Type':'application/json'},
        body: JSON.stringify({user_email:currentUser.email, stage:stage})
    }).then(function(r){return r.json()}).then(function(d){
        if (d.success && d.workflow) {
            var stages = document.querySelectorAll('.wf-stage');
            d.workflow.stages.forEach(function(s,i){
                if (stages[i]) {
                    stages[i].className = 'wf-stage ' + s.status;
                }
            });
        }
    });
}

function syncInbox() {
    if (!currentUser) { alert('请先登录'); return; }
    var btn = event.target;
    btn.textContent = '⏳ 同步中...'; btn.disabled = true;
    fetch('/api/email/sync', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({user_email: currentUser.email})
    }).then(function(r){return r.json()}).then(function(d){
        btn.textContent = '📥 同步'; btn.disabled = false;
        if (d.success) {
            var replies = d.replies || [];
            if (replies.length > 0) {
                var msg = '📬 发现 ' + replies.length + ' 条客户回复：';
                replies.forEach(function(r){
                    msg += '\n• ' + (r.from||'') + ' — ' + (r.subject||'') + ' [' + (r.intent||'?') + ']';
                });
                addMessage('assistant', msg);
            } else {
                addMessage('assistant', '📭 ' + (d.message || '未发现新的客户回复'));
            }
            if (typeof loadEmailBox === 'function') loadEmailBox();
        } else {
            addMessage('assistant', '❌ ' + (d.error || '同步失败'));
        }
    }).catch(function(e){
        btn.textContent = '📥 同步'; btn.disabled = false;
        addMessage('assistant', '❌ 同步失败：网络错误');
    });
}

function showFollowupHint(container, toEmail) {
    var hint = container.querySelector('.ea-followup-hint');
    hint.style.display = 'block';
    hint.innerHTML = '📅 已自动加入跟进队列 — 若3天后未收到回复，系统将提醒你发送跟进邮件给 <b>' + toEmail + '</b>';
}

// ═══════════════════════════════════════════
// 一键获客
// ═══════════════════════════════════════════
var acqBuyerData = [];

function openAcquisitionPanel() {
    document.getElementById('acqOverlay').classList.add('show');
    document.getElementById('acqMsg').className = 'acq-msg';
    document.getElementById('acqResults').style.display = 'none';
    document.getElementById('acqProgress').style.display = 'none';
    document.getElementById('acqKeyword').focus();
    // 预填用户产品
    if (window._userInfo && window._userInfo.product) {
        document.getElementById('acqKeyword').value = window._userInfo.product || '';
    }
}

function closeAcquisitionPanel() {
    document.getElementById('acqOverlay').classList.remove('show');
}

document.addEventListener('DOMContentLoaded', function() {
    // Acquisition panel close buttons
    var btnClose = document.getElementById('btnAcqClose');
    if (btnClose) btnClose.onclick = closeAcquisitionPanel;
    var btnCloseR = document.getElementById('btnAcqCloseResults');
    if (btnCloseR) btnCloseR.onclick = closeAcquisitionPanel;
    // Click overlay to close
    var acqOverlay = document.getElementById('acqOverlay');
    if (acqOverlay) {
        acqOverlay.addEventListener('click', function(e) {
            if (e.target === acqOverlay) closeAcquisitionPanel();
        });
    }

    // Go button
    var btnGo = document.getElementById('btnAcqGo');
    if (btnGo) btnGo.onclick = runAcquisition;

    // Export button
    var btnExport = document.getElementById('btnAcqExport');
    if (btnExport) btnExport.onclick = exportAcqCSV;

    // Enter key triggers search
    document.getElementById('acqKeyword').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') runAcquisition();
    });
});

function runAcquisition() {
    var keyword = document.getElementById('acqKeyword').value.trim();
    if (!keyword) {
        showAcqMsg('请输入产品关键词', 'error');
        return;
    }

    var market = document.getElementById('acqMarket').value.trim();
    var count = parseInt(document.getElementById('acqCount').value);

    var btn = document.getElementById('btnAcqGo');
    btn.disabled = true;
    btn.textContent = '搜索中...';

    document.getElementById('acqMsg').className = 'acq-msg';
    document.getElementById('acqResults').style.display = 'none';
    var progress = document.getElementById('acqProgress');
    progress.style.display = 'flex';
    document.getElementById('acqProgressText').textContent = '正在搜索 ' + keyword + ' 的买家...';

    var userEmail = (window._userInfo && window._userInfo.email) || 'demo@trademaster.com';

    fetch('/api/customer-acquisition', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
            user_email: userEmail,
            keyword: keyword,
            target_market: market,
            max_results: count
        })
    }).then(function(r) { return r.json(); })
    .then(function(d) {
        btn.disabled = false;
        btn.textContent = '开始获客';
        progress.style.display = 'none';

        if (!d.success) {
            showAcqMsg(d.error || '获客失败，请重试', 'error');
            return;
        }

        acqBuyerData = d.buyers || [];
        document.getElementById('acqResultsTitle').textContent =
            '找到 ' + d.total_found + ' 家买家，已保存 ' + d.saved_to_contacts + ' 家到客户跟进';

        var tbody = document.getElementById('acqTableBody');
        tbody.innerHTML = '';
        (d.buyers || []).forEach(function(b, i) {
            var tr = document.createElement('tr');
            var emailHtml = b.email && b.email.includes('@')
                ? '<span class="acq-email">' + escapeHtml(b.email) + '</span>'
                : '<span class="acq-no-email">无邮箱（建议LinkedIn联系）</span>';

            var draftHtml = b.draft_email
                ? '<div class="acq-draft">' + escapeHtml(b.draft_email.substring(0, 250)) + (b.draft_email.length > 250 ? '...' : '') + '</div>'
                : '<span class="acq-no-email">可手动编写</span>';

            var copyBtn = b.draft_email
                ? '<button class="acq-btn-copy" onclick="copyAcqDraft(' + i + ', this)">复制</button>'
                : '';

            tr.innerHTML = '<td><b>' + escapeHtml(b.company_name) + '</b></td>' +
                '<td>' + escapeHtml(b.country || '-') + '</td>' +
                '<td>' + (b.website ? '<a href="' + (b.website.startsWith('http') ? b.website : 'https://' + b.website) + '" target="_blank" style="color:var(--accent)">' + escapeHtml(b.website.substring(0,25)) + '</a>' : '-') + '</td>' +
                '<td>' + emailHtml + '</td>' +
                '<td>' + draftHtml + '</td>' +
                '<td style="white-space:nowrap">' + copyBtn + '<button class="acq-btn-copy" onclick="saveSingleContact(' + i + ',this)" style="margin-left:2px">存客户</button></td>';
            tbody.appendChild(tr);
        });

        document.getElementById('acqResults').style.display = 'block';
        showAcqMsg('获客成功！ ' + d.saved_to_contacts + ' 家客户已自动保存到客户跟进系统', 'success');
    }).catch(function(e) {
        btn.disabled = false;
        btn.textContent = '开始获客';
        progress.style.display = 'none';
        showAcqMsg('网络错误：' + e, 'error');
    });
}

function showAcqMsg(text, type) {
    var el = document.getElementById('acqMsg');
    el.className = 'acq-msg ' + (type || '');
    el.textContent = text;
    el.style.display = 'block';
    setTimeout(function() { el.className = 'acq-msg'; el.style.display = 'none'; }, 8000);
}

function copyAcqDraft(i, btn) {
    var text = acqBuyerData[i] && acqBuyerData[i].draft_email;
    if (!text) return;
    navigator.clipboard.writeText(text).then(function() {
        btn.textContent = '已复制';
        btn.classList.add('copied');
        setTimeout(function() { btn.textContent = '复制'; btn.classList.remove('copied'); }, 2000);
    });
}

function saveSingleContact(i, btn) {
    var b = acqBuyerData[i];
    if (!b) return;
    var orig = btn.textContent;
    btn.textContent = '保存中...';
    btn.disabled = true;

    var userEmail = (window._userInfo && window._userInfo.email) || 'demo@trademaster.com';

    fetch('/api/contacts/add', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
            user_email: userEmail,
            company_name: b.company_name,
            email: b.email || '',
            website: b.website || '',
            country: b.country || '',
            product_interest: document.getElementById('acqKeyword').value || '',
            source: '一键获客',
            notes: b.draft_email ? b.draft_email.substring(0, 200) : ''
        })
    }).then(function(r) { return r.json(); })
    .then(function(d) {
        if (d.success) {
            btn.textContent = '已保存';
            btn.classList.add('copied');
        } else {
            btn.textContent = orig;
            btn.disabled = false;
            alert('保存失败：' + (d.error || '未知错误'));
        }
    }).catch(function(e) {
        btn.textContent = orig;
        btn.disabled = false;
    });
}

function exportAcqCSV() {
    if (!acqBuyerData.length) return;
    var csv = '﻿公司名,国家,网站,邮箱,开发信摘要\n';
    acqBuyerData.forEach(function(b) {
        csv += csvField(b.company_name) + ',' + csvField(b.country) + ',' + csvField(b.website) + ',' + csvField(b.email) + ',' + csvField((b.draft_email || '').substring(0, 150).replace(/\n/g, ' ')) + '\n';
    });
    var blob = new Blob([csv], {type: 'text/csv;charset=utf-8'});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'TradeMaster客户线索_' + new Date().toISOString().slice(0,10) + '.csv';
    a.click();
    URL.revokeObjectURL(url);
}

function csvField(val) {
    val = (val || '').replace(/"/g, '""');
    return '"' + val + '"';
}

