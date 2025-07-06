# Design System: Health Insight Assistant

## Brand Principles
- **Trustworthy**: Medical-grade accuracy with transparent processes
- **Intelligent**: Advanced AI orchestration made approachable
- **Accessible**: Complex health insights simplified
- **Professional**: Clinical expertise with human warmth
- **Responsive**: Real-time analysis with visual feedback

## Color Palette

### Primary Colors
- **Primary Blue**: `#3B82F6` (RGB: 59, 130, 246)
  - Used for: Primary buttons, logo, active states, links, CMO agent
  - Represents: Trust, stability, medical professionalism

- **Pure White**: `#FFFFFF` (RGB: 255, 255, 255)
  - Used for: Primary backgrounds, cards, clean slate
  - Represents: Cleanliness, clarity, medical sterility

### Medical Specialist Colors
Each specialist has a unique color for instant recognition:

- **Cardiology Red**: `#EF4444` (RGB: 239, 68, 68) - Dr. Heart
- **Laboratory Green**: `#10B981` (RGB: 16, 185, 129) - Dr. Lab
- **Endocrinology Purple**: `#8B5CF6` (RGB: 139, 92, 246) - Dr. Hormone
- **Data Analysis Yellow**: `#F59E0B` (RGB: 245, 158, 11) - Dr. Analytics
- **Preventive Orange**: `#F97316` (RGB: 249, 115, 22) - Dr. Prevention
- **Pharmacy Orange**: `#FB923C` (RGB: 251, 146, 60) - Dr. Pharma
- **Nutrition Lime**: `#84CC16` (RGB: 132, 204, 22) - Dr. Nutrition
- **General Practice Cyan**: `#06B6D4` (RGB: 6, 182, 212) - Dr. Primary

### Neutral Colors
- **Background Gray**: `#F9FAFB` (RGB: 249, 250, 251)
- **Surface Gray**: `#F3F4F6` (RGB: 243, 244, 246)
- **Border Gray**: `#E5E7EB` (RGB: 229, 231, 235)
- **Text Primary**: `#111827` (RGB: 17, 24, 39)
- **Text Secondary**: `#6B7280` (RGB: 107, 114, 128)
- **Text Muted**: `#9CA3AF` (RGB: 156, 163, 175)

### Semantic Colors
- **Success Green**: `#10B981` (RGB: 16, 185, 129) - Normal health ranges
- **Warning Amber**: `#F59E0B` (RGB: 245, 158, 11) - Borderline values
- **Error Red**: `#EF4444` (RGB: 239, 68, 68) - Critical values
- **Info Blue**: `#3B82F6` (RGB: 59, 130, 246) - General information

## Typography

### Font Families
- **Primary Font**: System UI stack
  ```css
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, 
               "Helvetica Neue", Arial, sans-serif;
  ```
- **Monospace Font**: For code and data
  ```css
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Consolas, 
               "Liberation Mono", Menlo, monospace;
  ```

### Type Scale
- **Display**: 36px / 44px line-height / 700 weight
- **Heading 1**: 30px / 38px line-height / 600 weight
- **Heading 2**: 24px / 32px line-height / 600 weight
- **Heading 3**: 20px / 28px line-height / 600 weight
- **Heading 4**: 18px / 26px line-height / 600 weight
- **Body Large**: 16px / 24px line-height / 400 weight
- **Body**: 14px / 20px line-height / 400 weight
- **Small**: 12px / 16px line-height / 400 weight
- **Micro**: 11px / 14px line-height / 400 weight

## Spacing System
8-point grid system for consistent spacing:
- **xs**: 4px (0.25rem)
- **sm**: 8px (0.5rem)
- **md**: 16px (1rem)
- **lg**: 24px (1.5rem)
- **xl**: 32px (2rem)
- **2xl**: 48px (3rem)
- **3xl**: 64px (4rem)
- **4xl**: 80px (5rem)

## Glassmorphism Effects (CRITICAL for modern UI)
```css
/* Primary glass panel */
.glass-panel {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
}

/* Dark glass variant for contrast */
.glass-panel-dark {
  background: rgba(17, 24, 39, 0.75);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
}

/* Colored glass for specialist cards */
.glass-panel-colored {
  background: rgba(var(--specialist-color-rgb), 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(var(--specialist-color-rgb), 0.2);
  box-shadow: 0 4px 24px 0 rgba(var(--specialist-color-rgb), 0.15);
}
```

## Gradient Backgrounds
```css
/* Primary gradient - health theme */
.gradient-primary {
  background: linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%);
}

/* Health vitality gradient */
.gradient-health {
  background: linear-gradient(135deg, #10B981 0%, #06B6D4 100%);
}

/* Soft background gradient */
.gradient-soft {
  background: linear-gradient(180deg, #FFFFFF 0%, #F3F4F6 100%);
}

/* Specialist gradient overlays */
.gradient-cardiology {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%);
}
```

