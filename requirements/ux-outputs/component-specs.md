# Component Specifications

## Component: Header Navigation

### Purpose
Global navigation bar with branding, user info, and settings access

### Anatomy
- Logo and brand name (left)
- Page title (center)
- User menu (right)
- Settings icon (right)

### States
- Default: White background with subtle shadow
- Scrolled: Glass effect with blur
- Loading: Shimmer effect on user info

### Variants
- Full width on desktop
- Collapsed logo on mobile

### Props/Configuration
- `showUserInfo`: boolean
- `pageTitle`: string
- `onSettingsClick`: function

### Interaction Behavior
- Settings icon opens modal
- User menu shows dropdown
- Logo clicks to home

### Accessibility
- Skip navigation link
- ARIA landmarks
- Keyboard navigation

### Implementation Notes
```jsx
<header className="fixed top-0 w-full h-16 bg-white/90 backdrop-blur-md border-b border-gray-200 z-50">
  <div className="flex items-center justify-between h-full px-6">
    <div className="flex items-center space-x-3">
      <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
        <LucideIcon name="briefcase-medical" className="w-6 h-6 text-white" />
      </div>
      <div>
        <h1 className="text-lg font-semibold">Health Insight Assistant</h1>
        <p className="text-xs text-gray-500">Powered by Multi-Agent AI • Snowflake Cortex</p>
      </div>
    </div>
  </div>
</header>
```

---

## Component: Conversation Sidebar

### Purpose
Display and manage multiple conversation threads

### Anatomy
- New conversation button (top)
- Search bar
- Conversation list
- Each item: title, timestamp, preview

### States
- Default: List view
- Hover: Highlight item
- Active: Blue border and background
- Loading: Skeleton items

### Variants
- Expanded (280px width)
- Collapsed (icon only)
- Mobile drawer

### Props/Configuration
- `conversations`: Conversation[]
- `activeId`: string
- `onSelect`: function
- `onNewConversation`: function

### Interaction Behavior
- Click to select conversation
- Hover shows full title
- Delete on hover (icon appears)
- Drag to reorder (future)

### Accessibility
- Role="navigation"
- ARIA-current for active
- Keyboard arrow navigation

### Implementation Notes
```jsx
<aside className="w-[280px] h-full bg-white border-r border-gray-200 flex flex-col">
  <div className="p-4">
    <button className="w-full btn-primary flex items-center justify-center space-x-2">
      <Plus className="w-4 h-4" />
      <span>New Health Conversation</span>
    </button>
  </div>
  <div className="flex-1 overflow-y-auto">
    {conversations.map(conv => (
      <ConversationItem key={conv.id} {...conv} />
    ))}
  </div>
</aside>
```

---

## Component: Medical Team Card

### Purpose
Display specialist agent status and progress in real-time

### Anatomy
- Agent avatar with specialty icon
- Name and specialty label
- Status indicator (dot)
- Progress bar (when active)
- Confidence percentage (when complete)

### States
- Waiting: Gray, 50% opacity
- Active: Full color, pulsing animation
- Complete: Check mark overlay
- Error: Red indicator

### Variants
- CMO (larger, centered)
- Specialist (smaller, in grid)
- Compact (mobile view)

### Props/Configuration
```typescript
interface MedicalTeamCardProps {
  agentId: string;
  name: string;
  specialty: MedicalSpecialty;
  status: 'waiting' | 'active' | 'complete' | 'error';
  progress?: number;
  confidence?: number;
  color: string;
  icon: string;
}
```

### Interaction Behavior
- Hover shows tooltip with details
- Click expands analysis (when complete)
- Progress animates smoothly

### Accessibility
- ARIA-label with full status
- Live region for updates
- Sufficient color contrast

### Implementation Notes
```jsx
<div className={`
  relative p-4 rounded-xl transition-all duration-300
  ${status === 'waiting' ? 'opacity-50 grayscale' : ''}
  ${status === 'active' ? 'animate-pulse-subtle' : ''}
  border-2 border-${color}-200 bg-white
