// VoiceConnect Pro - Frontend JavaScript
// Retro minimalistic animations and interactions

// Global state
let isLoggedIn = false;
let currentUser = null;

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeAnimations();
    initializeScrollEffects();
    initializeTypingEffect();
    initializeTerminalAnimation();
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