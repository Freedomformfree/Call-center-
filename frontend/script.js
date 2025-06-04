// VoiceConnect Pro - Frontend JavaScript
// Retro minimalistic animations and interactions

// Global state
let isLoggedIn = false;
let currentUser = null;
let currentLanguage = 'en';
let originalTexts = new Map();

// DOM Content Loaded with error handling
document.addEventListener('DOMContentLoaded', function() {
    try {
        // Performance optimization: Use requestAnimationFrame for smooth animations
        requestAnimationFrame(() => {
            initializeAnimations();
            initializeScrollEffects();
            initializeTypingEffect();
            initializeTerminalAnimation();
            initializePerformanceOptimizations();
        });
    } catch (error) {
        console.error('Error initializing website:', error);
        // Fallback: basic functionality without animations
        initializeBasicFunctionality();
    }
});

// Initialize animations
function initializeAnimations() {
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add scroll-triggered animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);

    // Observe elements for animation
    document.querySelectorAll('.service-card, .feature-item, .pricing-card').forEach(el => {
        observer.observe(el);
    });
}

// Initialize scroll effects
function initializeScrollEffects() {
    let lastScrollTop = 0;
    const navbar = document.querySelector('.navbar');

    window.addEventListener('scroll', () => {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Navbar hide/show on scroll
        if (scrollTop > lastScrollTop && scrollTop > 100) {
            navbar.style.transform = 'translateY(-100%)';
        } else {
            navbar.style.transform = 'translateY(0)';
        }
        
        lastScrollTop = scrollTop;

        // Parallax effect for hero section
        const hero = document.querySelector('.hero');
        if (hero) {
            const scrolled = window.pageYOffset;
            const parallax = scrolled * 0.5;
            hero.style.transform = `translateY(${parallax}px)`;
        }
    });
}

// Initialize typing effect
function initializeTypingEffect() {
    const typingText = document.querySelector('.typing-text');
    if (!typingText) return;

    const texts = [
        'AI-Powered Call Center',
        'Smart Business Automation',
        'Intelligent Customer Engagement',
        'Next-Gen Communication Hub'
    ];
    
    let textIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    let typeSpeed = 100;

    function typeWriter() {
        const currentText = texts[textIndex];
        
        if (isDeleting) {
            typingText.textContent = currentText.substring(0, charIndex - 1);
            charIndex--;
            typeSpeed = 50;
        } else {
            typingText.textContent = currentText.substring(0, charIndex + 1);
            charIndex++;
            typeSpeed = 100;
        }

        if (!isDeleting && charIndex === currentText.length) {
            typeSpeed = 2000; // Pause at end
            isDeleting = true;
        } else if (isDeleting && charIndex === 0) {
            isDeleting = false;
            textIndex = (textIndex + 1) % texts.length;
            typeSpeed = 500; // Pause before next text
        }

        setTimeout(typeWriter, typeSpeed);
    }

    typeWriter();
}

// Initialize terminal animation
function initializeTerminalAnimation() {
    const terminalOutput = document.querySelector('.terminal-output');
    if (!terminalOutput) return;

    // Add glitch effect to terminal
    setInterval(() => {
        if (Math.random() < 0.1) { // 10% chance
            terminalOutput.style.filter = 'hue-rotate(90deg)';
            setTimeout(() => {
                terminalOutput.style.filter = 'none';
            }, 100);
        }
    }, 2000);
}

// Modal functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // Add entrance animation
        const modalContent = modal.querySelector('.modal-content');
        modalContent.style.animation = 'modalSlideIn 0.3s ease';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        const modalContent = modal.querySelector('.modal-content');
        modalContent.style.animation = 'modalSlideOut 0.3s ease';
        
        setTimeout(() => {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }, 300);
    }
}

function switchModal(fromModalId, toModalId) {
    closeModal(fromModalId);
    setTimeout(() => {
        openModal(toModalId);
    }, 300);
}

// Close modal when clicking outside
window.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        const modalId = event.target.id;
        closeModal(modalId);
    }
});

// Scroll to section
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Authentication handlers
async function handleLogin(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    
    const loginData = {
        email: formData.get('email') || form.querySelector('input[type="email"]').value,
        password: formData.get('password') || form.querySelector('input[type="password"]').value
    };

    try {
        showLoading(form);
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // Mock successful login
        isLoggedIn = true;
        currentUser = {
            email: loginData.email,
            name: 'John Doe',
            plan: 'professional'
        };
        
        hideLoading(form);
        closeModal('loginModal');
        showNotification('Welcome back! Redirecting to dashboard...', 'success');
        
        // Redirect to dashboard after delay
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 2000);
        
    } catch (error) {
        hideLoading(form);
        showNotification('Login failed. Please try again.', 'error');
    }
}

