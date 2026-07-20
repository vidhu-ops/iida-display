// IDA Application JavaScript

// Global variables
let isGenerating = false;

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize application
function initializeApp() {
    setupFormValidation();
    setupDropdownHandlers();
    setupUIEnhancements();
    checkSystemStatus();
}

// Form validation setup
function setupFormValidation() {
    const form = document.getElementById('research-form');
    if (form) {
        form.addEventListener('submit', handleFormSubmission);
        
        // Real-time validation
        const questionField = document.getElementById('question');
        if (questionField) {
            questionField.addEventListener('input', validateQuestion);
        }
    }
}

// Handle form submission
function handleFormSubmission(event) {
    if (isGenerating) {
        event.preventDefault();
        return;
    }

    const question = document.getElementById('question').value.trim();
    
    if (!question) {
        event.preventDefault();
        showAlert('Please enter a research question.', 'warning');
        return;
    }

    if (question.length < 10) {
        event.preventDefault();
        showAlert('Please provide a more detailed research question (at least 10 characters).', 'warning');
        return;
    }

    // Show loading state
    setGeneratingState(true);
}

// Validate question input
function validateQuestion() {
    const questionField = document.getElementById('question');
    const question = questionField.value.trim();
    
    // Remove existing validation classes
    questionField.classList.remove('is-valid', 'is-invalid');
    
    if (question.length > 0) {
        if (question.length >= 10) {
            questionField.classList.add('is-valid');
        } else if (question.length > 0) {
            questionField.classList.add('is-invalid');
        }
    }
}

// Setup dropdown handlers
function setupDropdownHandlers() {
    const categorySelect = document.getElementById('category');
    const subcategorySelect = document.getElementById('subcategory');
    
    if (categorySelect && subcategorySelect) {
        categorySelect.addEventListener('change', function() {
            loadSubcategories(this.value, subcategorySelect);
        });
    }
}

// Load subcategories based on selected category
function loadSubcategories(category, subcategorySelect) {
    // Get the subcategory select element if not provided
    if (!subcategorySelect) {
        subcategorySelect = document.getElementById('subcategory');
    }
    
    // Safety check
    if (!subcategorySelect) {
        console.error('Subcategory select element not found');
        return;
    }
    
    // Clear existing options
    subcategorySelect.innerHTML = '<option value="">Select focus area (optional)</option>';
    
    if (!category) {
        subcategorySelect.disabled = true;
        return;
    }
    
    // Enable subcategory dropdown
    subcategorySelect.disabled = false;
    
    // Check if we have dropdown options available
    if (typeof dropdownOptions !== 'undefined' && dropdownOptions[category]) {
        const subcategories = dropdownOptions[category];
        
        subcategories.forEach(subcategory => {
            const option = document.createElement('option');
            option.value = subcategory;
            option.textContent = subcategory;
            subcategorySelect.appendChild(option);
        });
    } else {
        // Fallback: fetch from API
        fetch(`/api/subcategories/${encodeURIComponent(category)}`)
            .then(response => response.json())
            .then(subcategories => {
                subcategories.forEach(subcategory => {
                    const option = document.createElement('option');
                    option.value = subcategory;
                    option.textContent = subcategory;
                    subcategorySelect.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Error loading subcategories:', error);
                subcategorySelect.disabled = true;
            });
    }
}

// Setup UI enhancements
function setupUIEnhancements() {
    // Add smooth scrolling
    addSmoothScrolling();
    
    // Add tooltip initialization if needed
    initializeTooltips();
    
    // Add form field focus effects
    addFocusEffects();
    
    // Add keyboard shortcuts
    addKeyboardShortcuts();
}

// Add smooth scrolling behavior
function addSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            // Only prevent default and scroll if href is not just "#"
            if (href && href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    if (typeof bootstrap !== 'undefined') {
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// Add focus effects to form fields
function addFocusEffects() {
    const formControls = document.querySelectorAll('.form-control, .form-select');
    
    formControls.forEach(control => {
        control.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        control.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });
}

// Add keyboard shortcuts
function addKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to submit form
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const form = document.getElementById('research-form');
            if (form && !isGenerating) {
                form.submit();
            }
        }
        
        // Escape to clear form
        if (e.key === 'Escape') {
            const form = document.getElementById('research-form');
            if (form && !isGenerating) {
                if (confirm('Clear the form?')) {
                    form.reset();
                    document.getElementById('subcategory').disabled = true;
                }
            }
        }
    });
}

// Set generating state
function setGeneratingState(generating) {
    isGenerating = generating;
    const btn = document.getElementById('generate-btn');
    const form = document.getElementById('research-form');
    
    if (btn) {
        if (generating) {
            btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Generating Report...';
            btn.disabled = true;
            btn.classList.add('generating');
        } else {
            btn.innerHTML = '<i class="fas fa-cogs me-2"></i>Generate Comprehensive Report';
            btn.disabled = false;
            btn.classList.remove('generating');
        }
    }
    
    if (form) {
        if (generating) {
            form.classList.add('loading');
        } else {
            form.classList.remove('loading');
        }
    }
}

// Show alert message
function showAlert(message, type = 'info') {
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.setAttribute('role', 'alert');
    
    const icon = getAlertIcon(type);
    alert.innerHTML = `
        <i class="${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Find container and insert alert
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alert, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
}

// Get alert icon based on type
function getAlertIcon(type) {
    const icons = {
        'success': 'fas fa-check-circle',
        'warning': 'fas fa-exclamation-triangle',
        'danger': 'fas fa-exclamation-circle',
        'info': 'fas fa-info-circle'
    };
    return icons[type] || icons.info;
}

// Check system status
function checkSystemStatus() {
    // Check if we're on the main page
    if (document.getElementById('research-form')) {
        // You could add periodic status checks here
        // For now, we'll just log that the system is initialized
        console.log('IDA System initialized successfully');
    }
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let lastFunc;
    let lastRan;
    return function() {
        const context = this;
        const args = arguments;
        if (!lastRan) {
            func.apply(context, args);
            lastRan = Date.now();
        } else {
            clearTimeout(lastFunc);
            lastFunc = setTimeout(function() {
                if ((Date.now() - lastRan) >= limit) {
                    func.apply(context, args);
                    lastRan = Date.now();
                }
            }, limit - (Date.now() - lastRan));
        }
    };
}

// Export functions for global access
window.IDA = {
    loadSubcategories,
    setGeneratingState,
    showAlert,
    debounce,
    throttle,
    triggerInstall: () => {
        if (window.deferredPrompt) {
            window.deferredPrompt.prompt();
        } else {
            const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
            if (isIOS) {
                alert('To install IIDA on iPhone/iPad:\n\n1. Tap the Share icon\n2. Select "Add to Home Screen"');
            } else {
                alert('To install IIDA:\n\n1. Tap the browser menu\n2. Select "Install app"');
            }
        }
    }
};
