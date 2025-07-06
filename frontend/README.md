# Multi-Agent Health Insight System v2 - Frontend

A sophisticated React TypeScript frontend showcasing Anthropic's multi-agent orchestration patterns with real-time medical team visualization, progressive specialist disclosure, and dynamic health data visualizations.

## 🏗️ Architecture Overview

This frontend implements a comprehensive medical team interface that demonstrates:
- **Orchestrator-Worker Pattern**: Visual representation of CMO (Chief Medical Officer) delegating to specialist agents
- **Real-time Status Updates**: Live SSE streaming showing specialist progress and analysis
- **Progressive Disclosure**: Specialists revealed as they're activated
- **Multi-Query Support**: Thread-based conversations with multiple health queries per thread
- **Dynamic Visualizations**: Auto-generated charts and dashboards from specialist analysis

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn
- Backend API running on port 8000

### Installation

```bash
# Install dependencies
npm install

# Configure environment (optional - defaults to localhost:8000)
cp .env.example .env.local

# Start development server
npm run dev
```

Application will be available at http://localhost:5173

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Deploy dist/ folder to your hosting service
```

## 📁 Project Structure

```
src/
├── components/                 # React components
│   ├── TwoPanelLayout.tsx     # Main orchestrator component
│   ├── ChatInterface.tsx      # SSE streaming & chat UI
│   ├── WelcomeState.tsx       # Three-panel onboarding
│   ├── EnhancedHeader.tsx     # Header with profile & reset
│   ├── ThreadSidebar.tsx      # Conversation management
│   ├── MessageBubble.tsx      # Individual chat messages
│   ├── CodeArtifact.tsx       # Dynamic React component execution
│   ├── VisualizationPanel.tsx # Multi-chart visualization support
│   ├── TabContainer.tsx       # Generic tab container
│   ├── medical-team/          # Medical team components
│   │   ├── MedicalTeamTab.tsx
│   │   ├── MedicalTeamOrgChart.tsx
│   │   ├── AgentCard.tsx
│   │   ├── StreamingAnalysis.tsx
│   │   ├── CompactQuerySelector.tsx
│   │   └── QuerySelector.tsx
│   └── visualizations/        # Data visualization components
│       ├── DataTable.tsx
│       └── ImportDashboard.tsx
├── services/                  # API integration layer
│   ├── api.ts                # Typed API client
│   └── sseEventParser.ts     # SSE to team state parser
├── types/                     # TypeScript definitions
│   ├── index.ts              # Core application types
│   └── medical-team.ts       # Medical team specific types
├── App.tsx                   # Root application component
├── main.tsx                  # Application entry point
└── index.css                 # Tailwind CSS & custom styles
```

## 🧩 Key Components

### TwoPanelLayout
The main orchestrator component managing the entire application state and layout.

**Features:**
- Three-panel responsive layout with resizable dividers
- Global state management (welcome → idle → analyzing → complete)
- Thread persistence with localStorage
- Visualization history per thread
- Multi-query support per conversation

**State Flow:**
```
welcome → idle → cmo-analyzing → team-assembling → team-working → synthesizing → visualizing → complete
```

### ChatInterface
Handles real-time SSE streaming and message management.

**Features:**
- Server-Sent Events (SSE) connection management
- Real-time code artifact extraction
- Auto-scrolling with query highlighting
- Comprehensive error handling for service overloads
- Dynamic visualization detection

**SSE Event Types:**
- `text`: Regular message content
- `thinking`: CMO reasoning and specialist status
- `tool_call`: Tool execution transparency
- `visualization`: Chart generation triggers

### MedicalTeamTab
Real-time medical team visualization with progressive specialist disclosure.

**Features:**
- Two-section layout: Org chart + Streaming analysis
- Query-based data management
- Live progress tracking (per-agent and overall)
- Specialist status animations
- CMO synthesis display

### SSEEventParser
Sophisticated parser converting SSE events to medical team state.

**Pattern Recognition:**
```typescript
// Specialist activation
"❤️ **Cardiology** is analyzing your health data..."

