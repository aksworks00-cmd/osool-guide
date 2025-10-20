# Osool Guide - UI Documentation

## Overview

**Osool Guide** is a minimalist web interface for the NATO Asset Codifier system. It provides an elegant, easy-to-use interface for classifying military and industrial assets according to NATO standards.

## Design

### Color Palette
- **Primary**: `#8A1538` (Burgundy) - Used for branding, buttons, and primary actions
- **Secondary**: `#A29475` (Gold) - Used for accents and data values
- **Background**: `#FAFAFA` (Light gray) - Clean, minimal background
- **Text**: `#2A2A2A` (Dark gray) - High contrast for readability

### Typography
- System fonts for optimal performance and native feel
- Minimal use of weights (300, 400, 500, 600)
- Generous spacing for clarity

### Layout
- Single-column, centered design (max-width: 800px)
- Mobile-responsive (adapts to all screen sizes)
- Clean card-based results display

## Features

### 1. **Search Interface**
- Large textarea for asset descriptions
- Keyboard shortcut: `Ctrl+Enter` to submit
- Auto-expanding textarea

### 2. **Loading States**
- Animated spinner during classification
- Disabled button to prevent duplicate requests

### 3. **Results Display**
- **NATO Codes**: NSG, NSC, INC displayed prominently
- **Confidence Bar**: Visual representation of classification confidence
- **Definition**: Full item definition from NATO database
- **Reasoning**: AI explanation of the classification decision

### 4. **Status Indicator**
- Real-time server connectivity status
- Shows total number of items in database
- Auto-refreshes every 30 seconds

### 5. **Error Handling**
- User-friendly error messages
- Network error detection
- Graceful degradation

## Usage

### Starting the Server
```bash
# From project root
python src/server.py --host 0.0.0.0 --port 8000 --workers 4
```

### Accessing the UI
Open your browser and navigate to:
```
http://localhost:8000
```

### Example Queries
Try classifying these items:
- `desktop computer`
- `M4 carbine rifle`
- `combat boots`
- `Toyota Land Cruiser 4x4`
- `Boeing 737 gas turbine accessory module`

## File Structure

```
ui/
├── index.html              # Main HTML page
├── static/
│   ├── css/
│   │   └── style.css       # Minimalist styling
│   └── js/
│       └── app.js          # Application logic & API integration
└── README.md               # This file
```

## API Integration

The UI communicates with the FastAPI backend via REST API:

### Endpoints Used
- `GET /health` - Check server status
- `POST /codify` - Classify an asset

### Request Format
```json
{
  "query": "desktop computer"
}
```

### Response Format
```json
{
  "inc": 47299,
  "name": "COMPUTER SET,DIGITAL",
  "definition": "A combination of items...",
  "nsg": 70,
  "nsc": 7010,
  "confidence": 0.85,
  "reasoning": "The item matches...",
  "error": null
}
```

## Customization

### Changing Colors
Edit `static/css/style.css` and update CSS variables:
```css
:root {
    --primary-color: #8A1538;    /* Your primary color */
    --secondary-color: #A29475;   /* Your secondary color */
}
```

### Changing API Endpoint
Edit `static/js/app.js`:
```javascript
const API_BASE_URL = 'http://your-server:8000';
```

### Adding Features
The code is modular and well-commented. Key functions:
- `handleSearch()` - Processes search requests
- `displayResults()` - Renders classification results
- `checkServerStatus()` - Monitors server health

## Browser Compatibility

Tested and working on:
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- **Page Load**: < 1 second
- **Classification Time**: 6-10 seconds (depends on backend)
- **Network Requests**: Minimal (only API calls)
- **Bundle Size**: < 50KB total

## Accessibility

- Semantic HTML structure
- High contrast colors (WCAG AA compliant)
- Keyboard navigation support
- Screen reader friendly

## Future Enhancements

Potential improvements:
- [ ] Dark mode toggle
- [ ] Search history
- [ ] Export results (PDF/CSV)
- [ ] Batch classification (multiple items)
- [ ] Advanced filters (by NSG/NSC)
- [ ] Offline mode with Service Workers
- [ ] Real-time suggestions as you type

## License

Part of the NATO Asset Codifier project.
