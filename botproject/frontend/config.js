// FILE: config.js
// Modern Eazr Financial Assistant - Configuration File
// Updated with enhanced features and modern theming

const config = {
    // API Configuration - Updated to match your backend (NO /api prefix)
    API_BASE_URL: 'http://13.126.81.152:8000',
    // For production, uncomment this:
    // API_BASE_URL: 'http://13.126.81.152:8000',
    
    // Application Settings
    APP_NAME: 'eazr',
    APP_TAGLINE: 'Your intelligent financial companion',
    
    // Theme Configuration
    THEME: {
        PRIMARY_COLOR: '#48bb78',
        SECONDARY_COLOR: '#38a169',
        ACCENT_COLOR: '#2f855a',
        SUCCESS_COLOR: '#48bb78',
        ERROR_COLOR: '#f56565',
        WARNING_COLOR: '#ed8936',
        INFO_COLOR: '#4299e1',
        BACKGROUND_GRADIENT: 'linear-gradient(135deg, #48bb78 0%, #38a169 50%, #2f855a 100%)',
        TEXT_PRIMARY: '#1a202c',
        TEXT_SECONDARY: '#718096',
        WHITE: '#ffffff',
        WHITE_ALPHA: 'rgba(255, 255, 255, 0.95)'
    },
    
    // Default Language
    DEFAULT_LANGUAGE: 'en',
    
    // Session Settings (matching backend expectations)
    SESSION_TIMEOUT: 30 * 60 * 1000, // 30 minutes in milliseconds
    
    // OTP Settings (matching backend validation)
    OTP_LENGTH: 4, // Updated to 4 digits for modern UI
    OTP_RESEND_TIMEOUT: 30, // seconds
    
    // UI Settings
    MESSAGE_AUTO_HIDE_DURATION: 5000, // milliseconds
    TYPING_INDICATOR_DELAY: 300, // milliseconds
    ANIMATION_DURATION: 300, // milliseconds
    
    // Feature Flags
    ENABLE_VOICE_INPUT: true,
    ENABLE_CHAT_HISTORY: true,
    ENABLE_FLOATING_ANIMATIONS: true,
    ENABLE_BACKDROP_BLUR: true,
    MAX_CHAT_HISTORY_ITEMS: 50,
    
    // Supported Languages (matching backend)
    SUPPORTED_LANGUAGES: {
        'en': { name: 'English', locale: 'en-IN', flag: '🇺🇸' },
        'hi': { name: 'हिन्दी (Hindi)', locale: 'hi-IN', flag: '🇮🇳' },
        'ta': { name: 'தமிழ் (Tamil)', locale: 'ta-IN', flag: '🇮🇳' },
        'te': { name: 'తెలుగు (Telugu)', locale: 'te-IN', flag: '🇮🇳' },
        'bn': { name: 'বাংলা (Bengali)', locale: 'bn-IN', flag: '🇮🇳' },
        'mr': { name: 'मराठी (Marathi)', locale: 'mr-IN', flag: '🇮🇳' },
        'gu': { name: 'ગુજરાતી (Gujarati)', locale: 'gu-IN', flag: '🇮🇳' },
        'kn': { name: 'ಕನ್ನಡ (Kannada)', locale: 'kn-IN', flag: '🇮🇳' },
        'ml': { name: 'മലയാളം (Malayalam)', locale: 'ml-IN', flag: '🇮🇳' },
        'pa': { name: 'ਪੰਜਾਬੀ (Punjabi)', locale: 'pa-IN', flag: '🇮🇳' }
    },
    
    // Quick Actions (matching backend intents) - Enhanced with emojis
    QUICK_ACTIONS: [
        {
            icon: '💰',
            title: 'Personal Loan',
            description: 'Get instant approval with competitive rates',
            action: 'I want to apply for personal loan',
            color: '#48bb78'
        },
        {
            icon: '🛡️',
            title: 'Insurance Plans',
            description: 'Comprehensive coverage for your future',
            action: 'I need insurance plan',
            color: '#4299e1'
        },
        {
            icon: '🎯',
            title: 'Digital Wallet',
            description: 'Seamless payments and KYC setup',
            action: 'Create wallet account',
            color: '#ed8936'
        },
        {
            icon: '📊',
            title: 'Account Balance',
            description: 'View your current balance and transactions',
            action: 'Check my account balance',
            color: '#9f7aea'
        },
        {
            icon: '🏦',
            title: 'Banking Services',
            description: 'Open accounts and manage banking',
            action: 'I need banking services',
            color: '#38b2ac'
        },
        {
            icon: '📈',
            title: 'Investment Plans',
            description: 'Grow your wealth with smart investments',
            action: 'Show me investment options',
            color: '#f6ad55'
        }
    ],
    
    // API Endpoints (matching your backend routes)
    ENDPOINTS: {
        SEND_OTP: '/send-otp',
        VERIFY_OTP: '/verify-otp',
        CHECK_SESSION: '/check-session',
        LOGOUT: '/logout',
        ASK: '/ask',
        CHATBOT_CONTINUE: '/chatbot-continue',
        HEALTH: '/health',
        SET_LANGUAGE: '/set-language',
        USER_PREFERENCES: '/user-preferences',
        CHAT_HISTORY: '/chat-history'
    },
    
    // Enhanced Error Messages with emojis
    ERROR_MESSAGES: {
        NETWORK_ERROR: '🌐 Network error. Please check your connection.',
        SERVER_ERROR: '⚠️ Server error. Please try again later.',
        INVALID_PHONE: '📱 Please enter a valid 10-digit mobile number',
        INVALID_OTP: '🔐 Invalid OTP. Please try again.',
        SESSION_EXPIRED: '⏰ Your session has expired. Please login again.',
        BACKEND_OFFLINE: '🚫 Cannot connect to server. Please ensure the backend is running.',
        RATE_LIMITED: '⏱️ Too many requests. Please wait a moment.',
        UNAUTHORIZED: '🔒 Unauthorized access. Please login again.'
    },
    
    // Enhanced Success Messages with emojis
    SUCCESS_MESSAGES: {
        OTP_SENT: '📨 OTP sent successfully!',
        OTP_RESENT: '🔄 OTP resent successfully!',
        LOGIN_SUCCESS: '🎉 Login successful! Redirecting...',
        LOGOUT_SUCCESS: '👋 Logged out successfully!',
        MESSAGE_SENT: '✅ Message sent successfully!',
        PREFERENCES_SAVED: '💾 Preferences saved successfully!'
    },
    
    // Intent Detection Keywords (for frontend fallback)
    INTENT_KEYWORDS: {
        wallet_setup: ['wallet', 'create wallet', 'setup wallet', 'open account', 'kyc', 'digital wallet'],
        personal_loan: ['loan', 'personal loan', 'apply loan', 'need money', 'borrow', 'credit'],
        insurance_plan: ['insurance', 'coverage', 'policy', 'protection', 'health insurance'],
        task: ['balance', 'transaction', 'credited', 'debited', 'account', 'statement', 'history'],
        greeting: ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'namaste'],
        help: ['help', 'what can you do', 'options', 'services', 'menu', 'assist'],
        investment: ['invest', 'investment', 'mutual fund', 'sip', 'portfolio', 'returns'],
        banking: ['bank', 'banking', 'savings', 'current account', 'fd', 'deposit']
    },
    
    // Local Storage Keys
    STORAGE_KEYS: {
        IS_LOGGED_IN: 'isLoggedIn',
        SESSION_ID: 'sessionId',
        ACCESS_TOKEN: 'accessToken',
        USER_ID: 'userId',
        USER_PHONE: 'userPhone',
        PREFERRED_LANGUAGE: 'preferredLanguage',
        LAST_ACTIVITY: 'lastActivity',
        DRAFT_MESSAGE: 'draftMessage',
        CHAT_HISTORY: 'chatHistory',
        USER_PREFERENCES: 'userPreferences',
        THEME_PREFERENCE: 'themePreference'
    },
    
    // Validation Patterns
    VALIDATION: {
        PHONE_PATTERN: /^[6-9]\d{9}$/, // Indian mobile number pattern
        OTP_PATTERN: /^\d{4}$/, // 4-digit OTP for modern UI
        EMAIL_PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        NAME_PATTERN: /^[a-zA-Z\s]{2,50}$/,
        PAN_PATTERN: /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/,
        AADHAR_PATTERN: /^\d{12}$/
    },
    
    // UI Constants
    UI: {
        MAX_MESSAGE_LENGTH: 2000,
        TYPING_SPEED: 50, // milliseconds per character for typing effect
        SCROLL_BEHAVIOR: 'smooth',
        ANIMATION_DURATION: 300, // milliseconds
        DEBOUNCE_DELAY: 500, // milliseconds for input debouncing
        MOBILE_BREAKPOINT: 768, // pixels
        TABLET_BREAKPOINT: 1024 // pixels
    },
    
    // Development Mode
    DEBUG: false, // Set to true for console logging
    
    // Performance Settings
    CACHE_DURATION: 5 * 60 * 1000, // 5 minutes for client-side caching
    MAX_RETRY_ATTEMPTS: 3,
    RETRY_DELAY: 1000, // milliseconds
    REQUEST_TIMEOUT: 30000, // 30 seconds
    
    // Accessibility
    A11Y: {
        FOCUS_VISIBLE: true,
        HIGH_CONTRAST: false,
        REDUCED_MOTION: false,
        SCREEN_READER_SUPPORT: true
    },
    
    // Chatbot Configuration
    CHATBOT: {
        MAX_CONTEXT_LENGTH: 10, // Number of previous messages to consider
        TYPING_DELAY_MIN: 500, // Minimum typing delay
        TYPING_DELAY_MAX: 2000, // Maximum typing delay
        SUGGESTION_LIMIT: 5, // Maximum number of suggestions to show
        AUTO_SCROLL: true,
        SAVE_CHAT_HISTORY: true
    }
};