// Completion with metrics
"✅ **Laboratory** completed analysis (12 queries executed, 95% confidence)"
```

**Supported Specialists:**
- ❤️ Cardiology
- 🔬 Laboratory Medicine
- 💊 Endocrinology
- 📊 Data Analysis
- 🛡️ Preventive Medicine
- 💉 Pharmacy
- 🥗 Nutrition
- ⚕️ General Practice

### CodeArtifact
Dynamic React component executor for visualizations.

**Features:**
- Real-time Babel compilation
- Live preview/code toggle
- Streaming code updates
- Recharts & Lucide integration
- Comprehensive error boundaries

## 🎨 Design System

### Theme
Light mode medical interface with health-appropriate aesthetics:
- **Background**: Subtle blue/purple gradient (`gradient-health-subtle`)
- **Primary**: Blue shades (#3b82f6)
- **Health Status**: 
  - Normal: Green (#10b981)
  - Warning: Yellow (#f59e0b)
  - Critical: Red (#ef4444)

### Animations
- `pulse-soft`: Subtle pulsing for active elements
- `fadeInUp`: Staggered specialist card appearances
- `dashAnimation`: Animated connection lines
- `blink`: Terminal cursor effect

### Glassmorphism
- `.glass-health`: Medical-themed glass effect
- `.glass-subtle`: Subtle backdrop blur

## 🔄 State Management

### Application States
```typescript
type AppState = 
  | 'welcome'        // Initial onboarding
  | 'idle'          // Ready for queries
  | 'cmo-analyzing' // CMO processing query
  | 'team-assembling' // Specialists being selected
  | 'team-working'  // Specialists analyzing
  | 'synthesizing'  // CMO creating summary
  | 'visualizing'   // Generating charts
  | 'complete'      // Analysis complete
```

### Persistence
- **Threads**: `localStorage.healthThreads`
- **Visualizations**: `localStorage.vizHistory`
- **Auto-send**: `localStorage.pendingQuestion`

## 🔌 API Integration

### Service Layer (`services/api.ts`)
```typescript
// Chat streaming
const eventSource = chatService.sendMessage({
  message: "Analyze my cholesterol trends",
  conversationId: threadId,
  enableExtendedThinking: true
});

// Health data operations
await healthService.importData({ directory: "/path/to/data" });
await healthService.queryData({ query: "SELECT * FROM lab_results" });
```

### SSE Event Handling
```typescript
eventSource.onmessage = (event) => {
  const chunk: StreamChunk = JSON.parse(event.data);
  switch (chunk.type) {
    case 'thinking':
      // Update team state
    case 'text':
      // Append to messages
    case 'visualization':
      // Generate chart
  }
};
```

## 🛠️ Development

### Available Scripts
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run type-check   # TypeScript validation
```

### Environment Variables
```env
VITE_API_URL=http://localhost:8000  # Backend API URL
```

### Adding New Features

#### New Specialist
1. Add to `medical-team.ts` types
2. Update `SSEEventParser` patterns
3. Add icon mapping in `AgentCard`
4. Update specialist configurations

#### New Visualization
1. Create component in `visualizations/`
2. Add case in `VisualizationCard`
3. Update visualization types
4. Handle in `CodeArtifact`

## 🚢 Deployment

### Docker
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

### Static Hosting
Compatible with:
- Vercel
- Netlify
- AWS S3 + CloudFront
- GitHub Pages
- Cloudflare Pages

## 🐛 Troubleshooting

### Common Issues

**SSE Connection Drops**
- Check CORS configuration in backend
- Verify API URL in environment
- Monitor browser DevTools Network tab

**Team Updates Not Showing**
- Check console for `[SSEParser]` logs
- Verify specialist patterns in messages
- Ensure proper event propagation

**Visualizations Not Rendering**
- Check for React component syntax errors
- Verify Recharts import availability
- Monitor CodeArtifact error boundaries

### Debug Mode
Enable detailed logging:
```javascript
// In browser console
localStorage.setItem('DEBUG', 'true');
```

## 📚 Key Patterns & Best Practices

### Component Composition
- Heavy use of composition over inheritance
- Clear parent-child relationships
- Props drilling minimized via context

### Performance Optimizations
- React.memo for expensive renders
- Lazy loading for visualizations
- Virtual scrolling ready (not yet implemented)
- Debounced resize handlers

### Error Handling
- Error boundaries for chart rendering
- Graceful SSE reconnection
- User-friendly error messages
- Fallback UI states

### Accessibility
- Semantic HTML structure
- ARIA labels for interactive elements
- Keyboard navigation support
- Focus management

## 🔗 Related Documentation

- [Backend README](../backend/README.md)
- [CLAUDE.md](../CLAUDE.md) - AI assistant guidelines
- [API Documentation](../backend/docs/api.md)
- [Deployment Guide](../docs/deployment.md)

## 📄 License

This project demonstrates Anthropic's best practices for multi-agent systems and is provided as an educational resource.