async function handleSignup(event) {
    event.preventDefault();
    const form = event.target;
    const inputs = form.querySelectorAll('input');
    
    const signupData = {
        name: inputs[0].value,
        email: inputs[1].value,
        company: inputs[2].value,
        phone: inputs[3].value,
        password: inputs[4].value
    };

    try {
        showLoading(form);
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Mock successful signup
        isLoggedIn = true;
        currentUser = {
            email: signupData.email,
            name: signupData.name,
            company: signupData.company,
            plan: 'starter'
        };
        
        hideLoading(form);
        closeModal('signupModal');
        showNotification('Account created successfully! Setting up your dashboard...', 'success');
        
        // Redirect to onboarding
        setTimeout(() => {
            window.location.href = '/onboarding';
        }, 2000);
        
    } catch (error) {
        hideLoading(form);
        showNotification('Signup failed. Please try again.', 'error');
    }
}

// Contact form handler
async function submitContactForm(event) {
    event.preventDefault();
    const form = event.target;
    const inputs = form.querySelectorAll('input, textarea');
    
    const contactData = {
        name: inputs[0].value,
        email: inputs[1].value,
        company: inputs[2].value,
        message: inputs[3].value
    };

    try {
        showLoading(form);
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        hideLoading(form);
        form.reset();
        showNotification('Message sent successfully! We\'ll get back to you soon.', 'success');
        
    } catch (error) {
        hideLoading(form);
        showNotification('Failed to send message. Please try again.', 'error');
    }
}

// Plan selection
function selectPlan(planName) {
    // Store selected plan
    localStorage.setItem('selectedPlan', planName);
    
    // Show plan selection feedback
    showNotification(`${planName.charAt(0).toUpperCase() + planName.slice(1)} plan selected!`, 'success');
    
    // Open signup modal if not logged in
    if (!isLoggedIn) {
        setTimeout(() => {
            openModal('signupModal');
        }, 1000);
    } else {
        // Redirect to billing
        setTimeout(() => {
            window.location.href = `/billing?plan=${planName}`;
        }, 1000);
    }
}

// Utility functions
function showLoading(form) {
    const button = form.querySelector('button[type="submit"]');
    if (button) {
        button.disabled = true;
        button.innerHTML = '<span class="loading-spinner"></span> Processing...';
        button.classList.add('loading');
    }
}

function hideLoading(form) {
    const button = form.querySelector('button[type="submit"]');
    if (button) {
        button.disabled = false;
        button.classList.remove('loading');
        
        // Restore original text based on form type
        if (form.classList.contains('auth-form')) {
            if (form.closest('#loginModal')) {
                button.innerHTML = 'Login';
            } else {
                button.innerHTML = 'Start Free Trial';
            }
        } else {
            button.innerHTML = 'Send Message';
        }
    }
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${getNotificationIcon(type)}</span>
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 3000;
        background: var(--bg-dark);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        max-width: 400px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        animation: slideInRight 0.3s ease;
    `;
    
    // Add type-specific styling
    if (type === 'success') {
        notification.style.borderColor = 'var(--success-color)';
    } else if (type === 'error') {
        notification.style.borderColor = 'var(--error-color)';
    }
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

function getNotificationIcon(type) {
    switch (type) {
        case 'success': return '✓';
        case 'error': return '✗';
        case 'warning': return '⚠';
        default: return 'ℹ';
    }
}

// Add CSS for notifications and loading
const additionalStyles = `
    .loading-spinner {
        display: inline-block;
        width: 12px;
        height: 12px;
        border: 2px solid transparent;
        border-top: 2px solid currentColor;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-right: 8px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
    
    @keyframes modalSlideOut {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-50px);
        }
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 12px;
        color: var(--text-primary);
        font-family: var(--font-mono);
    }
    
    .notification-close {
        background: none;
        border: none;
        color: var(--text-secondary);
        cursor: pointer;
        font-size: 18px;
        margin-left: auto;
        transition: var(--transition-fast);
    }
    
    .notification-close:hover {
        color: var(--text-primary);
    }
    
    .animate-in {
        animation: fadeInUp 0.6s ease forwards;
    }
    
    .btn-primary.loading {
        opacity: 0.7;
        cursor: not-allowed;
    }
