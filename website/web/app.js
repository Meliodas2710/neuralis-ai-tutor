let currentLang = localStorage.getItem('appLang') || 'en';
let currentRole = 'student';

const translations = {
    en: {
        nav_home: "Home",
        nav_features: "Features",
        nav_pricing: "Pricing",
        nav_login: "Login",
        nav_get_started: "Get Started",
        hero_title: "Unlock Your<br>Cognitive Edge.",
        hero_desc: "The world's first AI Study Agent designed specifically for high-achieving students and proactive parents who refuse to settle.",
        btn_transformation: "Begin Transformation",
        btn_watch: "Watch the future in 60s",
        tag_excellence: "BUILT FOR EXCELLENCE",
        heading_focus: "Designed for absolute <br>intellectual focus.",
        feature_paths_title: "Hyper-Personalized <br>Learning Paths",
        feature_paths_desc: "Neuralis understands your unique learning gaps and constructs a tailored path to mastery in real-time.",
        feature_shield_title: "Distraction Shield",
        feature_shield_desc: "AI-driven biological focus monitoring that alerts you the moment your attention drifts.",
        feature_schedule_title: "Automated Schedule Mastery",
        feature_schedule_desc: "Dynamic calendars that adapt to your life, extracurriculars, and optimal focus sessions.",
        feature_transparency_title: "Unified parent & <br>student transparency",
        feature_transparency_desc: "Stop the friction. Parents get real-time insights without being overbearing, fostering a healthy path to success.",
        auth_welcome_student: "WELCOME STUDENT",
        auth_welcome_parent: "WELCOME PARENT",
        auth_back_title: "WELCOME BACK",
        auth_create_title: "CREATE ACCOUNT",
        auth_login_btn: "Login Now",
        auth_register_btn: "Register Now",
        auth_toggle_reg: "Need an account? Register",
        auth_toggle_login: "Have an account? Login",
        err_missing: "Missing info",
        err_server_busy: "Server is busy or starting up (Cold Start)",
        toast_success_reg: "Registration successful! Please login.",
        preloader_text: "NEURALIS"
    },
    vi: {
        nav_home: "Trang chủ",
        nav_features: "Tính năng",
        nav_pricing: "Bảng giá",
        nav_login: "Đăng nhập",
        nav_get_started: "Bắt đầu ngay",
        hero_title: "Khai phá sức mạnh<br>Trí tuệ của bạn.",
        hero_desc: "Đại lý học tập AI đầu tiên trên thế giới được thiết kế riêng cho học sinh ưu tú và phụ huynh chủ động.",
        btn_transformation: "Bắt đầu chuyển đổi",
        btn_watch: "Xem tương lai trong 60s",
        tag_excellence: "XÂY DỰNG VÌ SỰ ƯU TÚ",
        heading_focus: "Thiết kế cho sự <br>tập trung trí tuệ tuyệt đối.",
        feature_paths_title: "Lộ trình học tập <br>Cá nhân hóa cao",
        feature_paths_desc: "Neuralis thấu hiểu lỗ hổng kiến thức duy nhất của bạn và xây dựng lộ trình tiến tới sự thành thạo theo thời gian thực.",
        feature_shield_title: "Lớp khiên Tập trung",
        feature_shield_desc: "Giám sát sự tập trung sinh học dựa trên AI, cảnh báo bạn ngay lập tức khi tâm trí xao nhãng.",
        feature_schedule_title: "Làm chủ Lịch trình tự động",
        feature_schedule_desc: "Lịch linh động thích ứng với cuộc sống, hoạt động ngoại khóa và các buổi tập trung tối ưu của bạn.",
        feature_transparency_title: "Phụ huynh & Học sinh <br>Minh bạch hợp nhất",
        feature_transparency_desc: "Xóa bỏ xung đột. Phụ huynh nhận thông tin chi tiết theo thời gian thực mà không gây áp lực, thúc đẩy con đường thành công.",
        auth_welcome_student: "CHÀO MỪNG HỌC SINH",
        auth_welcome_parent: "CHÀO MỪNG PHỤ HUYNH",
        auth_back_title: "CHÀO MỪNG TRỞ LẠI",
        auth_create_title: "TẠO TÀI KHOẢN",
        auth_login_btn: "Đăng nhập ngay",
        auth_register_btn: "Đăng ký ngay",
        auth_toggle_reg: "Chưa có tài khoản? Đăng ký",
        auth_toggle_login: "Đã có tài khoản? Đăng nhập",
        err_missing: "Thiếu thông tin",
        err_server_busy: "Server đang bận hoặc đang khởi động (Cold Start)",
        toast_success_reg: "Đăng ký thành công! Hãy đăng nhập.",
        preloader_text: "NEURALIS"
    }
};

window.changeLanguage = function(lang) {
    currentLang = lang;
    localStorage.setItem('appLang', lang);
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang][key]) {
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = translations[lang][key];
            } else {
                // To prevent wiping out nested spans like .gradient-text,
                // we treat specific keys as full HTML or ignore them if the element has descendants
                el.innerHTML = translations[lang][key];
            }
        }
    });
    // Update active state on buttons if any
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
    });
};

// --- ENVIRONMENT DETECTION & INITIALIZATION ---
function startApp() {
    if (window.appInitialized) return;
    
    // Fallback for standard browsers: Mock the pywebview API to talk to REST API instead
    if (!window.pywebview || !window.pywebview.api) {
        window.isWebMode = true;
        window.pywebview = {
            api: new Proxy({}, {
                get: (target, prop) => {
                    return async (...args) => {
                        try {
                            const token = localStorage.getItem('accessToken');
                            let url = `https://neuralis-ai-tutor.onrender.com/${prop}`;
                            let options = { 
                                headers: { 
                                    'Content-Type': 'application/json',
                                    'Authorization': token ? `Bearer ${token}` : ''
                                } 
                            };
                            
                            if (prop === 'login' || prop === 'register') {
                                options.method = 'POST';
                                options.body = JSON.stringify({username: args[0], password: args[1], role: args[2]});
                            } else {
                                options.method = (args.length > 0) ? 'POST' : 'GET';
                                if (options.method === 'POST') options.body = JSON.stringify(args[0] || {});
                            }

                            const response = await fetch(url, options);
                            const result = await response.json();
                            if (!response.ok) return { success: false, message: result.detail || 'Lỗi hệ thống' };
                            return result;
                        } catch (e) {
                            return { success: false, message: 'Server đang bận hoặc đang khởi động' };
                        }
                    };
                }
            })
        };
    }
    initApp();
}

window.addEventListener('pywebviewready', startApp);
document.addEventListener('DOMContentLoaded', () => setTimeout(startApp, 500));