`}>
  <div className="flex flex-col items-center">
    <div className={`
      w-16 h-16 rounded-full flex items-center justify-center
      bg-${color}-100 text-${color}-600
      ${status === 'active' ? 'animate-pulse' : ''}
    `}>
      <Icon name={icon} className="w-8 h-8" />
    </div>
    <h3 className="mt-2 font-semibold">{name}</h3>
    <p className="text-sm text-gray-500">{specialty}</p>
    
    {status === 'active' && (
      <div className="w-full mt-3">
        <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className={`h-full bg-${color}-500 transition-all duration-500`}
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-xs text-center mt-1">{progress}%</p>
      </div>
    )}
    
    {status === 'complete' && (
      <div className="absolute -bottom-2 -right-2 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
        <Check className="w-4 h-4 text-white" />
      </div>
    )}
  </div>
</div>
```

---

## Component: Chat Message

### Purpose
Display user queries and AI responses with appropriate formatting

### Anatomy
- Avatar/icon
- Role indicator
- Message content
- Timestamp
- Metadata (tokens, confidence)

### States
- Default: Static display
- Streaming: Animated dots
- Error: Red accent
- Tool call: Collapsible detail

### Variants
- User message: Right-aligned, blue
- Assistant message: Left-aligned, gray
- System message: Centered, muted

### Props/Configuration
- `role`: 'user' | 'assistant' | 'system'
- `content`: string | StreamingContent
- `timestamp`: Date
- `metadata`: MessageMetadata

### Interaction Behavior
- Tool calls collapse/expand
- Code blocks have copy button
- Long messages truncate

### Accessibility
- Semantic HTML structure
- Screen reader announcements
- Keyboard-navigable actions