`;

// Inject additional styles
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);

// Initialize matrix rain effect (optional retro touch)
function initializeMatrixRain() {
    const canvas = document.createElement('canvas');
    canvas.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
        opacity: 0.1;
    `;
    
    document.body.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    const matrix = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789@#$%^&*()*&^%+-/~{[|`]}";
    const matrixArray = matrix.split("");
    
    const fontSize = 10;
    const columns = canvas.width / fontSize;
    const drops = [];
    
    for (let x = 0; x < columns; x++) {
        drops[x] = 1;
    }
    
    function draw() {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.04)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = '#00ff41';
        ctx.font = fontSize + 'px monospace';
        
        for (let i = 0; i < drops.length; i++) {
            const text = matrixArray[Math.floor(Math.random() * matrixArray.length)];
            ctx.fillText(text, i * fontSize, drops[i] * fontSize);
            
            if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                drops[i] = 0;
            }
            drops[i]++;
        }
    }
    
    setInterval(draw, 35);
    
    // Resize handler
    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

// Uncomment to enable matrix rain effect
// initializeMatrixRain();

// Translation functionality
const translations = {
    'ru': {
        'VoiceConnect': 'VoiceConnect',
        'Pro': 'Pro',
        'Home': 'Главная',
        'Services': 'Услуги',
        'Features': 'Возможности',
        'Pricing': 'Цены',
        'Contact': 'Контакты',
        'Login': 'Войти',
        'Sign Up': 'Регистрация',
        'AI-Powered Call Center': 'ИИ-Колл-центр',
        'That Actually Works': 'Который Действительно Работает',
        'Transform your business with intelligent call automation, real-time analytics, and seamless customer engagement.': 'Трансформируйте свой бизнес с помощью интеллектуальной автоматизации звонков, аналитики в реальном времени и бесшовного взаимодействия с клиентами.',
        'Start Free Trial': 'Начать Бесплатный Пробный Период',
        'Learn More': 'Узнать Больше',
        'Our Services': 'Наши Услуги',
        'Automated Calling': 'Автоматические Звонки',
        'AI-powered outbound calling with natural conversation flow and intelligent lead qualification.': 'ИИ-звонки с естественным потоком разговора и интеллектуальной квалификацией лидов.',
        'Smart dialing algorithms': 'Умные алгоритмы набора',
        'Voice recognition': 'Распознавание голоса',
        'Call recording & analysis': 'Запись и анализ звонков',
        'SMS Campaigns': 'SMS Кампании',
        'Multi-channel SMS marketing with SIM800C integration for reliable message delivery.': 'Многоканальный SMS маркетинг с интеграцией SIM800C для надежной доставки сообщений.',
        'Bulk SMS sending': 'Массовая отправка SMS',
        'Delivery tracking': 'Отслеживание доставки',
        'Response automation': 'Автоматизация ответов',
        'Real-time Analytics': 'Аналитика в Реальном Времени',
        'Comprehensive dashboard with live metrics, performance tracking, and business insights.': 'Комплексная панель с живыми метриками, отслеживанием производительности и бизнес-аналитикой.',
        'Live call monitoring': 'Мониторинг звонков в реальном времени',
        'Conversion tracking': 'Отслеживание конверсий',
        'ROI analysis': 'Анализ ROI',
        'AI Automation': 'ИИ Автоматизация',
        'Intelligent business functions that handle customer follow-ups, lead scoring, and appointment scheduling.': 'Интеллектуальные бизнес-функции для работы с клиентами, оценки лидов и планирования встреч.',
        'Lead qualification': 'Квалификация лидов',
        'Appointment booking': 'Бронирование встреч',
        'Customer follow-up': 'Работа с клиентами',
        'Why Choose VoiceConnect Pro?': 'Почему Выбрать VoiceConnect Pro?',
        'Easy Setup': 'Простая Настройка',
        'Get started in minutes with our plug-and-play SIM800C modules and intuitive dashboard.': 'Начните работу за минуты с нашими модулями SIM800C и интуитивной панелью управления.',
        'Scalable Solution': 'Масштабируемое Решение',
        'From small businesses to enterprises, our system grows with your needs.': 'От малого бизнеса до предприятий, наша система растет вместе с вашими потребностями.',
        'Cost Effective': 'Экономически Эффективно',
        'Reduce operational costs by up to 70% with automated calling and smart routing.': 'Сократите операционные расходы до 70% с автоматическими звонками и умной маршрутизацией.',
        '24/7 Support': 'Поддержка 24/7',
        'Our expert team is always available to help you maximize your results.': 'Наша команда экспертов всегда готова помочь вам максимизировать результаты.',
        'Simple, Affordable Pricing': 'Простые, Доступные Цены',
        'VoiceConnect Pro': 'VoiceConnect Pro',
        'Best Value': 'Лучшая Цена',
        'Unlimited calls and SMS': 'Неограниченные звонки и SMS',
        'Multiple SIM800C modules': 'Несколько модулей SIM800C',
        'Advanced AI automation': 'Продвинутая ИИ автоматизация',
        'Real-time analytics': 'Аналитика в реальном времени',
        'Multi-language support': 'Поддержка многих языков',
        '24/7 email support': 'Поддержка по email 24/7',
        'Local GSM integration': 'Интеграция с локальным GSM',
        'Visual workflow builder': 'Визуальный конструктор процессов',
        'Get Started Now': 'Начать Сейчас',
        '5 SIM800C modules': '5 модулей SIM800C',
        'Advanced analytics': 'Продвинутая аналитика',
        'AI automation tools': 'Инструменты ИИ автоматизации',
        'Priority support': 'Приоритетная поддержка',
        'Unlimited calls': 'Неограниченные звонки',
        'Unlimited modules': 'Неограниченные модули',
        'Custom integrations': 'Пользовательские интеграции',
        'Dedicated account manager': 'Персональный менеджер',
        '24/7 phone support': 'Телефонная поддержка 24/7',
        'Get In Touch': 'Связаться с Нами',
        'Ready to transform your business?': 'Готовы трансформировать свой бизнес?',
        'Our team is here to help you get started with VoiceConnect Pro. Schedule a demo or ask any questions.': 'Наша команда готова помочь вам начать работу с VoiceConnect Pro. Запланируйте демо или задайте вопросы.',
        'Your Name': 'Ваше Имя',
        'Your Email': 'Ваш Email',
        'Company Name': 'Название Компании',
        'Tell us about your needs': 'Расскажите о ваших потребностях',
        'Send Message': 'Отправить Сообщение',
        'The future of AI-powered call centers.': 'Будущее ИИ-колл-центров.',
        'Product': 'Продукт',
        'Support': 'Поддержка',
        'Documentation': 'Документация',
        'Help Center': 'Центр Помощи',
        'Company': 'Компания',
        'About': 'О нас',
        'Careers': 'Карьера',
        'Privacy': 'Конфиденциальность',
        '© 2024 VoiceConnect Pro. All rights reserved.': '© 2024 VoiceConnect Pro. Все права защищены.',
        'Welcome Back': 'Добро Пожаловать',
        'Email': 'Email',
        'Password': 'Пароль',
        'Don\'t have an account?': 'Нет аккаунта?',
        'Sign up': 'Зарегистрироваться',
        'Get Started Today': 'Начните Сегодня',
        'Full Name': 'Полное Имя',
        'Phone Number': 'Номер Телефона',
        'Already have an account?': 'Уже есть аккаунт?',
        'contactSuccess': 'Сообщение отправлено успешно!',
        'contactError': 'Ошибка отправки сообщения. Попробуйте снова.',
        'planSelected': 'План выбран успешно! Мы свяжемся с вами в ближайшее время.',
        'planError': 'Ошибка выбора плана. Попробуйте снова.'
    },
    'uz': {
        'VoiceConnect': 'VoiceConnect',
        'Pro': 'Pro',
        'Home': 'Bosh sahifa',
        'Services': 'Xizmatlar',
        'Features': 'Imkoniyatlar',
        'Pricing': 'Narxlar',
        'Contact': 'Aloqa',
        'Login': 'Kirish',
        'Sign Up': 'Ro\'yxatdan o\'tish',
        'AI-Powered Call Center': 'AI-Quvvatli Qo\'ng\'iroq Markazi',
        'That Actually Works': 'Haqiqatan Ham Ishlaydigan',
        'Transform your business with intelligent call automation, real-time analytics, and seamless customer engagement.': 'Biznesingizni aqlli qo\'ng\'iroq avtomatizatsiyasi, real vaqt tahlili va uzluksiz mijozlar bilan ishlash orqali o\'zgartiring.',
        'Start Free Trial': 'Bepul Sinov Boshlash',
        'Learn More': 'Ko\'proq O\'rganish',
        'Our Services': 'Bizning Xizmatlarimiz',
        'Automated Calling': 'Avtomatik Qo\'ng\'iroqlar',
        'AI-powered outbound calling with natural conversation flow and intelligent lead qualification.': 'Tabiiy suhbat oqimi va aqlli lead baholash bilan AI-quvvatli chiquvchi qo\'ng\'iroqlar.',
        'Smart dialing algorithms': 'Aqlli terish algoritmlari',
        'Voice recognition': 'Ovoz tanish',
        'Call recording & analysis': 'Qo\'ng\'iroqlarni yozish va tahlil',
        'SMS Campaigns': 'SMS Kampaniyalar',
        'Multi-channel SMS marketing with SIM800C integration for reliable message delivery.': 'Ishonchli xabar yetkazish uchun SIM800C integratsiyasi bilan ko\'p kanalli SMS marketing.',
        'Bulk SMS sending': 'Ommaviy SMS yuborish',
        'Delivery tracking': 'Yetkazishni kuzatish',
        'Response automation': 'Javob avtomatizatsiyasi',
        'Real-time Analytics': 'Real Vaqt Tahlili',
        'Comprehensive dashboard with live metrics, performance tracking, and business insights.': 'Jonli ko\'rsatkichlar, ishlash kuzatuvi va biznes tahlili bilan to\'liq dashboard.',
        'Live call monitoring': 'Jonli qo\'ng\'iroqlarni kuzatish',
        'Conversion tracking': 'Konversiya kuzatuvi',
        'ROI analysis': 'ROI tahlili',
        'AI Automation': 'AI Avtomatizatsiya',
        'Intelligent business functions that handle customer follow-ups, lead scoring, and appointment scheduling.': 'Mijozlar bilan ishlash, lead baholash va uchrashuvlarni rejalashtirish uchun aqlli biznes funksiyalar.',
        'Lead qualification': 'Lead baholash',
        'Appointment booking': 'Uchrashuvlarni bron qilish',
        'Customer follow-up': 'Mijozlar bilan ishlash',
        'Why Choose VoiceConnect Pro?': 'Nega VoiceConnect Pro ni Tanlash Kerak?',
        'Easy Setup': 'Oson O\'rnatish',
        'Get started in minutes with our plug-and-play SIM800C modules and intuitive dashboard.': 'Bizning plug-and-play SIM800C modullari va intuitiv dashboard bilan daqiqalar ichida boshlang.',
        'Scalable Solution': 'Kengaytiriladigan Yechim',
        'From small businesses to enterprises, our system grows with your needs.': 'Kichik biznesdan korxonalargacha, bizning tizimimiz sizning ehtiyojlaringiz bilan o\'sadi.',
        'Cost Effective': 'Tejamkor',
        'Reduce operational costs by up to 70% with automated calling and smart routing.': 'Avtomatik qo\'ng\'iroqlar va aqlli marshrutlash bilan operatsion xarajatlarni 70% gacha kamaytiring.',
        '24/7 Support': '24/7 Qo\'llab-quvvatlash',
        'Our expert team is always available to help you maximize your results.': 'Bizning ekspert jamoamiz natijalaringizni maksimallashtirish uchun doimo tayyor.',
        'Simple, Affordable Pricing': 'Oddiy, Arzon Narxlar',
        'VoiceConnect Pro': 'VoiceConnect Pro',
        'Best Value': 'Eng Yaxshi Narx',
        'Unlimited calls and SMS': 'Cheksiz qo\'ng\'iroqlar va SMS',
        'Multiple SIM800C modules': 'Ko\'p SIM800C modullari',
        'Advanced AI automation': 'Ilg\'or AI avtomatizatsiya',
        'Real-time analytics': 'Real vaqt tahlili',
        'Multi-language support': 'Ko\'p til qo\'llab-quvvatlash',
        '24/7 email support': '24/7 email qo\'llab-quvvatlash',
        'Local GSM integration': 'Mahalliy GSM integratsiyasi',
        'Visual workflow builder': 'Vizual ish oqimi quruvchisi',
        'Get Started Now': 'Hozir Boshlash',
        '5 SIM800C modules': '5 ta SIM800C moduli',
        'Advanced analytics': 'Ilg\'or tahlil',
        'AI automation tools': 'AI avtomatizatsiya vositalari',
        'Priority support': 'Ustuvor qo\'llab-quvvatlash',
        'Unlimited calls': 'Cheksiz qo\'ng\'iroqlar',
        'Unlimited modules': 'Cheksiz modullar',
        'Custom integrations': 'Maxsus integratsiyalar',
        'Dedicated account manager': 'Maxsus hisob menejeri',
        '24/7 phone support': '24/7 telefon qo\'llab-quvvatlash',
        'Get In Touch': 'Bog\'lanish',
        'Ready to transform your business?': 'Biznesingizni o\'zgartirishga tayyormisiz?',
        'Our team is here to help you get started with VoiceConnect Pro. Schedule a demo or ask any questions.': 'Bizning jamoamiz VoiceConnect Pro bilan boshlashingizga yordam berish uchun shu yerda. Demo rejalashtiring yoki savollar bering.',
        'Your Name': 'Ismingiz',
        'Your Email': 'Emailingiz',
        'Company Name': 'Kompaniya Nomi',
        'Tell us about your needs': 'Ehtiyojlaringiz haqida ayting',
        'Send Message': 'Xabar Yuborish',
        'The future of AI-powered call centers.': 'AI-quvvatli qo\'ng\'iroq markazlarining kelajagi.',
        'Product': 'Mahsulot',
        'Support': 'Qo\'llab-quvvatlash',
        'Documentation': 'Hujjatlar',
        'Help Center': 'Yordam Markazi',
        'Company': 'Kompaniya',
        'About': 'Haqida',
        'Careers': 'Karyera',
        'Privacy': 'Maxfiylik',
        '© 2024 VoiceConnect Pro. All rights reserved.': '© 2024 VoiceConnect Pro. Barcha huquqlar himoyalangan.',
        'Welcome Back': 'Xush Kelibsiz',
        'Email': 'Email',
        'Password': 'Parol',
        'Don\'t have an account?': 'Hisobingiz yo\'qmi?',
        'Sign up': 'Ro\'yxatdan o\'ting',
        'Get Started Today': 'Bugun Boshlang',
        'Full Name': 'To\'liq Ism',
        'Phone Number': 'Telefon Raqami',
        'Already have an account?': 'Allaqachon hisobingiz bormi?',
        'contactSuccess': 'Xabar muvaffaqiyatli yuborildi!',
        'contactError': 'Xabar yuborishda xatolik. Qaytadan urinib ko\'ring.',
        'planSelected': 'Reja muvaffaqiyatli tanlandi! Tez orada siz bilan bog\'lanamiz.',
        'planError': 'Rejani tanlashda xatolik. Qaytadan urinib ko\'ring.'
    }
};