function initApp() {
    if (appInitialized) return;
    appInitialized = true;
    
    // --- PRELOADER LOGIC ---
    setTimeout(() => {
        const preloader = document.getElementById('preloader');
        if (preloader) {
            preloader.style.opacity = '0';
            setTimeout(() => preloader.style.display = 'none', 600);
        }
    }, 1500);

    // --- HEADER SCROLL EFFECT ---
    window.addEventListener('scroll', () => {
        const header = document.querySelector('.main-header');
        if (window.scrollY > 50) header.classList.add('scrolled');
        else header.classList.remove('scrolled');
    });

    // --- NAVIGATION & VIEW MANAGEMENT ---
    window.showAuthView = function() {
        document.getElementById('auth-view').style.display = 'block';
        document.getElementById('landing-view').style.display = 'none';
        document.querySelector('.main-header').style.display = 'none';
        document.body.style.overflow = 'hidden';
    };

    window.goHome = function() {
        document.getElementById('auth-view').style.display = 'none';
        document.getElementById('landing-view').style.display = 'block';
        document.getElementById('main-view').style.display = 'none';
        document.querySelector('.main-header').style.display = 'block';
        document.body.style.overflow = 'auto';
    };

    window.setRole = function(role) {
        currentRole = role;
        document.querySelectorAll('.role-btn').forEach(btn => {
            const isMatch = btn.textContent.toLowerCase().includes(role);
            btn.classList.toggle('active', isMatch);
            // In the new Elite UI, inactive buttons are transparent
            if (!isMatch) {
                btn.style.background = 'transparent';
                btn.style.color = 'var(--text-muted)';
            } else {
                btn.style.background = 'var(--primary-color)';
                btn.style.color = '#000';
            }
        });
        document.getElementById('auth-title').textContent = (role === 'student') ? 'WELCOME STUDENT' : 'WELCOME PARENT';
    };

    // Auto-login check
    const savedToken = localStorage.getItem('accessToken');
    if (savedToken) {
        window.currentUserId = localStorage.getItem('currentUserId');
        window.currentUserRole = localStorage.getItem('currentUserRole');
        
        document.getElementById('landing-view').style.display = 'none';
        document.querySelector('.main-header').style.display = 'none';
        document.getElementById('auth-view').style.display = 'none';
        document.getElementById('main-view').style.display = 'block';
        loadDashboard();
    }

    // Auth Submit Toggle
    let isRegisterMode = false;
    document.getElementById('auth-toggle-btn').addEventListener('click', () => {
        isRegisterMode = !isRegisterMode;
        document.getElementById('auth-submit-btn').textContent = isRegisterMode ? 'Đăng ký ngay' : 'Đăng nhập ngay';
        document.getElementById('auth-toggle-btn').textContent = isRegisterMode ? 'Đăng nhập' : 'Đăng ký ngay';
        document.getElementById('auth-title').textContent = isRegisterMode ? 'CREATE ACCOUNT' : 'CHÀO MỪNG TRỞ LẠI';
    });

    document.getElementById('auth-submit-btn').addEventListener('click', async () => {
        const u = document.getElementById('auth-username').value.trim();
        const p = document.getElementById('auth-password').value.trim();
        if (!u || !p) { alert("Thiếu thông tin"); return; }

        const btn = document.getElementById('auth-submit-btn');
        btn.disabled = true;
        const oldText = btn.textContent;
        btn.textContent = "🚀 Đang xử lý...";

        try {
            const api = window.pywebview.api;
            let res = isRegisterMode ? await api.register(u, p, currentRole) : await api.login(u, p, currentRole);

            if (res.success) {
                if (isRegisterMode) {
                    alert("Đăng ký thành công! Hãy đăng nhập.");
                    document.getElementById('auth-toggle-btn').click();
                } else {
                    localStorage.setItem('accessToken', res.access_token);
                    localStorage.setItem('currentUserId', res.user_data.id);
                    localStorage.setItem('currentUserRole', res.user_data.role);
                    location.reload(); // Refresh to load app
                }
            } else {
                alert("Lỗi: " + res.message);
            }
        } catch (e) {
            alert("Lỗi kết nối Server");
        } finally {
            btn.disabled = false;
            btn.textContent = oldText;
        }
    });

    document.getElementById('logout-btn').addEventListener('click', () => {
        localStorage.clear();
        location.reload();
    });

    // Navigation routing logic moved here to ensure elements exist
    const navLinks = document.querySelectorAll('.nav-links li');
    const pages = document.querySelectorAll('.page');

    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            const pageId = link.getAttribute('data-page');
            
            navLinks.forEach(n => n.classList.remove('active'));
            link.classList.add('active');
            
            pages.forEach(p => p.classList.remove('active-page'));
            document.getElementById(pageId).classList.add('active-page');
            
            if (pageId === 'main-dashboard') {
                loadDashboard();
            }
            if (pageId === 'profile') {
                loadUserProfileSettings();
            }
            if (pageId === 'achievements') {
                loadAchievements();
            }
            if (pageId === 'leaderboard') {
                loadLeaderboard();
            }
        });
    });

    function updateSidebarForRole(role) {
        const studentTabs = ['nav-student-dashboard', 'nav-achievements', 'nav-chat', 'nav-schedule'];
        const parentTabs = ['nav-parent-dashboard'];

        if (role === 'parent') {
            studentTabs.forEach(id => {
                const el = document.getElementById(id);
                if (id === 'nav-student-dashboard') { 
                    el.style.display = 'none'; 
                } else if (['nav-chat', 'nav-achievements'].includes(id)) {
                    el.style.display = 'none'; // Parents don't chat or see own achievements
                } else {
                    el.style.display = 'flex';
                }
            });
            parentTabs.forEach(id => document.getElementById(id).style.display = 'flex');
            document.getElementById('action-btn').style.display = 'none';
        } else {
            studentTabs.forEach(id => document.getElementById(id).style.display = 'flex');
            parentTabs.forEach(id => document.getElementById(id).style.display = 'none');
            document.getElementById('action-btn').style.display = 'block';
        }
    }

    // --- Role Management ---
    let isParentMode = false;
    async function checkParentMode() {
        if (window.pywebview && window.pywebview.api) {
            const hasPin = await window.pywebview.api.has_parent_pin();
            const unlockArea = document.getElementById('parent-unlock-area');
            const activeArea = document.getElementById('parent-active-area');
            
            if (!hasPin) {
                isParentMode = true; // No pin = unlocked mode (Admin)
                document.getElementById('parent-mode-status').textContent = 'Chế độ: Chưa cài PIN (Mở khóa toàn bộ)';
                document.getElementById('parent-mode-status').style.color = '#2ed573';
                document.getElementById('nav-parent-dashboard').style.display = 'flex';
                unlockArea.style.display = 'flex';
                activeArea.style.display = 'none';
                document.getElementById('toggle-parent-mode-btn').textContent = 'Tạo mã PIN Phụ huynh';
            } else {
                isParentMode = false; // Has pin = locked mode (Student)
                document.getElementById('parent-mode-status').textContent = 'Chế độ: Học sinh (Bị giới hạn)';
                document.getElementById('parent-mode-status').style.color = '#ff4757';
                document.getElementById('nav-parent-dashboard').style.display = 'none';
                unlockArea.style.display = 'flex';
                activeArea.style.display = 'none';
                document.getElementById('toggle-parent-mode-btn').textContent = 'Mở khóa Phụ Huynh';
                if (document.getElementById('dashboard').classList.contains('active-page')) {
                    document.querySelector('[data-page="student-dashboard"]').click();
                }
            }
        }
    }

    document.getElementById('toggle-parent-mode-btn').addEventListener('click', async () => {
        const pin = document.getElementById('parent-pin-input').value;
        if (!pin) { alert('Vui lòng nhập PIN'); return; }
        
        if (window.pywebview && window.pywebview.api) {
            const hasPin = await window.pywebview.api.has_parent_pin();
            if (hasPin) {
                // Verify
                const isValid = await window.pywebview.api.verify_parent_pin(pin);
                if (isValid) {
                    isParentMode = true;
                    document.getElementById('parent-mode-status').textContent = 'Chế độ: Phụ Huynh (Đã mở khóa)';
                    document.getElementById('parent-mode-status').style.color = '#2ed573';
                    document.getElementById('nav-parent-dashboard').style.display = 'flex';
                    document.getElementById('parent-pin-input').value = '';
                    document.getElementById('parent-unlock-area').style.display = 'none';
                    document.getElementById('parent-active-area').style.display = 'flex';
                    alert('Đã bật chế độ Phụ Huynh!');
                } else {
                    alert('Mã PIN không chính xác!');
                }
            } else {
                // Set new pin
                await window.pywebview.api.save_parent_pin(pin);
                isParentMode = true;
                document.getElementById('parent-mode-status').textContent = 'Chế độ: Phụ Huynh (Đã cài PIN)';
                document.getElementById('parent-mode-status').style.color = '#2ed573';
                document.getElementById('nav-parent-dashboard').style.display = 'flex';
                document.getElementById('parent-pin-input').value = '';
                document.getElementById('parent-unlock-area').style.display = 'none';
                document.getElementById('parent-active-area').style.display = 'flex';
                alert('Đã thiết lập mã PIN và bật chế độ Phụ Huynh! Học sinh sau này sẽ bị hạn chế và phải nhập PIN để xem Dashboard/Cài đặt.');
            }
        }
    });

    document.getElementById('switch-student-btn').addEventListener('click', () => {
        isParentMode = false;
        document.getElementById('parent-mode-status').textContent = 'Chế độ: Học sinh (Bị giới hạn)';
        document.getElementById('parent-mode-status').style.color = '#ff4757';
        document.getElementById('nav-parent-dashboard').style.display = 'none';
        document.getElementById('parent-unlock-area').style.display = 'flex';
        document.getElementById('parent-active-area').style.display = 'none';
        
        if (document.getElementById('dashboard').classList.contains('active-page')) {
            document.querySelector('[data-page="student-dashboard"]').click();
        }
        alert('Đã trao quyền điều khiển lại cho Học Sinh!');
    });

    document.getElementById('remove-pin-btn').addEventListener('click', async () => {
        if (confirm("Cảnh báo: Bạn có chắc chắn muốn hủy mã PIN? \nHọc sinh sẽ có lại toàn quyền truy cập AI Insights và bỏ chặn phần mềm!")) {
            if (window.pywebview && window.pywebview.api) {
                await window.pywebview.api.clear_parent_pin();
                checkParentMode();
                alert('Đã gỡ bỏ mã PIN. Phần mềm được mở khóa hoàn toàn.');
            }
        }
    });

    async function loadDashboard() {
        if (!window.pywebview || !window.pywebview.api) return;
        
        const isParent = window.currentUserRole === 'parent';
        const targetId = isParent ? window.linkedStudentId : window.currentUserId;
        
        // Handle Parent Linking View
        const linkingArea = document.getElementById('parent-linking-area');
        if (isParent && !window.linkedStudentId) {
            if (linkingArea) linkingArea.style.display = 'block';
            document.getElementById('dash-main-title').textContent = "Giám Sát Học Tập";
            document.getElementById('dash-main-subtitle').textContent = "Vui lòng liên kết tài khoản của con để xem tiến độ.";
            return;
        } else {
            if (linkingArea) linkingArea.style.display = 'none';
        }

        // Fetch Data
        let profile, schedules, dashData;
        try {
            if (isParent) {
                profile = await window.pywebview.api.get_remote_user_profile(targetId);
                schedules = await window.pywebview.api.get_remote_schedules(targetId);
                document.getElementById('dash-main-title').textContent = `Giám Sát: ${profile.full_name || 'Con'}`;
                document.getElementById('dash-main-subtitle').textContent = "Đang theo dõi lộ trình học tập của con.";
            } else {
                profile = await window.pywebview.api.get_user_profile();
                schedules = await window.pywebview.api.get_schedules();
                document.getElementById('dash-main-title').textContent = "Góc Học Tập";
                document.getElementById('dash-main-subtitle').textContent = "Tổng quan tình trạng tập trung và lịch biểu hôm nay.";
            }
            dashData = await window.pywebview.api.get_dashboard_data();
        } catch (e) {
            console.error("Dashboard data fetch failed", e);
            return;
        }

        if (profile) {
            const xpDisp = document.getElementById('dash-xp-display');
            const lvDisp = document.getElementById('dash-level-display');
            if (xpDisp) xpDisp.textContent = `Điểm kinh nghiệm: ${profile.total_xp || 0} XP`;
            if (lvDisp) lvDisp.textContent = `Cấp độ: ${profile.level || 1}`;
            
            // Focus Time
            const hours = Math.floor((dashData?.today_focus_seconds || 0) / 3600);
            const mins = Math.floor(((dashData?.today_focus_seconds || 0) % 3600) / 60);
            const focusDisp = document.getElementById('dash-focus-time');
            if (focusDisp) focusDisp.textContent = `${hours}h ${mins}m`;
        }

        // Blocked Summary
        const blockList = document.getElementById('dash-block-list');
        const totalBlocks = document.getElementById('dash-total-blocks');
        if (totalBlocks) totalBlocks.textContent = `${dashData?.total_blocks_today || 0} LẦN`;
        if (blockList && dashData?.blocked_apps) {
            blockList.innerHTML = '';
            dashData.blocked_apps.slice(0, 4).forEach(app => {
                blockList.innerHTML += `<i data-lucide="${getIconForApp(app)}"></i>`;
            });
        }

        // Render Schedules
        const scheduleList = document.getElementById('dash-schedule-list');
        if (scheduleList) {
            scheduleList.innerHTML = '';
            if (!schedules || schedules.length === 0) {
                scheduleList.innerHTML = '<p style="color:var(--text-secondary); font-size:13px; padding: 20px;">Lịch học hôm nay đang trống.</p>';
            } else {
                schedules.slice(0, 3).forEach(s => {
                    scheduleList.innerHTML += `
                        <div class="timeline-item-mini" style="display:flex; justify-content:space-between; align-items:center; padding-bottom:12px; border-bottom:1px solid var(--border-color); margin-bottom:12px;">
                            <div>
                                <h6 style="margin:0; font-size:14px;">${s.task}</h6>
                                <p style="margin:4px 0 0; font-size:12px; color:var(--text-secondary);">${s.time} - ${s.duration}m</p>
                            </div>
                            <span class="status-dot ${s.strict_mode ? 'active' : ''}"></span>
                        </div>
                    `;
                });
            }
        }

        // AI Insights
        const insightsElem = document.getElementById('dash-ai-insights');
        if (insightsElem) {
            insightsElem.textContent = isParent ? "Đang phân tích lộ trình của con..." : "Đang phân tích thói quen...";
            window.pywebview.api.get_ai_insights().then(text => {
                insightsElem.textContent = text;
            });
        }
        
        if (window.lucide) window.lucide.createIcons();
    }

    function getIconForApp(appName) {
        const lower = appName.toLowerCase();
        if (lower.includes('youtube')) return 'video';
        if (lower.includes('facebook') || lower.includes('tiktok')) return 'message-circle';
        if (lower.includes('game') || lower.includes('steam')) return 'gamepad-2';
        return 'shield-alert';
    }

    // Refresh Dashboard quietly every 10 seconds if it is open
    setInterval(() => {
        const isParentActive = document.getElementById('dashboard').classList.contains('active-page');
        const isStudentActive = document.getElementById('student-dashboard').classList.contains('active-page');
        
        if (isParentActive || isStudentActive) {
            window.pywebview.api.get_dashboard_data().then(data => {
                if (!data) return;
                const hours = Math.floor(data.today_focus_seconds / 3600);
                const mins = Math.floor((data.today_focus_seconds % 3600) / 60);
                
                if (document.getElementById('dash-focus-time')) document.getElementById('dash-focus-time').textContent = `${hours}h ${mins}m`;
                if (document.getElementById('st-focus-time')) document.getElementById('st-focus-time').textContent = `${hours}h ${mins}m`;
                
                const blocksCount = Object.keys(data.blocked_summary_today || {}).length;
                if (document.getElementById('dash-goals-met')) document.getElementById('dash-goals-met').textContent = `${blocksCount}/10`;
            });
        }
    }, 10000);

    // --- Gamification & Badges ---
    const ALL_BADGES = {
        academic: [
            { id: "calculus_master", icon: "calculator", color: "#0984e3", title: "Toán Học Đỉnh Cao", desc: "Hoàn thành bài tập nâng cao chuẩn xác." },
            { id: "history_buff", icon: "book-open", color: "#6c5ce7", title: "Sử Gia Dễ Thương", desc: "Thành thạo module Lịch sử trong thời gian kỷ lục." },
            { id: "science_sage", icon: "flask-conical", color: "#e84393", title: "Nhà Khoa Học Gia", desc: "Trả lời chính xác bộ câu hỏi thực hành khó nhất." }
        ],
        focus: [
            { id: "focus_4h", icon: "zap", color: "#0984e3", title: "4h Focus Streak", desc: "Học tập trung liên tiếp 4 tiếng." },
            { id: "distraction_free", icon: "minus-circle", color: "#6c5ce7", title: "Tuần Vô Nhiễm", desc: "Cả tuần không bị khóa app xao nhãng." }
        ],
        consistency: [
            { id: "streak_14", icon: "flame", color: "#ff7675", title: "14 Day Streak", desc: "Điểm danh học tập 14 ngày liên tiếp." },
            { id: "early_bird", icon: "sunrise", color: "#b2bec3", title: "Early Bird", desc: "Bắt đầu ca học đầu tiên trước 6h sáng." }
        ]
    };

    function createBadgeHtml(b) {
        return `
            <div class="badge-box">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div class="badge-icon-sq" style="background: ${b.color}20;"><i data-lucide="${b.icon}" style="color: ${b.color};"></i></div>
                </div>
                <h4 style="margin: 16px 0 8px 0; font-size: 15px;">${b.title}</h4>
                <p style="font-size: 12px; color: var(--text-secondary); line-height: 1.5;">${b.desc}</p>
                <div class="badge-date"><i data-lucide="calendar" style="width:12px;height:12px;"></i> ĐÃ ĐẠT ĐƯỢC</div>
            </div>
        `;
    }

    function createSmBadgeHtml(b) {
        return `
            <div class="badge-box sm">
                <div class="badge-icon-sq" style="background: ${b.color}20;"><i data-lucide="${b.icon}" style="color: ${b.color};"></i></div>
                <div>
                    <h4 style="font-size: 14px; margin-bottom: 4px;">${b.title}</h4>
                    <p style="font-size: 11px; color: var(--text-secondary); line-height: 1.4;">${b.desc}</p>
                </div>
            </div>
        `;
    }

    async function loadAchievements() {
        if (!window.pywebview || !window.pywebview.api) return;
        const profile = await window.pywebview.api.get_user_profile();
        if(!profile) return;
        
        document.getElementById('ach-current-xp').textContent = `${profile.xp.toLocaleString()} XP`;
        document.getElementById('ach-target-xp').textContent = `${profile.next_level_xp.toLocaleString()} XP`;
        document.getElementById('ach-level-text').innerHTML = `Level ${profile.level}: <span>${profile.rank_name}</span>`;
        document.getElementById('ach-next-level').textContent = `Next: Level ${profile.level + 1}`;
        document.getElementById('ach-total-badges').textContent = profile.total_badges || 0;
        
        const nextXp = profile.next_level_xp;
        if(nextXp > 0) {
            const percent = (profile.xp - profile.prev_level_xp) / (nextXp - profile.prev_level_xp) * 100;
            const p = Math.min(100, Math.max(0, percent));
            document.getElementById('ach-xp-bar').style.width = p + '%';
            document.getElementById('ach-percent').textContent = Math.round(p) + '%';
        } else {
            document.getElementById('ach-xp-bar').style.width = '100%';
            document.getElementById('ach-percent').textContent = 'MAX';
        }
        
        const btn = document.getElementById('ach-check-in-btn');
        if(btn) {
            if(profile.checked_in_today) {
                btn.disabled = true;
                btn.style.opacity = '0.5';
                btn.innerHTML = `<i data-lucide="check-circle" style="width:16px; margin-right:6px;"></i> ĐÃ ĐIỂM DANH`;
            } else {
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.innerHTML = `<i data-lucide="check-circle" style="width:16px; margin-right:6px;"></i> ĐIỂM DANH`;
            }
        }
        
        // Render unlocked badges
        const unlocked = profile.unlocked_badges || [];
        
        // Academic
        let accHtml = '';
        ALL_BADGES.academic.forEach(b => {
             if(unlocked.includes(b.id)) accHtml += createBadgeHtml(b);
        });
        document.getElementById('academic-badges').innerHTML = accHtml || '<p style="color:var(--text-secondary); font-size:13px; grid-column: span 3;">Chưa có danh hiệu nào.</p>';
        
        // Focus
        let focHtml = '';
        ALL_BADGES.focus.forEach(b => {
             if(unlocked.includes(b.id)) focHtml += createSmBadgeHtml(b);
        });
        document.getElementById('focus-badges').innerHTML = focHtml || '<p style="color:var(--text-secondary); font-size:13px;">Tiếp tục học để mở khóa.</p>';
        
        // Consistency
        let conHtml = '';
        ALL_BADGES.consistency.forEach(b => {
             if(unlocked.includes(b.id)) conHtml += createSmBadgeHtml(b);
        });
        document.getElementById('consistency-badges').innerHTML = conHtml || '<p style="color:var(--text-secondary); font-size:13px;">Hãy chuỗi ngày nỗ lực để mở khóa.</p>';
        
        if (window.lucide) window.lucide.createIcons();
    }

    // --- Parent Monitoring Logic ---
    async function loadParentMonitoring() {
        const unlinkedView = document.getElementById('parent-unlinked-view');
        const linkedView = document.getElementById('parent-linked-view');
        
        if (!window.linkedStudentId) {
            unlinkedView.style.display = 'block';
            linkedView.style.display = 'none';
            return;
        }

        unlinkedView.style.display = 'none';
        linkedView.style.display = 'block';

        const child = await window.pywebview.api.get_remote_user_profile(window.linkedStudentId);
        if (child) {
            document.getElementById('child-name').textContent = child.full_name || "Con của bạn";
            document.getElementById('child-level').textContent = `Level ${child.level || 1}`;
            document.getElementById('child-xp').textContent = `${child.total_xp || 0} XP`;
            document.getElementById('child-badges').textContent = child.badges_count || 0;
            
            // Load child's schedules
            const schedules = await window.pywebview.api.get_remote_schedules(window.linkedStudentId);
            renderChildSchedules(schedules);
        }
    }

    function renderChildSchedules(schedules) {
        const list = document.getElementById('parent-child-schedule-list');
        list.innerHTML = '';
        if (schedules.length === 0) {
            list.innerHTML = '<p style="color:var(--text-secondary); font-size:13px; padding: 20px;">Con chưa có lịch học nào.</p>';
        } else {
            schedules.forEach(s => {
                list.innerHTML += `
                    <div style="display:flex; justify-content:space-between; align-items:center; padding:12px; background:rgba(255,255,255,0.02); border:1px solid var(--border-color); border-radius:10px; margin-bottom:10px;">
                        <div>
                            <h6 style="margin:0; font-size:14px;">${s.task}</h6>
                            <p style="margin:2px 0 0; font-size:12px; color:var(--text-secondary);">${s.time} - ${s.duration} phút</p>
                        </div>
                        <button onclick="deleteChildSchedule(${s.id})" style="background:transparent; border:none; color:var(--danger); cursor:pointer;"><i data-lucide="trash-2" style="width:16px;"></i></button>
                    </div>
                `;
            });
        }
        if (window.lucide) lucide.createIcons();
    }

    window.deleteChildSchedule = async (id) => {
        if (!confirm("Bạn có chắc chắn muốn xóa lịch học này của con không?")) return;
        const res = await window.pywebview.api.delete_remote_schedule(window.linkedStudentId, id);
        if (res.success) {
            window.showAIToast("Đã xóa lịch học của con thành công!");
            loadParentMonitoring();
        }
    };

    document.getElementById('parent-link-confirm-btn').addEventListener('click', async () => {
        const code = document.getElementById('parent-link-input').value.trim();
        if (!code) return;
        const res = await window.pywebview.api.link_parent_student(code);
        if (res.success) {
            alert("Liên kết thành công!");
            // Update linkedStudentId from profile
            const profile = await window.pywebview.api.get_user_profile();
            window.linkedStudentId = profile.linked_student_id;
            loadParentMonitoring();
        } else {
            alert(res.message);
        }
    });

    document.getElementById('parent-add-schedule-trigger').addEventListener('click', () => {
        const task = prompt("Tên bài học của con:");
        const time = prompt("Giờ bắt đầu (HH:MM):", "08:00");
        const duration = prompt("Thời lượng (phút):", "45");
        if (task && time && duration) {
            window.pywebview.api.add_remote_schedule(window.linkedStudentId, task, time, parseInt(duration)).then(res => {
                if (res.success) {
                    window.showAIToast("Đã thêm lịch học mới cho con!");
                    loadParentMonitoring();
                }
            });
        }
    });

    // --- AI Command Parsing ---
    async function handleAICommand(text) {
        // Create Schedule: [[CREATE_SCHEDULE: Task, Time, Duration]]
        const createMatch = text.match(/\[\[CREATE_SCHEDULE:\s*(.*?),\s*(.*?),\s*(.*?)\]\]/);
        if (createMatch) {
            const [_, task, time, duration] = createMatch;
            await window.pywebview.api.add_schedule(task, time, parseInt(duration), true);
            window.showAIToast(`🤖 AI: Tớ đã tự động thêm lịch học <b>${task}</b> vào lúc ${time} cho bạn!`);
            if (document.getElementById('nav-schedule').classList.contains('active')) loadSchedules();
            if (document.getElementById('student-dashboard').classList.contains('active-page')) loadDashboard();
        }

        // Delete Schedule: [[DELETE_SCHEDULE: TaskName]]
        const deleteMatch = text.match(/\[\[DELETE_SCHEDULE:\s*(.*?)\]\]/);
        if (deleteMatch) {
            const taskName = deleteMatch[1].trim();
            const res = await window.pywebview.api.delete_schedule_by_name(taskName);
            if (res.success) {
                window.showAIToast(`🤖 AI: Đã xóa lịch <b>${taskName}</b> theo yêu cầu của bạn.`);
                if (document.getElementById('nav-schedule').classList.contains('active')) loadSchedules();
                if (document.getElementById('student-dashboard').classList.contains('active-page')) loadDashboard();
            }
        }
    }

    // --- Profile Form Logic ---
    async function loadUserProfileSettings() {
        if (!window.pywebview || !window.pywebview.api) return;
        const p = await window.pywebview.api.get_user_profile();
        if(!p) return;
        
        document.getElementById('prof-display-name').textContent = p.full_name || "Tài khoản Sinh viên";
        document.getElementById('prof-display-email').textContent = p.email || "student@neuralis.ai";
        document.getElementById('prof-join-date').textContent = p.joined_date || "Hôm nay";
        
        document.getElementById('prof-name').value = p.full_name || "";
        document.getElementById('prof-email').value = p.email || "";
        document.getElementById('prof-address').value = p.address || "";
        document.getElementById('prof-father').value = p.father_name || "";
        document.getElementById('prof-mother').value = p.mother_name || "";
        document.getElementById('prof-parent-code').value = p.parent_code || "";
    }

    const saveProfileBtn = document.getElementById('save-profile-btn');
    if (saveProfileBtn) {
        saveProfileBtn.addEventListener('click', async () => {
            if (!window.pywebview || !window.pywebview.api) return;
            const data = {
                full_name: document.getElementById('prof-name').value,
                email: document.getElementById('prof-email').value,
                address: document.getElementById('prof-address').value,
                father_name: document.getElementById('prof-father').value,
                mother_name: document.getElementById('prof-mother').value,
                parent_code: document.getElementById('prof-parent-code').value
            };
            
            // Xử lý Liên Kết Phụ Huynh riêng biệt
            if (isParentMode && data.parent_code) {
                const linkRes = await window.pywebview.api.link_parent_account(data.parent_code);
                if (linkRes.success) {
                    window.showAIToast("Đã liên kết Học sinh thành công!");
                } else {
                    window.showAIToast("Lỗi liên kết: " + linkRes.message);
                    return;
                }
            }
            
            const res = await window.pywebview.api.update_user_profile(data);
            if (res.success) {
                window.showAIToast(res.message);
                loadUserProfileSettings();
                document.getElementById('sidebar-profile').querySelector('#profile-name').textContent = data.full_name || "Tài khoản";
            } else {
                window.showAIToast("Lỗi: " + res.message);
            }
        });
    }

    // --- Leaderboard Logic ---
    async function loadLeaderboard() {
        if (!window.pywebview || !window.pywebview.api) return;
        const listDiv = document.getElementById('leaderboard-list');
        listDiv.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 40px 0;">Đang đồng bộ Đám Mây...</div>';
        
        const top_users = await window.pywebview.api.get_leaderboard();
        listDiv.innerHTML = '';
        
        if (!top_users || top_users.length === 0) {
            listDiv.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 40px 0;">Chưa có dữ liệu thi đấu.</div>';
            return;
        }
        
        top_users.forEach((u, idx) => {
            let color = "var(--text-secondary)";
            let rankText = `#${idx + 1}`;
            if (idx === 0) { color = "#FFD700"; rankText = "🏆 #1"; }
            if (idx === 1) { color = "#C0C0C0"; rankText = "🥈 #2"; }
            if (idx === 2) { color = "#CD7F32"; rankText = "🥉 #3"; }
            
            const row = document.createElement('div');
            row.style.cssText = `display: flex; justify-content: space-between; align-items: center; padding: 16px 0; border-bottom: 1px solid rgba(255,255,255,0.05); transition: 0.2s;`;
            row.innerHTML = `
                <div style="width: 50px; font-weight: bold; font-size: 16px; color: ${color};">${rankText}</div>
                <div style="flex: 1; display: flex; align-items: center; gap: 12px;">
                    <div style="width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #6c5ce7, #a29bfe); display: flex; align-items: center; justify-content: center; font-weight: bold; color: white;">
                        ${(u.full_name || u.username).substring(0,1).toUpperCase()}
                    </div>
                    <div>
                        <div style="font-weight: 600; font-size: 15px;">${u.full_name || u.username}</div>
                        <div style="font-size: 12px; color: var(--text-secondary);">@${u.username}</div>
                    </div>
                </div>
                <div style="width: 100px; text-align: center; font-weight: 600; color: #00ff88;">Lv ${u.level}</div>
                <div style="width: 100px; text-align: right; font-weight: bold; color: #a29bfe;">${u.total_xp} XP</div>
            `;
            listDiv.appendChild(row);
        });
    }

    // --- Split Layout Resizer Logic ---
    const resizers = document.querySelectorAll('.split-resizer');
    let isResizing = false;
    let currentX = 0;
    let initialWidth = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--inner-sidebar-width')) || 320;
    
    // Khôi phục chiều rộng đã lưu
    const savedSidebarWidth = localStorage.getItem('app-inner-sidebar-width');
    if (savedSidebarWidth) {
        document.documentElement.style.setProperty('--inner-sidebar-width', savedSidebarWidth + 'px');
        initialWidth = parseInt(savedSidebarWidth);
    }
    
    resizers.forEach(resizer => {
        resizer.addEventListener('mousedown', function(e) {
            isResizing = true;
            currentX = e.clientX;
            const rootStyle = getComputedStyle(document.documentElement);
            initialWidth = parseInt(rootStyle.getPropertyValue('--inner-sidebar-width')) || 320;
            resizer.classList.add('active');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none'; // Ngăn bôi đen chữ khi dính chuột
        });
    });

    document.addEventListener('mousemove', function(e) {
        if (!isResizing) return;
        const dx = e.clientX - currentX;
        let newWidth = initialWidth + dx;
        if (newWidth < 250) newWidth = 250; // min width
        if (newWidth > 600) newWidth = 600; // max width
        document.documentElement.style.setProperty('--inner-sidebar-width', newWidth + 'px');
    });

    document.addEventListener('mouseup', function() {
        if (isResizing) {
            isResizing = false;
            resizers.forEach(r => r.classList.remove('active'));
            document.body.style.cursor = 'default';
            document.body.style.userSelect = 'auto';
            const finalWidth = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--inner-sidebar-width'));
            localStorage.setItem('app-inner-sidebar-width', finalWidth);
        }
    });

    // --- Chat functionality ---
    let currentSessionId = null;
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const chatHistory = document.getElementById('chat-history');
    const chatSessionsList = document.getElementById('chat-sessions-list');
    const newChatBtn = document.getElementById('new-chat-btn');
    const chatTitleDisplay = document.getElementById('chat-title-display');

    async function loadChatSessions() {
        if (!window.pywebview || !window.pywebview.api) return;
        const sessions = await window.pywebview.api.get_chat_sessions();
        chatSessionsList.innerHTML = '';
        
        if (sessions.length === 0) {
            createNewSession();
            return;
        }

        sessions.forEach(s => {
            const div = document.createElement('div');
            div.className = 'chat-session-item';
            div.textContent = s.title;
            if (s.id === currentSessionId) div.classList.add('active');
            
            div.addEventListener('click', () => {
                selectSession(s.id, s.title, div);
            });
            chatSessionsList.appendChild(div);
        });

        if (!currentSessionId) {
            selectSession(sessions[0].id, sessions[0].title, chatSessionsList.firstChild);
        }
    }

    async function selectSession(id, title, elem) {
        currentSessionId = id;
        chatTitleDisplay.textContent = title;
        document.querySelectorAll('.chat-session-item').forEach(el => el.classList.remove('active'));
        if (elem) elem.classList.add('active');
        
        // Load message history
        chatHistory.innerHTML = '';
        if (window.pywebview && window.pywebview.api) {
            const history = await window.pywebview.api.get_chat_history(id);
            if (history.length === 0) {
                appendMessage('ai', 'Chào bạn! Phiên trò chuyện mới đã khởi tạo. Bạn muốn thảo luận gì?');
            } else {
                history.forEach(msg => appendMessage(msg.role, msg.content));
            }
        }
    }

    async function createNewSession(title = 'Trò chuyện mới') {
        if (!window.pywebview || !window.pywebview.api) return;
        const newId = await window.pywebview.api.create_chat_session(title);
        currentSessionId = newId;
        await loadChatSessions();
        selectSession(newId, title, chatSessionsList.firstChild);
    }

    newChatBtn.addEventListener('click', () => {
        createNewSession("Phiên thảo luận " + new Date().toLocaleTimeString());
    });

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;
        
        if (!currentSessionId) {
            await createNewSession(text.substring(0, 30) + (text.length > 30 ? "..." : ""));
        } else {
            // Rename session to match first topic if it's the very first message sent
            const userMessagesCount = chatHistory.querySelectorAll('.user-message').length;
            if (userMessagesCount === 0) {
                const newTitle = text.substring(0, 30) + (text.length > 30 ? "..." : "");
                chatTitleDisplay.textContent = newTitle;
                document.querySelectorAll('.chat-session-item.active').forEach(e => e.textContent = newTitle);
                if (window.pywebview && window.pywebview.api) {
                    window.pywebview.api.rename_chat_session(currentSessionId, newTitle);
                }
            }
        }

        // Add user message
        appendMessage('user', text);
        chatInput.value = '';

        // Add loading indicator
        const loadingId = 'msg-' + Date.now();
        appendMessage('ai', '...', loadingId);

        // Call Python Backend
        try {
            if (window.pywebview && window.pywebview.api) {
                const response = await window.pywebview.api.chat_with_ai(currentSessionId, text);
                updateMessage(loadingId, response);
                handleAICommand(response);
            } else {
                setTimeout(() => updateMessage(loadingId, 'Mock AI response...'), 1000);
            }
        } catch (err) {
            updateMessage(loadingId, 'Lỗi kết nối AI: ' + err);
        }
    }

    sendBtn.addEventListener('click', () => sendMessage());
    chatInput.addEventListener('keydown', (e) => {
        // Hỗ trợ gõ dấu tiếng Việt (TELEX/VNI) không bị nhận diện nhầm phím Enter
        if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
            e.preventDefault();
            sendMessage();
        }
    });

    function formatMarkdown(text) {
        if (window.marked) {
            return marked.parse(text);
        }
        return text;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function appendMessage(sender, text, id = null) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}-message`;
        if (id) msgDiv.id = id;
        
        const avatar = sender === 'ai' ? '<div class="avatar"><i data-lucide="bot"></i></div>' : '';
        let contentHtml = sender === 'ai' ? formatMarkdown(text) : escapeHtml(text);
        
        const bubble = `<div class="bubble markdown-body">${contentHtml}</div>`;
        
        msgDiv.innerHTML = `${avatar}${bubble}`;
        chatHistory.appendChild(msgDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        if (window.lucide) window.lucide.createIcons();
    }

    function updateMessage(id, text) {
        const msgDiv = document.getElementById(id);
        if (msgDiv) {
            let contentHtml = msgDiv.classList.contains('ai-message') ? formatMarkdown(text) : escapeHtml(text);
            msgDiv.querySelector('.bubble').innerHTML = contentHtml;
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
    }

    // Load and Save Settings (Sites, Apps)
    loadSettings();

    document.getElementById('add-website-btn').addEventListener('click', async () => {
        const input = document.getElementById('new-website');
        const site = input.value.trim();
        if (site) {
            if (window.pywebview && window.pywebview.api) {
                await window.pywebview.api.add_blocked_website(site);
                loadSettings();
            } else {
                addToList('blocked-websites', site);
            }
            input.value = '';
        }
    });

    document.getElementById('add-app-btn').addEventListener('click', async () => {
        const input = document.getElementById('new-app');
        const app = input.value.trim();
        if (app) {
            if (window.pywebview && window.pywebview.api) {
                await window.pywebview.api.add_blocked_app(app);
                loadSettings();
            } else {
                addToList('blocked-apps', app);
            }
            input.value = '';
        }
    });

    document.getElementById('save-settings-btn').addEventListener('click', async () => {
        const provider = providerSelect.value;
        const geminiKey = document.getElementById('api-key-input').value.trim();
        const openaiKey = document.getElementById('openai-key-input').value.trim();
        const xaiKey = document.getElementById('xai-key-input').value.trim();
        
        if (window.pywebview && window.pywebview.api) {
            await window.pywebview.api.save_ai_config(provider, geminiKey, openaiKey, xaiKey);
            alert("Đã lưu cấu hình AI.");
        }
    });

    function triggerAlarm(task, duration_mins, strictMode) {
        const overlay = document.getElementById('alarm-overlay');
        const title = document.getElementById('alarm-title');
        title.textContent = "Đã đến giờ: " + task;
        overlay.style.display = 'flex';

        // Tự động sinh đoạn chat mới về chủ đề bài học
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.create_chat_session("Phiên học: " + task).then(() => {
                loadChatSessions();
            });
        }

        const audio = new Audio('https://cdn.pixabay.com/download/audio/2021/08/04/audio_0625c1539c.mp3');
        audio.play().catch(e => console.log("Trình duyệt chặn Audio", e));
    }

    // Handle provider selection UI toggle
    const providerSelect = document.getElementById('ai-provider');
    const groupGemini = document.getElementById('group-gemini');
    const groupOpenai = document.getElementById('group-openai');
    const groupXai = document.getElementById('group-xai');

    providerSelect.addEventListener('change', () => {
        groupGemini.style.display = 'none';
        groupOpenai.style.display = 'none';
        groupXai.style.display = 'none';
        if(providerSelect.value === 'gemini') groupGemini.style.display = 'flex';
        if(providerSelect.value === 'openai') groupOpenai.style.display = 'flex';
        if(providerSelect.value === 'xai') groupXai.style.display = 'flex';
    });

    async function loadSettings() {
        if (!window.pywebview || !window.pywebview.api) return;
        const config = await window.pywebview.api.get_config();
        
        const webList = document.getElementById('blocked-websites');
        webList.innerHTML = '';
        config.websites.forEach(site => {
            const item = createListItem(site, () => removeSite(site));
            webList.appendChild(item);
        });

        const appList = document.getElementById('blocked-apps');
        appList.innerHTML = '';
        config.apps.forEach(app => {
            const item = createListItem(app, () => removeApp(app));
            appList.appendChild(item);
        });

        providerSelect.value = config.ai_provider || 'gemini';
        providerSelect.dispatchEvent(new Event('change'));
        
        document.getElementById('api-key-input').value = config.api_key || '';
        document.getElementById('openai-key-input').value = config.openai_api_key || '';
        document.getElementById('xai-key-input').value = config.xai_api_key || '';
    }

    async function removeSite(site) {
        if (window.pywebview && window.pywebview.api) {
            await window.pywebview.api.remove_blocked_website(site);
            loadSettings();
        }
    }

    async function removeApp(app) {
        if (window.pywebview && window.pywebview.api) {
            await window.pywebview.api.remove_blocked_app(app);
            loadSettings();
        }
    }

    // Schedule logic
    document.getElementById('add-schedule-btn').addEventListener('click', async () => {
        const task = document.getElementById('task-name').value;
        const start = document.getElementById('start-time').value; // format HH:MM
        const duration = parseInt(document.getElementById('duration').value);
        const strictMode = document.getElementById('strict-mode').checked;

        if (!task || !start || !duration) {
            alert("Vui lòng nhập đủ thông tin lịch học!");
            return;
        }

        if (window.pywebview && window.pywebview.api) {
            await window.pywebview.api.add_schedule(task, start, duration, strictMode);
            loadSchedules();
        } else {
            addToList('schedule-list', `${task} - ${start} (${duration} phút) ${strictMode ? '[Cấm Game]' : ''}`);
        }
    });

    async function loadSchedules() {
        if (!window.pywebview || !window.pywebview.api) return;
        const schedules = await window.pywebview.api.get_schedules();
        const list = document.getElementById('schedule-list');
        list.innerHTML = '';
        schedules.forEach(s => {
            const strictText = s.strict_mode ? '<span style="color: #ff4444">[Khóa Game/Web]</span>' : '<span style="color: #00ff88">[Chỉ nhắc nhở]</span>';
            const text = `${s.task} - ${s.time} (${s.duration} phút) ${strictText}`;
            const item = createListItem(text, () => removeSchedule(s.id));
            // make list item render HTML safely
            item.querySelector('span').innerHTML = text;
            list.appendChild(item);
        });
    }

    async function removeSchedule(id) {
        if (window.pywebview && window.pywebview.api) {
            await window.pywebview.api.remove_schedule(id);
            loadSchedules();
        }
    }

    function createListItem(text, removeCallback) {
        const div = document.createElement('div');
        div.className = 'block-item';
        div.innerHTML = `<span>${text}</span> <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="remove-btn" style="cursor:pointer; width: 16px; height: 16px;"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>`;
        div.querySelector('.remove-btn').addEventListener('click', removeCallback);
        return div;
    }

    function addToList(listId, text) {
        const list = document.getElementById(listId);
        list.appendChild(createListItem(text, function() {
            this.parentElement.remove();
        }));
    }

    // Alarm UI control exposed to Python
    window.showAlarm = function(taskName) {
        document.getElementById('alarm-desc').textContent = "Nhiệm vụ: " + taskName;
        document.getElementById('alarm-overlay').classList.add('show');
        window.startFocusMode();
    };

    document.getElementById('start-study-btn').addEventListener('click', () => {
        document.getElementById('alarm-overlay').classList.remove('show');
    });

    window.startFocusMode = function(duration_mins, strictMode) {
        document.getElementById('system-status').textContent = "Đang tập trung";
        document.getElementById('system-status').style.color = "#ff4757";
        document.querySelector('.pulse-dot').style.backgroundColor = "#ff4757";
        document.querySelector('.pulse-dot').style.boxShadow = "0 0 8px #ff4757";
        
        // Chỉ có phụ huynh mới có quyền dùng nút Dừng Khẩn Cấp.
        if (isParentMode) {
            document.getElementById('emergency-stop-btn').style.display = "flex";
        } else {
            document.getElementById('emergency-stop-btn').style.display = "none";
        }
    };

    // Emergency stop logic
    document.getElementById('emergency-stop-btn').addEventListener('click', async () => {
        if(confirm("Bạn có chắc chắn muốn TẮT chế độ tập trung ngay lúc này không? Mọi trang web và game sẽ được mở khóa.")) {
            if (window.pywebview && window.pywebview.api) {
                await window.pywebview.api.stop_focus_mode();
                window.endFocusMode();
            }
        }
    });

    window.endFocusMode = function() {
        document.getElementById('system-status').textContent = "Sẵn sàng";
        document.getElementById('system-status').style.color = "var(--text-secondary)";
        document.querySelector('.pulse-dot').style.backgroundColor = "#00ff88";
        document.querySelector('.pulse-dot').style.boxShadow = "0 0 8px #00ff88";
        document.getElementById('emergency-stop-btn').style.display = "none";
    };

    window.showBlockWarning = function(appName) {
        document.getElementById('killed-app-name').textContent = appName;
        const warningOverlay = document.getElementById('warning-overlay');
        warningOverlay.classList.add('show');
        
        // Auto hide after 4 seconds
        setTimeout(() => {
            warningOverlay.classList.remove('show');
        }, 4000);
    };

    // Initial loads removed from here, moved to post-login
} // FINAL CLOSING OF initApp
