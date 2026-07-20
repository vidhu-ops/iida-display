# IDA Research Platform - Integration Guide

## Overview

This guide shows you how to integrate the IDA Research Platform into any website using our shortcode system. The platform provides comprehensive AI-powered research and analysis capabilities that can be embedded seamlessly into your existing web properties.

## Integration Methods

### Method 1: Full HTML Shortcode (Recommended for WordPress/CMS)

Use the complete HTML file for maximum control and customization:

```html
<!-- Include the full shortcode -->
<iframe src="https://your-ida-domain.replit.app/shortcode.html" 
        width="100%" 
        height="900px" 
        style="border: none; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
</iframe>
```

### Method 2: JavaScript Shortcode (Best for Custom Websites)

#### Step 1: Include the JavaScript file

```html
<script src="https://your-ida-domain.replit.app/ida-shortcode.js"></script>
```

#### Step 2: Create a container (Optional)

```html
<div id="ida-research-platform"></div>
```

#### Step 3: Initialize (if custom container needed)

```javascript
// Auto-initializes if container with id="ida-research-platform" exists
// Or create custom instance:
window.IDAShortcode.create({
    containerId: 'my-custom-ida-container',
    baseUrl: 'https://your-ida-domain.replit.app',
    width: '100%',
    height: '800px',
    title: '🔬 Research Platform',
    subtitle: 'Custom Integration'
});
```

### Method 3: WordPress Shortcode

Create a WordPress plugin or add to functions.php:

```php
function ida_research_shortcode($atts) {
    $attributes = shortcode_atts(array(
        'width' => '100%',
        'height' => '800px',
        'title' => 'IDA Research Platform'
    ), $atts);
    
    wp_enqueue_script('ida-shortcode', 'https://your-ida-domain.replit.app/ida-shortcode.js');
    
    return '
    <div id="ida-research-platform-' . uniqid() . '"></div>
    <script>
        document.addEventListener("DOMContentLoaded", function() {
            window.IDAShortcode.create({
                containerId: "ida-research-platform-' . uniqid() . '",
                baseUrl: "https://your-ida-domain.replit.app",
                width: "' . $attributes['width'] . '",
                height: "' . $attributes['height'] . '",
                title: "' . $attributes['title'] . '"
            });
        });
    </script>';
}
add_shortcode('ida_research', 'ida_research_shortcode');
```

Usage in WordPress:
```
[ida_research width="100%" height="600px" title="My Research Tool"]
```

### Method 4: React Component

```jsx
import React, { useEffect, useRef } from 'react';

const IDAResearchPlatform = ({ 
    width = '100%', 
    height = '800px',
    title = 'IDA Research Platform'
}) => {
    const containerRef = useRef(null);
    const idaIdRef = useRef(`ida-research-${Math.random().toString(36).substr(2, 9)}`);

    useEffect(() => {
        // Load IDA shortcode script
        const script = document.createElement('script');
        script.src = 'https://your-ida-domain.replit.app/ida-shortcode.js';
        script.onload = () => {
            if (window.IDAShortcode) {
                window.IDAShortcode.create({
                    containerId: idaIdRef.current,
                    baseUrl: 'https://your-ida-domain.replit.app',
                    width: width,
                    height: height,
                    title: title
                });
            }
        };
        document.head.appendChild(script);

        return () => {
            document.head.removeChild(script);
        };
    }, [width, height, title]);

    return <div id={idaIdRef.current} ref={containerRef}></div>;
};

export default IDAResearchPlatform;
```

### Method 5: Simple Iframe (Quickest Setup)

```html
<iframe 
    src="https://your-ida-domain.replit.app" 
    width="100%" 
    height="800px" 
    style="border: 1px solid #ddd; border-radius: 8px;">
</iframe>
```

## Configuration Options

### JavaScript Configuration

```javascript
window.IDAShortcode.create({
    containerId: 'ida-container',           // Container element ID
    baseUrl: 'https://your-domain.com',     // Your IDA deployment URL
    width: '100%',                          // Width (CSS value)
    height: '800px',                        // Height (CSS value)
    title: 'Custom Title',                  // Header title
    subtitle: 'Custom Subtitle'            // Header subtitle
});
```

### CSS Customization

Override default styles by adding CSS:

```css
/* Custom header colors */
.ida-shortcode-header {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
}

/* Custom container styling */
.ida-shortcode-container {
    border: 2px solid #007bff !important;
    border-radius: 12px !important;
}

/* Remove footer */
.ida-shortcode-footer {
    display: none !important;
}
```

## Advanced Features

### Fullscreen Support

The shortcode includes built-in fullscreen functionality:
- Click "⛶ Fullscreen" in the footer
- Press ESC to exit fullscreen
- Programmatic control: `window.IDAShortcode.toggleFullscreen('container-id')`

### Refresh Functionality

Reload the embedded platform:
- Click "🔄 Refresh" in the footer
- Programmatic control: `window.IDAShortcode.refreshFrame('container-id')`

### Multiple Instances

You can embed multiple IDA instances on the same page:

```javascript
// Create multiple research platforms
window.IDAShortcode.create({
    containerId: 'ida-platform-1',
    title: 'Market Research'
});

window.IDAShortcode.create({
    containerId: 'ida-platform-2',
    title: 'Competitive Analysis'
});
```

## Security Considerations

1. **HTTPS Only**: Always use HTTPS URLs for production
2. **Content Security Policy**: Add your IDA domain to CSP if applicable
3. **CORS**: Ensure your IDA deployment allows embedding from your domain

## Troubleshooting

### Common Issues

**Issue**: Shortcode not loading
- **Solution**: Check network connectivity and ensure IDA domain is accessible

**Issue**: Styling conflicts
- **Solution**: Use CSS specificity or iframe isolation

**Issue**: Mobile responsiveness
- **Solution**: The shortcode is responsive by default, but ensure parent containers allow flexibility

### Debug Mode

Add debug parameter to see loading status:

```javascript
window.IDAShortcode.create({
    containerId: 'ida-debug',
    debug: true  // Shows console logs
});
```

## Examples

### Blog Integration
```html
<!-- In your blog post -->
<div class="research-embed">
    <h3>Market Analysis Tool</h3>
    <div id="ida-research-platform"></div>
</div>
<script src="https://your-ida-domain.replit.app/ida-shortcode.js"></script>
```

### Dashboard Widget
```html
<!-- Dashboard widget -->
<div class="widget-container">
    <script>
        window.IDAShortcode.create({
            containerId: 'dashboard-ida-widget',
            height: '400px',
            title: 'Quick Research',
            subtitle: 'Dashboard Widget'
        });
    </script>
    <div id="dashboard-ida-widget"></div>
</div>
```

## Support

For integration support and customization requests, contact your development team or refer to the main IDA documentation.

## Update Instructions

1. Replace `https://your-ida-domain.replit.app` with your actual IDA deployment URL
2. Test the integration in a development environment first
3. Customize CSS and configuration as needed
4. Deploy to production

---

**Note**: Remember to update the `baseUrl` in all examples to match your actual IDA deployment URL.