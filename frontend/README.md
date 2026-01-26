# CivicLens Frontend

Modern React + Tailwind CSS frontend for the CivicLens AI platform.

## Tech Stack

- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS 3** - Utility-first CSS framework
- **PostCSS** - CSS processing

## Quick Start

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at http://localhost:5173/

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Header.jsx      # App header with navigation
│   │   └── Footer.jsx      # App footer
│   ├── App.jsx             # Main app component
│   ├── main.jsx            # Entry point
│   └── index.css           # Tailwind directives
├── public/                 # Static assets
├── index.html              # HTML template
├── tailwind.config.js      # Tailwind configuration
├── postcss.config.js       # PostCSS configuration
├── vite.config.js          # Vite configuration
└── package.json            # Dependencies
```

## Features

### Current Implementation

✅ Responsive header with branding and navigation  
✅ Hero section with call-to-action buttons  
✅ Features grid showcasing key capabilities  
✅ System status indicator  
✅ Footer with links  
✅ Tailwind CSS styling  
✅ Modern, clean UI design  

### Planned Features

- [ ] API integration with backend
- [ ] User authentication
- [ ] Policy search and filtering
- [ ] Multilingual support
- [ ] User profile management
- [ ] Dark mode toggle

## Customization

### Tailwind Configuration

Edit `tailwind.config.js` to customize colors, fonts, and other design tokens:

```javascript
export default {
  theme: {
    extend: {
      colors: {
        primary: '#your-color',
      },
    },
  },
}
```

### Components

Components are located in `src/components/`. Each component is a self-contained React functional component using Tailwind for styling.

## API Integration

To connect to the backend API, update the base URL in your API client:

```javascript
const API_BASE_URL = 'http://localhost:8000/api/v1';
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint (if configured)

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

MIT License - See LICENSE file for details
