# Layout Guidelines

## Desktop Layouts (1200px+)

### Three-Panel Layout (CRITICAL)
The foundation of the Health Insight Assistant is the three-panel layout, each serving a specific purpose:

```
┌─────────────┬─────────────────────────┬─────────────┐
│   Sidebar   │     Main Content        │   Context   │
│   (300px)   │      (Flexible)         │   (400px)   │
│             │      (min 600px)        │             │
└─────────────┴─────────────────────────┴─────────────┘
```

#### Left Sidebar: Conversation Management
- **Width**: 300px fixed
- **Purpose**: Navigation and conversation history
- **Collapsible**: Animates to 60px icon-only mode
- **Contents**:
  - New conversation button (always visible)
  - Search bar (hides when collapsed)
  - Conversation list with auto-generated titles
  - Timestamps and preview text
- **Behavior**:
  - Smooth slide animation (300ms)
  - Maintains scroll position
  - Active conversation highlighted

#### Center Panel: Main Interaction Area
- **Width**: Flexible (min 600px, max 1200px)
- **Purpose**: Primary chat interface and content display
- **Contents**:
  - Header with page context
  - Message stream with proper spacing
  - Input area fixed at bottom
  - Tool call visualizations inline
- **Behavior**:
  - Auto-scrolls to new messages
  - Maintains 80ch max width for readability
  - Centers content with padding

#### Right Panel: Context-Sensitive Content
- **Width**: 400px flexible (can expand to 600px)
- **Purpose**: Display agent status and visualizations
- **Tab Navigation**:
  - Medical Team (default)
  - Visualization (appears when charts generated)
  - Additional tabs as needed
- **Contents per Tab**:
  
  **Medical Team Tab**:
  - Query selector dropdown
  - Team hierarchy visualization
  - Real-time agent status
  - Progress indicators
  - Analysis results section
  
  **Visualization Tab**:
  - Query selector (synced)
  - Chart container
  - Interactive controls
  - Data summary

### Multi-Agent Visualization Layout

The medical team visualization follows a hierarchical layout:

```
         CMO (80px)
         /   |   \
       /     |     \
  Spec1   Spec2   Spec3  (60px each)
    |       |       |
  Spec4   Spec5   Spec6
    |       |       |
  Spec7   Spec8   (...)
```

- **CMO Positioning**: Center-top, larger element (80px circle)
- **Specialist Arrangement**: 
  - Arc formation around CMO
  - Maximum 4 per row
  - 60px circles
  - Connected by animated lines
- **Status Visualization**:
  - **Waiting**: Gray scale, 50% opacity
  - **Thinking/Active**: Color with pulse animation
  - **Complete**: Check mark overlay
  - **Error**: Red border with X icon

## Tablet Layouts (768px - 1199px)

### Two-Panel Mode
```
┌─────────────────────────┬─────────────┐
│     Main Content        │   Context   │
│      (Flexible)         │   (350px)   │
│      (min 400px)        │             │
└─────────────────────────┴─────────────┘
```

- **Sidebar**: Hidden by default, accessible via hamburger menu
- **Main Content**: Takes primary focus
- **Context Panel**: Slightly narrower (350px)
- **Adaptations**:
  - Larger touch targets (44px minimum)
  - Simplified medical team visualization
  - Stacked agent cards instead of arc

### Portrait Orientation
- Single column for message stream
- Bottom sheet for agent status
- Swipeable tabs for panels

## Mobile Layouts (<768px)

### Single Column Layout
```
┌─────────────────┐
│     Header      │
├─────────────────┤
│                 │
│   Main Content  │
│                 │
├─────────────────┤
│  Bottom Nav     │
└─────────────────┘
```

- **Navigation**: Bottom tab bar
- **Panel Access**: Full-screen overlays
- **Adaptations**:
  - Stack all content vertically
  - Collapsible sections
  - Swipe gestures for panel access
  - Floating action button for new query

### Mobile-Specific Components