### Implementation Notes
```jsx
<div className={`flex gap-3 p-4 ${role === 'user' ? 'flex-row-reverse' : ''}`}>
  <div className={`
    w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0
    ${role === 'user' ? 'bg-blue-500' : 'bg-gray-200'}
  `}>
    {role === 'user' ? <User /> : <Bot />}
  </div>
  
  <div className={`
    max-w-[70%] rounded-lg p-4
    ${role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100'}
  `}>
    <div className="prose prose-sm">
      {content}
    </div>
    <time className="text-xs opacity-70 mt-2 block">
      {timestamp.toLocaleTimeString()}
    </time>
  </div>
</div>
```

---

## Component: Query Input

### Purpose
Primary interface for users to submit health questions

### Anatomy
- Text input field
- Submit button
- Character counter
- Voice input (future)

### States
- Default: Empty, placeholder visible
- Typing: Character count updates
- Submitting: Loading state
- Disabled: During analysis

### Variants
- Welcome page: Larger, centered
- Chat page: Bottom bar style

### Props/Configuration
- `onSubmit`: function
- `placeholder`: string
- `maxLength`: number (500)
- `disabled`: boolean

### Interaction Behavior
- Enter key submits
- Shift+Enter for new line
- Auto-grow height
- Clear button when typed

### Accessibility
- Label for screen readers
- Error announcements
- Keyboard shortcuts

### Implementation Notes
```jsx
<form onSubmit={handleSubmit} className="p-4 border-t border-gray-200 bg-white">
  <div className="flex gap-3">
    <textarea
      className="flex-1 resize-none rounded-lg border border-gray-300 p-3 
                 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
      placeholder="Ask about labs, medications, correlations, or health..."
      rows={1}
      maxLength={500}
      value={query}
      onChange={(e) => setQuery(e.target.value)}
      onKeyDown={handleKeyDown}
    />
    <button 
      type="submit"
      disabled={!query.trim() || isLoading}
      className="btn-primary px-6"
    >
      {isLoading ? <Loader className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
    </button>
  </div>
  <div className="text-xs text-gray-500 mt-2 text-right">
    {query.length}/500
  </div>
</form>
```

---

## Component: Example Query Card

### Purpose
Provide quick-start options on welcome screen

### Anatomy
- Icon representing query type
- Query text
- Complexity badge
- Hover state with glow

### States
- Default: White with border
- Hover: Elevated shadow, slight scale
- Clicked: Brief press animation

### Variants
- Simple: Green badge
- Standard: Blue badge
- Complex: Orange badge

### Props/Configuration
- `query`: string
- `complexity`: 'simple' | 'standard' | 'complex'
- `icon`: LucideIcon
- `onClick`: function

### Interaction Behavior
- Click submits query immediately
- Hover shows full query if truncated
- Keyboard accessible

### Accessibility
- Button role
- Descriptive label
- Focus indicators

### Implementation Notes
```jsx
<button
  onClick={() => onSubmit(query)}
  className="group p-6 bg-white rounded-xl border-2 border-gray-200 
             hover:border-blue-500 hover:shadow-lg transition-all duration-300
             hover:scale-[1.02] active:scale-[0.98]"
>
  <div className="flex items-start gap-4">
    <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center
                    group-hover:bg-blue-200 transition-colors">
      <Icon className="w-6 h-6 text-blue-600" />
    </div>
    <div className="flex-1 text-left">
      <p className="font-medium text-gray-900">{query}</p>
      <span className={`
        inline-block mt-2 px-2 py-1 text-xs rounded-full
        ${complexity === 'simple' ? 'bg-green-100 text-green-700' : ''}
        ${complexity === 'standard' ? 'bg-blue-100 text-blue-700' : ''}
        ${complexity === 'complex' ? 'bg-orange-100 text-orange-700' : ''}
      `}>
        {complexity} • {expectedSpecialists} specialists
      </span>
    </div>
  </div>
</button>
```

---

## Component: Visualization Container

### Purpose
Render dynamically generated charts and data visualizations

### Anatomy
- Chart title and description
- Interactive chart area
- Legend (toggleable)
- Controls (zoom, pan, export)
- Data table toggle

### States
- Loading: Skeleton loader
- Rendered: Full interactivity
- Error: Fallback message
- Updating: Subtle overlay

### Variants
- Time series line chart
- Comparison bar chart
- Correlation scatter plot
- Distribution histogram

### Props/Configuration
- `code`: string (React component)
- `metadata`: VisualizationMetadata
- `onError`: function

### Interaction Behavior
- Hover for tooltips
- Click legend to toggle series
- Drag to zoom
- Double-click to reset

### Accessibility
- Chart descriptions
- Keyboard navigation
- Screen reader data table
- High contrast mode

### Implementation Notes
```jsx
<div className="bg-white rounded-xl p-6 border border-gray-200">
  <div className="mb-4">
    <h3 className="text-lg font-semibold">{metadata.title}</h3>
    <p className="text-sm text-gray-600">{metadata.description}</p>
  </div>
  
  <div className="relative">
    {isLoading && (
      <div className="absolute inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center">
        <Loader className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    )}
    
    <div id="chart-container" className="w-full h-[400px]">
      {/* Dynamically rendered chart */}
    </div>
  </div>
  
  <div className="mt-4 flex justify-between items-center">
    <button className="text-sm text-blue-600 hover:text-blue-700">
      View data table
    </button>
    <div className="flex gap-2">
      <button className="p-2 hover:bg-gray-100 rounded">
        <Download className="w-4 h-4" />
      </button>
      <button className="p-2 hover:bg-gray-100 rounded">
        <Maximize2 className="w-4 h-4" />
      </button>
    </div>
  </div>
</div>
```

---

## Component: Query Selector

### Purpose
Navigate between multiple queries in a conversation

### Anatomy
- Dropdown trigger
- Query list with numbers
- Current selection indicator
- Query preview text

### States
- Closed: Shows current query
- Open: Dropdown list
- Hover: Highlight option

### Variants
- Medical team tab version
- Visualization tab version

### Props/Configuration
- `queries`: Query[]
- `currentIndex`: number
- `onChange`: function

### Interaction Behavior
- Click to open dropdown
- Select to navigate
- Escape to close
- Updates all related panels

### Accessibility
- Combobox pattern
- Arrow key navigation
- Live region updates

### Implementation Notes
```jsx
<div className="relative">
  <button
    onClick={() => setOpen(!open)}
    className="flex items-center justify-between w-full p-3 bg-white 
               border border-gray-300 rounded-lg hover:border-gray-400"
  >
    <span className="flex items-center gap-2">
      <span className="text-sm text-gray-500">Query {currentIndex + 1} of {queries.length}</span>
      <ChevronDown className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} />
    </span>
  </button>
  
  {open && (
    <div className="absolute top-full mt-1 w-full bg-white border border-gray-200 
                    rounded-lg shadow-lg z-10 max-h-64 overflow-y-auto">
      {queries.map((query, index) => (
        <button
          key={index}
          onClick={() => handleSelect(index)}
          className={`
            w-full p-3 text-left hover:bg-gray-50 
            ${index === currentIndex ? 'bg-blue-50 border-l-4 border-blue-500' : ''}
          `}
        >
          <div className="text-sm font-medium">Query {index + 1}</div>
          <div className="text-xs text-gray-600 truncate">{query.text}</div>
        </button>
      ))}
    </div>
  )}
</div>
```

---

## Component: Progress Indicator

### Purpose
Show real-time progress of agent analysis

### Anatomy
- Progress bar or circle
- Percentage text
- Activity label
- ETA (when available)

### States
- Idle: Hidden
- Active: Animated fill
- Complete: Full, success color
- Error: Red color

### Variants
- Linear bar (specialist cards)
- Circular (CMO overview)
- Stepped (multi-phase)

### Props/Configuration
- `value`: 0-100
- `label`: string
- `color`: string
- `showPercentage`: boolean

### Interaction Behavior
- Smooth transitions
- No direct interaction
- Updates via SSE

### Accessibility
- Role="progressbar"
- aria-valuenow
- aria-label with context

### Implementation Notes
```jsx
// Linear progress
<div className="w-full">
  <div className="flex justify-between text-xs mb-1">
    <span className="text-gray-600">{label}</span>
    {showPercentage && <span className="font-medium">{value}%</span>}
  </div>
  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
    <div
      className="h-full bg-gradient-to-r from-blue-500 to-blue-600 
                 rounded-full transition-all duration-500 ease-out"
      style={{ width: `${value}%` }}
    />
  </div>
</div>

// Circular progress
<svg className="w-20 h-20 transform -rotate-90">
  <circle
    cx="40"
    cy="40"
    r="36"
    stroke="#E5E7EB"
    strokeWidth="8"
    fill="none"
  />
  <circle
    cx="40"
    cy="40"
    r="36"
    stroke={color}
    strokeWidth="8"
    fill="none"
    strokeDasharray={`${2 * Math.PI * 36}`}
    strokeDashoffset={`${2 * Math.PI * 36 * (1 - value / 100)}`}
    className="transition-all duration-500 ease-out"
  />
</svg>
```

---

## Component: Analysis Results Card

### Purpose
Display completed analysis from specialists

### Anatomy
- Specialist avatar and name
- Confidence score
- Key findings summary
- Timestamp
- Expand/collapse control

### States
- Collapsed: Summary only
- Expanded: Full details
- Highlighted: New result

### Variants
- Compact (sidebar)
- Detailed (main view)

### Props/Configuration
- `specialist`: SpecialistInfo
- `result`: AnalysisResult
- `defaultExpanded`: boolean

### Interaction Behavior
- Click header to toggle
- Smooth expand animation
- Copy findings button

### Accessibility
- Expandable region pattern
- Clear heading hierarchy
- Keyboard navigation

### Implementation Notes
```jsx
<div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
  <button
    onClick={() => setExpanded(!expanded)}
    className="w-full p-4 flex items-center justify-between hover:bg-gray-50"
  >
    <div className="flex items-center gap-3">
      <div className={`w-10 h-10 rounded-full bg-${specialist.color}-100 
                      flex items-center justify-center`}>
        <Icon name={specialist.icon} className={`w-5 h-5 text-${specialist.color}-600`} />
      </div>
      <div className="text-left">
        <h4 className="font-medium">{specialist.name}</h4>
        <p className="text-sm text-gray-500">
          Analysis complete with {result.confidence}% confidence
        </p>
      </div>
    </div>
    <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform 
                            ${expanded ? 'rotate-180' : ''}`} />
  </button>
  
  {expanded && (
    <div className="px-4 pb-4 border-t border-gray-100">
      <div className="mt-3 space-y-2">
        {result.findings.map((finding, i) => (
          <div key={i} className="text-sm">
            <span className="font-medium">{finding.title}:</span>
            <span className="text-gray-600 ml-1">{finding.detail}</span>
          </div>
        ))}
      </div>
    </div>
  )}
</div>
```