// Language selector functions
function toggleLanguageMenu() {
    const languageMenu = document.getElementById('languageMenu');
    const languageSelector = document.querySelector('.language-selector');
    
    languageMenu.classList.toggle('active');
    languageSelector.classList.toggle('active');
    
    // Close menu when clicking outside
    document.addEventListener('click', function closeMenu(e) {
        if (!languageSelector.contains(e.target)) {
            languageMenu.classList.remove('active');
            languageSelector.classList.remove('active');
            document.removeEventListener('click', closeMenu);
        }
    });
}

function translatePage(targetLanguage) {
    if (targetLanguage === currentLanguage) return;
    
    const languageMenu = document.getElementById('languageMenu');
    const languageSelector = document.querySelector('.language-selector');
    const currentLanguageSpan = document.getElementById('currentLanguage');
    
    // Close language menu
    languageMenu.classList.remove('active');
    languageSelector.classList.remove('active');
    
    // Store original texts if this is the first translation
    if (currentLanguage === 'en' && originalTexts.size === 0) {
        storeOriginalTexts();
    }
    
    // Update current language
    currentLanguage = targetLanguage;
    
    // Update language button text
    const languageFlags = {
        'en': '🌐 EN',
        'ru': '🇷🇺 RU',
        'uz': '🇺🇿 UZ',
        'es': '🇪🇸 ES',
        'fr': '🇫🇷 FR',
        'de': '🇩🇪 DE',
        'zh': '🇨🇳 ZH',
        'ar': '🇸🇦 AR',
        'hi': '🇮🇳 HI',
        'ja': '🇯🇵 JA'
    };
    
    currentLanguageSpan.textContent = languageFlags[targetLanguage] || '🌐 EN';
    
    // Apply translations
    if (targetLanguage === 'en') {
        restoreOriginalTexts();
    } else {
        applyTranslations(targetLanguage);
    }
    
    // Show notification
    const languageNames = {
        'en': 'English',
        'ru': 'Русский',
        'uz': 'O\'zbek',
        'es': 'Español',
        'fr': 'Français',
        'de': 'Deutsch',
        'zh': '中文',
        'ar': 'العربية',
        'hi': 'हिन्दी',
        'ja': '日本語'
    };
    
    showNotification(`Page translated to ${languageNames[targetLanguage]}`, 'success');
}