#### Condensed Medical Team View
```
┌─────────────────────────┐
│ CMO: Complete ✓         │
├─────────────────────────┤
│ ❤️ Cardiology (85%)     │
│ ████████████░░░         │
├─────────────────────────┤
│ 🧬 Endocrinology (45%)  │
│ ██████░░░░░░░░         │
├─────────────────────────┤
│ 📊 Data Analysis (...)  │
│ Waiting...              │
└─────────────────────────┘
```

#### Mobile Navigation Pattern
- **Tab Bar Items**:
  1. Conversations
  2. Current Chat
  3. Medical Team
  4. Visualizations
  5. Menu

## Breakpoints

```css
/* Mobile First Approach */
/* Base: Mobile (320px - 767px) */
.container {
  padding: 16px;
  width: 100%;
}

/* Tablet (768px - 1023px) */
@media (min-width: 768px) {
  .container {
    display: grid;
    grid-template-columns: 1fr 350px;
    gap: 0;
  }
}

/* Desktop (1024px - 1439px) */
@media (min-width: 1024px) {
  .container {
    grid-template-columns: 300px 1fr 400px;
  }
}

/* Wide (1440px+) */
@media (min-width: 1440px) {
  .container {
    max-width: 1920px;
    margin: 0 auto;
  }
  
  .main-content {
    max-width: 1200px;
  }
}
```

## Streaming UI Patterns

### Message Components
Messages appear with slide-up animation and proper spacing:

```html
<div class="message-container">
  <!-- User Message (right-aligned) -->
  <div class="flex justify-end mb-6">
    <div class="max-w-[70%]">
      <div class="bg-blue-500 text-white rounded-lg p-4">
        <p>[message content]</p>
      </div>
      <time class="text-xs text-gray-500 mt-1 block text-right">[time]</time>
    </div>
  </div>
  
  <!-- Assistant Message (left-aligned) -->
  <div class="flex mb-6">
    <div class="flex-shrink-0 w-10 h-10 rounded-full bg-gray-200 mr-3">
      [avatar]
    </div>
    <div class="max-w-[70%]">
      <div class="bg-white rounded-lg shadow-sm border p-4">
        <p>[message content]</p>
      </div>
      <time class="text-xs text-gray-500 mt-1 block">[time]</time>
    </div>
  </div>
</div>
```

### Tool Call Display
Collapsible tool calls with clear visual hierarchy:

```html
<div class="tool-call bg-gradient-to-r from-blue-50 to-indigo-50 
            border-l-3 border-blue-500 rounded-lg p-4 mb-4">
  <button class="w-full flex items-center justify-between text-left">
    <div class="flex items-center space-x-2">
      <span class="text-blue-600">🔧</span>
      <span class="font-medium text-blue-700">Tool: execute_health_query_v2</span>
    </div>
    <svg class="w-5 h-5 text-blue-600 transform transition-transform">
      <!-- Chevron icon -->
    </svg>
  </button>
  
  <div class="mt-3 pl-7 text-sm text-gray-600 hidden">
    <!-- Collapsed by default -->
    <code class="block bg-white p-3 rounded border border-gray-200">
      [tool details]
    </code>
  </div>
</div>
```

### Thinking Indicators
Show agent processing state:

```html
<!-- Inline thinking dots -->
<span class="inline-flex items-center">
  <span class="thinking-dots text-gray-500"></span>
</span>

<!-- Agent thinking card -->
<div class="bg-gray-50 rounded-lg p-4 flex items-center space-x-3">
  <div class="animate-pulse">
    <div class="w-8 h-8 bg-blue-200 rounded-full"></div>
  </div>
  <p class="text-sm text-gray-600">
    Dr. Heart is analyzing your cardiovascular data...
  </p>
</div>
```

## Grid Systems

### 12-Column Grid (Desktop)
```css
.grid-container {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 24px;
}

/* Sidebar: 3 columns */
.sidebar { grid-column: span 3; }

/* Main: 6 columns */
.main { grid-column: span 6; }

/* Context: 3 columns */
.context { grid-column: span 3; }
```

