/**
 * IDA Research Platform - JavaScript Shortcode
 * Easy integration for any website
 * Usage: Just include this script and call createIDAShortcode()
 */

(function() {
    'use strict';
    
    // Default configuration
    const IDA_CONFIG = {
        baseUrl: window.location.origin, // Change this to your IDA domain
        containerId: 'iida-research-platform',
        width: '100%',
        height: '800px',
        title: '🔬 IDA - Intelligent Data Analytics',
        subtitle: 'AI-Powered Research & Analysis Platform'
    };
    
    // CSS styles for the shortcode
    const IDA_STYLES = `
        .ida-shortcode-container {
            width: 100%;
            max-width: 1200px;
            margin: 20px auto;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            background: white;
        }
        .ida-shortcode-header {
            background: linear-gradient(135deg, #0d6efd 0%, #6610f2 100%);
            color: white;
            padding: 15px 20px;
            text-align: center;
        }
        .ida-shortcode-header h3 {
            margin: 0;
            font-size: 1.5rem;
            font-weight: 600;
        }
        .ida-shortcode-header p {
            margin: 5px 0 0 0;
            opacity: 0.9;
            font-size: 0.9rem;
        }
        .ida-shortcode-frame {
            width: 100%;
            border: none;
            background: #f8f9fa;
        }
        .ida-shortcode-footer {
            background: #f8f9fa;
            padding: 10px 20px;
            text-align: center;
            font-size: 0.8rem;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
        }
        .ida-shortcode-footer a {
            color: #0d6efd;
            text-decoration: none;
            margin: 0 10px;
            cursor: pointer;
        }
        .ida-shortcode-footer a:hover {
            text-decoration: underline;
        }
        .ida-shortcode-loading {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 200px;
            background: #f8f9fa;
            color: #6c757d;
            font-size: 1rem;
        }
        .ida-shortcode-loading::after {
            content: '';
            width: 20px;
            height: 20px;
            margin-left: 10px;
            border: 2px solid #6c757d;
            border-top: 2px solid #0d6efd;
            border-radius: 50%;
            animation: ida-spin 1s linear infinite;
        }
        @keyframes ida-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @media (max-width: 768px) {
            .ida-shortcode-container {
                margin: 10px;
                max-width: calc(100% - 20px);
            }
            .ida-shortcode-header h3 {
                font-size: 1.3rem;
            }
        }
        .ida-fullscreen {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            z-index: 9999 !important;
            margin: 0 !important;
            max-width: none !important;
        }
        .ida-fullscreen .ida-shortcode-frame {
            height: calc(100vh - 120px) !important;
        }
    `;
    
    // Inject CSS styles
    function injectStyles() {
        if (!document.getElementById('ida-shortcode-styles')) {
            const style = document.createElement('style');
            style.id = 'ida-shortcode-styles';
            style.textContent = IDA_STYLES;
            document.head.appendChild(style);
        }
    }
    
    // Create the HTML structure
    function createHTML(config) {
        return `
            <div class="ida-shortcode-container" id="${config.containerId}-container">
                <div class="ida-shortcode-header">
                    <h3>${config.title}</h3>
                    <p>${config.subtitle}</p>
                </div>
                
                <div class="ida-shortcode-loading" id="${config.containerId}-loading">
                    Loading IDA Platform...
                </div>
                
                <iframe 
                    id="${config.containerId}-frame"
                    class="ida-shortcode-frame" 
                    src="${config.baseUrl}"
                    title="IIDA Research Platform"
                    style="display: none; height: ${config.height};"
                    onload="window.IDAShortcode.showFrame('${config.containerId}')"
                ></iframe>
                
                <div class="ida-shortcode-footer">
                    Powered by <a href="${config.baseUrl}" target="_blank">IDA Research Platform</a> |
                    <a onclick="window.IDAShortcode.toggleFullscreen('${config.containerId}')">⛶ Fullscreen</a> |
                    <a onclick="window.IDAShortcode.refreshFrame('${config.containerId}')">🔄 Refresh</a>
                </div>
            </div>
        `;
    }
    
    // Shortcode functionality
    window.IDAShortcode = {
        // Show frame when loaded
        showFrame: function(containerId) {
            const loading = document.getElementById(containerId + '-loading');
            const frame = document.getElementById(containerId + '-frame');
            
            if (loading) loading.style.display = 'none';
            if (frame) frame.style.display = 'block';
        },
        
        // Toggle fullscreen mode
        toggleFullscreen: function(containerId) {
            const container = document.getElementById(containerId + '-container');
            const frame = document.getElementById(containerId + '-frame');
            
            if (!container || !frame) return;
            
            if (container.classList.contains('ida-fullscreen')) {
                container.classList.remove('ida-fullscreen');
                frame.style.height = IDA_CONFIG.height;
            } else {
                container.classList.add('ida-fullscreen');
                frame.style.height = 'calc(100vh - 120px)';
            }
        },
        
        // Refresh the iframe
        refreshFrame: function(containerId) {
            const frame = document.getElementById(containerId + '-frame');
            const loading = document.getElementById(containerId + '-loading');
            
            if (!frame || !loading) return;
            
            loading.style.display = 'flex';
            frame.style.display = 'none';
            
            // Reload the iframe
            frame.src = frame.src;
        },
        
        // Create a new shortcode instance
        create: function(options = {}) {
            const config = Object.assign({}, IDA_CONFIG, options);
            
            // Inject styles
            injectStyles();
            
            // Create container or use existing
            let container = document.getElementById(config.containerId);
            if (!container) {
                container = document.createElement('div');
                container.id = config.containerId;
                document.body.appendChild(container);
            }
            
            // Set HTML content
            container.innerHTML = createHTML(config);
            
            return config.containerId;
        }
    };
    
    // Auto-create shortcode if container exists
    document.addEventListener('DOMContentLoaded', function() {
        const defaultContainer = document.getElementById(IDA_CONFIG.containerId);
        if (defaultContainer) {
            window.IDAShortcode.create();
        }
    });
    
    // Handle escape key for fullscreen exit
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const fullscreenContainers = document.querySelectorAll('.ida-fullscreen');
            fullscreenContainers.forEach(container => {
                container.classList.remove('ida-fullscreen');
                const frame = container.querySelector('.ida-shortcode-frame');
                if (frame) frame.style.height = IDA_CONFIG.height;
            });
        }
    });
    
})();