function storeOriginalTexts() {
    // Store all translatable text elements
    const translatableElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, a, button, span, li, label, input[placeholder], textarea[placeholder]');
    
    translatableElements.forEach((element, index) => {
        const key = `element_${index}`;
        
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            if (element.placeholder) {
                originalTexts.set(key + '_placeholder', element.placeholder);
            }
        } else {
            // Store text content, but preserve child elements
            const textContent = element.childNodes.length === 1 && element.childNodes[0].nodeType === Node.TEXT_NODE 
                ? element.textContent.trim() 
                : element.textContent.trim();
            
            if (textContent && !element.querySelector('input, button, a') && !element.closest('.language-menu')) {
                originalTexts.set(key, textContent);
            }
        }
        
        // Store element reference
        element.setAttribute('data-translate-key', key);
    });
}

function applyTranslations(targetLanguage) {
    const targetTranslations = translations[targetLanguage];
    if (!targetTranslations) return;
    
    // Translate elements
    document.querySelectorAll('[data-translate-key]').forEach(element => {
        const key = element.getAttribute('data-translate-key');
        
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            const placeholderKey = key + '_placeholder';
            const originalPlaceholder = originalTexts.get(placeholderKey);
            if (originalPlaceholder && targetTranslations[originalPlaceholder]) {
                element.placeholder = targetTranslations[originalPlaceholder];
            }
        } else {
            const originalText = originalTexts.get(key);
            if (originalText && targetTranslations[originalText]) {
                // Preserve HTML structure while replacing text
                if (element.childNodes.length === 1 && element.childNodes[0].nodeType === Node.TEXT_NODE) {
                    element.textContent = targetTranslations[originalText];
                } else {
                    // For elements with mixed content, replace text nodes only
                    element.childNodes.forEach(node => {
                        if (node.nodeType === Node.TEXT_NODE && node.textContent.trim() === originalText) {
                            node.textContent = targetTranslations[originalText];
                        }
                    });
                }
            }
        }
    });
}