// Utility functions
config.utils = {
    // Get full API URL
    getApiUrl: (endpoint) => {
        return `${config.API_BASE_URL}${endpoint}`;
    },
    
    // Format phone number for display
    formatPhone: (phone) => {
        if (!phone) return '';
        if (phone.length > 4) {
            return phone.substring(0, 3) + ' ' + 'X'.repeat(phone.length - 5) + phone.slice(-2);
        }
        return phone;
    },
    
    // Validate phone number
    isValidPhone: (phone) => {
        return config.VALIDATION.PHONE_PATTERN.test(phone);
    },
    
    // Validate OTP
    isValidOTP: (otp) => {
        return config.VALIDATION.OTP_PATTERN.test(otp);
    },
    
    // Get language name
    getLanguageName: (code) => {
        return config.SUPPORTED_LANGUAGES[code]?.name || 'Unknown';
    },
    
    // Format currency
    formatCurrency: (amount, currency = 'INR') => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: currency
        }).format(amount);
    },
    
    // Format date
    formatDate: (date, options = {}) => {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        };
        return new Intl.DateTimeFormat('en-IN', { ...defaultOptions, ...options }).format(new Date(date));
    },
    
    // Debug log
    log: (message, data) => {
        if (config.DEBUG) {
            console.log(`[Eazr] ${message}`, data || '');
        }
    },
    
    // Error log
    error: (message, error) => {
        console.error(`[Eazr Error] ${message}`, error || '');
    },
    
    // Generate unique ID
    generateId: () => {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },
    
    // Debounce function
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Throttle function
    throttle: (func, limit) => {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    },
    
    // Storage helpers
    storage: {
        get: (key) => {
            try {
                const value = localStorage.getItem(key);
                return value ? JSON.parse(value) : null;
            } catch (e) {
                config.utils.error('Storage get error', e);
                return localStorage.getItem(key);
            }
        },
        
        set: (key, value) => {
            try {
                localStorage.setItem(key, typeof value === 'string' ? value : JSON.stringify(value));
                return true;
            } catch (e) {
                config.utils.error('Storage set error', e);
                return false;
            }
        },
        
        remove: (key) => {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (e) {
                config.utils.error('Storage remove error', e);
                return false;
            }
        },
        
        clear: () => {
            try {
                localStorage.clear();
                return true;
            } catch (e) {
                config.utils.error('Storage clear error', e);
                return false;
            }
        }
    },
    
    // Session helpers
    session: {
        isValid: () => {
            const isLoggedIn = config.utils.storage.get(config.STORAGE_KEYS.IS_LOGGED_IN);
            const accessToken = config.utils.storage.get(config.STORAGE_KEYS.ACCESS_TOKEN);
            const userId = config.utils.storage.get(config.STORAGE_KEYS.USER_ID);
            
            return isLoggedIn === 'true' && accessToken && userId;
        },
        
        updateActivity: () => {
            config.utils.storage.set(config.STORAGE_KEYS.LAST_ACTIVITY, Date.now().toString());
        },
        
        isExpired: () => {
            const lastActivity = config.utils.storage.get(config.STORAGE_KEYS.LAST_ACTIVITY);
            if (!lastActivity) return true;
            
            const timeSinceActivity = Date.now() - parseInt(lastActivity);
            return timeSinceActivity > config.SESSION_TIMEOUT;
        },
        
        clear: () => {
            config.utils.storage.clear();
        },
        
        getUserData: () => {
            return {
                userId: config.utils.storage.get(config.STORAGE_KEYS.USER_ID),
                userPhone: config.utils.storage.get(config.STORAGE_KEYS.USER_PHONE),
                sessionId: config.utils.storage.get(config.STORAGE_KEYS.SESSION_ID),
                accessToken: config.utils.storage.get(config.STORAGE_KEYS.ACCESS_TOKEN)
            };
        }
    },
    
    // API helpers
    api: {
        // Make API request with proper headers and error handling
        request: async (endpoint, options = {}) => {
            const url = config.utils.getApiUrl(endpoint);
            const accessToken = config.utils.storage.get(config.STORAGE_KEYS.ACCESS_TOKEN);
            
            const defaultHeaders = {
                'Content-Type': 'application/json'
            };
            
            if (accessToken) {
                defaultHeaders['Authorization'] = `Bearer ${accessToken}`;
            }
            
            const requestOptions = {
                ...options,
                headers: {
                    ...defaultHeaders,
                    ...(options.headers || {})
                }
            };
            
            config.utils.log(`API Request: ${endpoint}`, requestOptions);
            
            try {
                const response = await fetch(url, requestOptions);
                
                // Handle session expiry
                if (response.status === 401) {
                    config.utils.session.clear();
                    window.location.href = 'login.html';
                    return null;
                }
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.detail || data.message || `HTTP ${response.status}`);
                }
                
                config.utils.log(`API Response: ${endpoint}`, data);
                
                return { response, data };
            } catch (error) {
                config.utils.error(`API Error: ${endpoint}`, error);
                throw error;
            }
        },
        
        // Retry failed requests
        requestWithRetry: async (endpoint, options = {}, maxRetries = config.MAX_RETRY_ATTEMPTS) => {
            let lastError;
            
            for (let i = 0; i <= maxRetries; i++) {
                try {
                    return await config.utils.api.request(endpoint, options);
                } catch (error) {
                    lastError = error;
                    if (i < maxRetries) {
                        await new Promise(resolve => setTimeout(resolve, config.RETRY_DELAY * (i + 1)));
                    }
                }
            }
            
            throw lastError;
        }
    },
    
    // UI helpers
    ui: {
        // Show notification
        showNotification: (message, type = 'info', duration = config.MESSAGE_AUTO_HIDE_DURATION) => {
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.textContent = message;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 1rem 1.5rem;
                background: ${type === 'error' ? '#f56565' : type === 'success' ? '#48bb78' : '#4299e1'};
                color: white;
                border-radius: 8px;
                z-index: 1000;
                animation: slideIn 0.3s ease;
            `;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }, duration);
        },
        
        // Format message with markdown-like syntax
        formatMessage: (content) => {
            return content
                .replace(/\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
        },
        
        // Check if device is mobile
        isMobile: () => {
            return window.innerWidth <= config.UI.MOBILE_BREAKPOINT;
        },
        
        // Check if device is tablet
        isTablet: () => {
            return window.innerWidth > config.UI.MOBILE_BREAKPOINT && window.innerWidth <= config.UI.TABLET_BREAKPOINT;
        },
        
        // Scroll to element
        scrollToElement: (element, behavior = config.UI.SCROLL_BEHAVIOR) => {
            if (element) {
                element.scrollIntoView({ behavior, block: 'center' });
            }
        }
    }
};

// Make config available globally
window.appConfig = config;

// Initialize configuration on page load
document.addEventListener('DOMContentLoaded', () => {
    config.utils.log('Config initialized', {
        apiUrl: config.API_BASE_URL,
        debug: config.DEBUG,
        version: '2.0.0',
        theme: config.THEME.PRIMARY_COLOR
    });
    
    // Set CSS custom properties for theme colors
    const root = document.documentElement;
    Object.entries(config.THEME).forEach(([key, value]) => {
        root.style.setProperty(`--${key.toLowerCase().replace(/_/g, '-')}`, value);
    });
});

// Export for modules if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = config;
}