## Elevation & Shadows
```css
/* Shadow levels for depth hierarchy */
.shadow-xs {
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.shadow-sm {
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.shadow-md {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.shadow-lg {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.shadow-xl {
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

/* Colored shadows for specialists */
.shadow-colored {
  box-shadow: 0 4px 14px 0 rgba(var(--specialist-color-rgb), 0.25);
}
```

## Border Radius
- **Sharp**: 0px - Never used in this system
- **Subtle**: 4px - Small UI elements
- **Default**: 8px - Buttons, inputs, small cards
- **Medium**: 12px - Cards, panels
- **Large**: 16px - Large cards, modals
- **XL**: 24px - Feature cards
- **Full**: 9999px - Pills, avatars

## Animation Principles
### Timing Functions
```css
/* Standard easing */
.ease-standard {
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}

/* Decelerate - for enter animations */
.ease-out {
  transition-timing-function: cubic-bezier(0, 0, 0.2, 1);
}

/* Accelerate - for exit animations */
.ease-in {
  transition-timing-function: cubic-bezier(0.4, 0, 1, 1);
}

/* Spring effect - for delightful interactions */
.ease-spring {
  transition-timing-function: cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

### Duration Values
- **Instant**: 75ms - Hover states
- **Fast**: 150ms - Small transitions
- **Normal**: 300ms - Most UI transitions
- **Slow**: 500ms - Complex animations
- **Deliberate**: 700ms - Page transitions

## Medical UI Patterns

### Agent Status States
```css
/* Waiting state */
.agent-waiting {
  opacity: 0.5;
  filter: grayscale(50%);
}

/* Active/Thinking state */
.agent-active {
  animation: pulse-thinking 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Complete state */
.agent-complete {
  position: relative;
}

.agent-complete::after {
  content: '✓';
  position: absolute;
  bottom: -4px;
  right: -4px;
  width: 20px;
  height: 20px;
  background: #10B981;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}
```

### Progress Indicators
```css
/* Linear progress bar */
.progress-bar {
  height: 4px;
  background: #E5E7EB;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--specialist-color) 0%, var(--specialist-color-light) 100%);
  border-radius: 2px;
  transition: width 300ms ease-out;
}

/* Circular progress for agents */
.progress-circle {
  stroke-dasharray: 283;
  stroke-dashoffset: calc(283 - (283 * var(--progress)) / 100);
  transition: stroke-dashoffset 300ms ease-out;
}
```

## Health Data Visualization Patterns

### Chart Color Sequences
```javascript
// Primary sequence for multi-series data
const chartColors = [
  '#3B82F6', // Primary blue
  '#10B981', // Success green
  '#F59E0B', // Warning amber
  '#8B5CF6', // Purple
  '#06B6D4', // Cyan
  '#EF4444', // Error red
  '#84CC16', // Lime
  '#FB923C'  // Orange
];

// Health status colors
const healthStatusColors = {
  normal: '#10B981',
  borderline: '#F59E0B',
  abnormal: '#EF4444',
  critical: '#7C3AED'
};
```

### Reference Range Visualization
```css
/* Shaded reference range on charts */
.reference-range {
  fill: rgba(16, 185, 129, 0.1);
  stroke: rgba(16, 185, 129, 0.3);
  stroke-width: 1;
  stroke-dasharray: 4 2;
}

/* Out of range indicator */
.out-of-range {
  fill: rgba(239, 68, 68, 0.1);
  stroke: rgba(239, 68, 68, 0.3);
}
```

## Component Tokens

### Button Variations
```css
/* Primary button */
.btn-primary {
  background: #3B82F6;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 150ms ease-out;
}

.btn-primary:hover {
  background: #2563EB;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

/* Glass button */
.btn-glass {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(229, 231, 235, 0.5);
  color: #111827;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
}
```

### Card Styles
```css
/* Standard card */
.card {
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Glass card */
.card-glass {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
}

/* Specialist card */
.card-specialist {
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid var(--specialist-color);
  border-radius: 12px;
  padding: 16px;
  position: relative;
  transition: all 300ms ease-out;
}
```

## Responsive Breakpoints
- **Mobile**: 320px - 767px
- **Tablet**: 768px - 1023px
- **Desktop**: 1024px - 1439px
- **Wide**: 1440px+

## CSS Custom Properties
```css
:root {
  /* Colors */
  --color-primary: #3B82F6;
  --color-background: #FFFFFF;
  --color-surface: #F9FAFB;
  --color-border: #E5E7EB;
  --color-text-primary: #111827;
  --color-text-secondary: #6B7280;
  
  /* Specialist colors */
  --color-cardiology: #EF4444;
  --color-laboratory: #10B981;
  --color-endocrinology: #8B5CF6;
  --color-data-analysis: #F59E0B;
  --color-preventive: #F97316;
  --color-pharmacy: #FB923C;
  --color-nutrition: #84CC16;
  --color-general-practice: #06B6D4;
  
  /* Spacing */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
  
  /* Border radius */
  --radius-sm: 4px;
  --radius-default: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  
  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  
  /* Animation */
  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;
  --easing-standard: cubic-bezier(0.4, 0, 0.2, 1);
}
```