function restoreOriginalTexts() {
    document.querySelectorAll('[data-translate-key]').forEach(element => {
        const key = element.getAttribute('data-translate-key');
        
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            const placeholderKey = key + '_placeholder';
            const originalPlaceholder = originalTexts.get(placeholderKey);
            if (originalPlaceholder) {
                element.placeholder = originalPlaceholder;
            }
        } else {
            const originalText = originalTexts.get(key);
            if (originalText) {
                if (element.childNodes.length === 1 && element.childNodes[0].nodeType === Node.TEXT_NODE) {
                    element.textContent = originalText;
                } else {
                    // Restore original text in text nodes
                    element.childNodes.forEach(node => {
                        if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
                            node.textContent = originalText;
                        }
                    });
                }
            }
        }
    });
}

// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// API Functions
async function submitContactForm(formData) {
    try {
        const response = await fetch(`${API_BASE_URL}/contact`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error submitting contact form:', error);
        throw error;
    }
}

async function selectPlan(planData) {
    try {
        const response = await fetch(`${API_BASE_URL}/select-plan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(planData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error selecting plan:', error);
        throw error;
    }
}

async function getSystemStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error getting system status:', error);
        return { status: 'offline', services: {} };
    }
}

async function getAnalytics() {
    try {
        const response = await fetch(`${API_BASE_URL}/analytics`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error getting analytics:', error);
        return { data: {} };
    }
}

// Enhanced form submission
document.addEventListener('DOMContentLoaded', function() {
    // Contact form submission
    const contactForm = document.querySelector('#contact form');
    if (contactForm) {
        contactForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = {
                name: formData.get('name'),
                email: formData.get('email'),
                company: formData.get('company') || '',
                message: formData.get('message')
            };
            
            try {
                const result = await submitContactForm(data);
                alert(translations[currentLanguage].contactSuccess || 'Message sent successfully!');
                this.reset();
            } catch (error) {
                alert(translations[currentLanguage].contactError || 'Error sending message. Please try again.');
            }
        });
    }
    
    // Plan selection buttons
    const planButtons = document.querySelectorAll('.plan-button, .cta-button');
    planButtons.forEach(button => {
        button.addEventListener('click', async function(e) {
            if (this.textContent.includes('$') || this.textContent.includes('Choose') || this.textContent.includes('Get Started')) {
                e.preventDefault();
                
                const planData = {
                    plan: 'VoiceConnect Pro',
                    email: ''
                };
                
                try {
                    const result = await selectPlan(planData);
                    alert(translations[currentLanguage].planSelected || 'Plan selected successfully! We will contact you soon.');
                } catch (error) {
                    alert(translations[currentLanguage].planError || 'Error selecting plan. Please try again.');
                }
            }
        });
    });
    
    // Load system status
    loadSystemStatus();
    
    // Update status every 30 seconds
    setInterval(loadSystemStatus, 30000);
});

async function loadSystemStatus() {
    try {
        const status = await getSystemStatus();
        updateStatusIndicators(status);
    } catch (error) {
        console.error('Failed to load system status:', error);
    }
}

function updateStatusIndicators(status) {
    // Update any status indicators on the page
    const statusElements = document.querySelectorAll('.status-indicator');
    statusElements.forEach(element => {
        if (status.status === 'healthy') {
            element.classList.add('online');
            element.classList.remove('offline');
            element.textContent = 'System Online';
        } else {
            element.classList.add('offline');
            element.classList.remove('online');
            element.textContent = 'System Offline';
        }
    });
}

// Performance Optimizations for PC
function initializePerformanceOptimizations() {
    // Lazy loading for images
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        observer.unobserve(img);
                    }
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    // Preload critical resources
    preloadCriticalResources();
    
    // Optimize scroll performance
    optimizeScrollPerformance();
    
    // Initialize keyboard navigation
    initializeKeyboardNavigation();
}

function preloadCriticalResources() {
    // Preload fonts
    const fontLink = document.createElement('link');
    fontLink.rel = 'preload';
    fontLink.href = 'https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap';
    fontLink.as = 'style';
    document.head.appendChild(fontLink);
}

function optimizeScrollPerformance() {
    let ticking = false;
    
    function updateScrollEffects() {
        // Throttled scroll effects
        const scrollY = window.pageYOffset;
        
        // Update navigation background
        const nav = document.querySelector('.navbar');
        if (nav) {
            if (scrollY > 50) {
                nav.classList.add('scrolled');
            } else {
                nav.classList.remove('scrolled');
            }
        }
        
        ticking = false;
    }
    
    function requestTick() {
        if (!ticking) {
            requestAnimationFrame(updateScrollEffects);
            ticking = true;
        }
    }
    
    window.addEventListener('scroll', requestTick, { passive: true });
}

function initializeKeyboardNavigation() {
    // Enhanced keyboard navigation for accessibility
    document.addEventListener('keydown', function(e) {
        // ESC key to close modals/dropdowns
        if (e.key === 'Escape') {
            closeAllDropdowns();
        }
        
        // Tab navigation improvements
        if (e.key === 'Tab') {
            document.body.classList.add('keyboard-navigation');
        }
    });
    
    // Remove keyboard navigation class on mouse use
    document.addEventListener('mousedown', function() {
        document.body.classList.remove('keyboard-navigation');
    });
}

function closeAllDropdowns() {
    const dropdowns = document.querySelectorAll('.language-dropdown');
    dropdowns.forEach(dropdown => {
        dropdown.classList.remove('active');
    });
}

// Basic functionality fallback
function initializeBasicFunctionality() {
    console.log('Running in basic mode - animations disabled');
    
    // Basic smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
    
    // Basic form handling
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', handleContactSubmit);
    }
}

// Error boundary for critical functions
function safeExecute(fn, fallback = null) {
    try {
        return fn();
    } catch (error) {
        console.error('Safe execution failed:', error);
        if (fallback) {
            return fallback();
        }
    }
}

// Performance monitoring
function monitorPerformance() {
    if ('performance' in window) {
        window.addEventListener('load', () => {
            setTimeout(() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                console.log('Page load time:', perfData.loadEventEnd - perfData.loadEventStart, 'ms');
            }, 0);
        });
    }
}

// Initialize performance monitoring
monitorPerformance();