### 8-Column Grid (Tablet)
```css
@media (min-width: 768px) and (max-width: 1023px) {
  .grid-container {
    grid-template-columns: repeat(8, 1fr);
    gap: 16px;
  }
  
  .main { grid-column: span 5; }
  .context { grid-column: span 3; }
}
```

### 4-Column Grid (Mobile)
```css
@media (max-width: 767px) {
  .grid-container {
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }
  
  .full-width { grid-column: span 4; }
}
```

## Spacing Guidelines

### Consistent Spacing Scale
Use multiples of 8px for all spacing:

```css
/* Spacing variables */
--space-1: 4px;   /* Tight spacing */
--space-2: 8px;   /* Default small */
--space-3: 12px;  /* Compact */
--space-4: 16px;  /* Standard */
--space-5: 20px;  /* Comfortable */
--space-6: 24px;  /* Spacious */
--space-8: 32px;  /* Section spacing */
--space-10: 40px; /* Large sections */
--space-12: 48px; /* Extra large */
--space-16: 64px; /* Page sections */
```

### Component Spacing Rules

#### Cards
- Padding: 24px (desktop), 16px (mobile)
- Margin between cards: 16px
- Internal element spacing: 12px

#### Messages
- Between messages: 24px
- Avatar to content: 12px
- Message padding: 16px

#### Form Elements
- Label to input: 4px
- Between form fields: 16px
- Button group spacing: 12px

## Responsive Typography

### Font Size Scaling
```css
/* Base (Mobile) */
h1 { font-size: 24px; line-height: 32px; }
h2 { font-size: 20px; line-height: 28px; }
h3 { font-size: 18px; line-height: 26px; }
body { font-size: 14px; line-height: 20px; }

/* Tablet and up */
@media (min-width: 768px) {
  h1 { font-size: 30px; line-height: 38px; }
  h2 { font-size: 24px; line-height: 32px; }
  h3 { font-size: 20px; line-height: 28px; }
  body { font-size: 16px; line-height: 24px; }
}
```

### Line Length
- Optimal: 45-75 characters
- Maximum container: 80ch for readability
- Adjust font size to maintain line length

## Touch Targets

### Minimum Sizes
- Touch targets: 44x44px minimum
- Spacing between targets: 8px minimum
- Buttons: 48px height on mobile
- Links: Add padding for larger hit area

### Mobile Interactions
```css
/* Enhance touch targets on mobile */
@media (max-width: 767px) {
  button, a, .clickable {
    min-height: 44px;
    min-width: 44px;
    padding: 12px;
  }
  
  /* Add tap highlight */
  * {
    -webkit-tap-highlight-color: rgba(59, 130, 246, 0.1);
  }
}
```

## Performance Considerations

### Layout Optimization
1. Use CSS Grid for major layout
2. Flexbox for component layouts
3. Avoid deep nesting
4. Minimize reflows during updates

### Lazy Loading Patterns
```html
<!-- Lazy load panels -->
<div class="panel" data-lazy="true">
  <div class="skeleton-loader">
    <!-- Show while loading -->
  </div>
</div>

<!-- Intersection Observer for charts -->
<div class="chart-container" data-observe="true">
  <!-- Load when visible -->
</div>
```

### Animation Performance
- Use `transform` and `opacity` for animations
- Avoid animating `width`, `height`, `top`, `left`
- Enable GPU acceleration with `will-change`
- Limit concurrent animations

## Adaptive Loading

### Network-Aware Loading
```javascript
// Adjust based on connection
if (navigator.connection?.effectiveType === '4g') {
  // Load full experience
} else {
  // Simplified version
  // Fewer animations
  // Compressed assets
}
```

### Progressive Enhancement
1. Core content first
2. Enhance with JavaScript
3. Add animations last
4. Provide fallbacks

This layout system ensures the Health Insight Assistant provides an optimal experience across all devices while maintaining the sophisticated multi-agent visualization that makes the system unique.