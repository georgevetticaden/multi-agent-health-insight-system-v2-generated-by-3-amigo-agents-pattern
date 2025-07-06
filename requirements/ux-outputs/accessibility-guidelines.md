# Accessibility Guidelines

## Overview

The Health Insight Assistant is designed to be accessible to all users, including those with disabilities. We follow WCAG 2.1 AA standards as a minimum, with AAA compliance where possible. Given the medical nature of the application, accessibility is not just a legal requirement but a moral imperative to ensure health insights are available to everyone.

## Core Principles

1. **Perceivable**: Information must be presentable in ways users can perceive
2. **Operable**: Interface components must be operable by all users
3. **Understandable**: Information and UI operation must be understandable
4. **Robust**: Content must be robust enough for various assistive technologies

## Color & Contrast

### Contrast Requirements

#### Text Contrast
- **Normal text**: 4.5:1 minimum against background
- **Large text** (18pt+ or 14pt+ bold): 3:1 minimum
- **Medical values**: 7:1 for critical health data

```css
/* Contrast-compliant color combinations */
.text-primary { color: #111827; }     /* On white: 19.97:1 ✓ */
.text-secondary { color: #6B7280; }   /* On white: 5.31:1 ✓ */
.text-on-blue { color: #FFFFFF; }     /* On #3B82F6: 6.42:1 ✓ */
.text-on-red { color: #FFFFFF; }      /* On #EF4444: 4.54:1 ✓ */

/* High contrast mode overrides */
@media (prefers-contrast: high) {
  .text-secondary { color: #374151; }  /* Darker gray */
  .border { border-width: 2px; }       /* Thicker borders */
}
```

### Color Usage Guidelines

#### Never Rely on Color Alone
```jsx
// Bad: Color only
<div className="text-red-600">Critical value</div>

// Good: Color + Icon + Text
<div className="text-red-600 flex items-center">
  <ExclamationTriangle className="w-4 h-4 mr-1" />
  <span>Critical value</span>
  <span className="sr-only">Warning: This value requires immediate attention</span>
</div>
```

#### Health Status Indicators
```jsx
const HealthStatus = ({ value, range }) => {
  const status = getStatus(value, range);
  
  return (
    <div className="flex items-center space-x-2">
      {/* Visual indicator */}
      <div className={`w-3 h-3 rounded-full ${getStatusColor(status)}`} />
      
      {/* Text label */}
      <span className="text-sm font-medium">
        {status === 'normal' && 'Normal'}
        {status === 'warning' && 'Borderline'}
        {status === 'critical' && 'Critical'}
      </span>
      
      {/* Icon for clarity */}
      {status === 'critical' && <AlertCircle className="w-4 h-4" />}
      
      {/* Screen reader context */}
      <span className="sr-only">
        Your value of {value} is {status} compared to the normal range of {range.min}-{range.max}
      </span>
    </div>
  );
};
```

### Medical Specialist Color Accessibility
Each specialist has a unique color, but identification doesn't rely solely on color:

```jsx
const SpecialistCard = ({ specialist }) => (
  <div className="specialist-card">
    {/* Icon provides visual distinction beyond color */}
    <div className={`icon-container bg-${specialist.color}-100`}>
      <span className="text-2xl" role="img" aria-label={specialist.name}>
        {specialist.emoji}
      </span>
    </div>
    
    {/* Text labels are always present */}
    <h3 className="font-medium">{specialist.name}</h3>
    <p className="text-sm text-gray-600">{specialist.specialty}</p>
    
    {/* Status uses multiple indicators */}
    <div className="status-indicator">
      {specialist.status === 'active' && (
        <>
          <div className="animate-pulse w-2 h-2 bg-blue-500 rounded-full" />
          <span className="ml-2 text-sm">Analyzing...</span>
        </>
      )}
    </div>
  </div>
);
```

## Keyboard Navigation

### Navigation Order
1. Skip links (hidden until focused)
2. Header navigation
3. Sidebar (if visible)
4. Main content
5. Context panel

### Skip Links Implementation
```html
<a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded">
  Skip to main content
</a>
<a href="#medical-team" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-40 bg-blue-600 text-white px-4 py-2 rounded">
  Skip to medical team
</a>
```

### Focus Management

#### Visible Focus Indicators
```css
/* Custom focus styles that meet WCAG requirements */
*:focus {
  outline: none;
}

*:focus-visible {
  outline: 2px solid #3B82F6;
  outline-offset: 2px;
  border-radius: 4px;
}

/* High contrast mode */
@media (prefers-contrast: high) {
  *:focus-visible {
    outline: 3px solid currentColor;
    outline-offset: 3px;
  }
}
```

#### Focus Trapping for Modals
```jsx
const Modal = ({ isOpen, onClose, children }) => {
  const modalRef = useRef();
  
  useEffect(() => {
    if (isOpen) {
      // Save previous focus
      const previousFocus = document.activeElement;
      
      // Focus first focusable element
      const focusable = modalRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      focusable[0]?.focus();
      
      // Restore focus on close
      return () => previousFocus?.focus();
    }
  }, [isOpen]);
  
  const handleKeyDown = (e) => {
    if (e.key === 'Escape') onClose();
    // Tab trapping logic...
  };
  
  return (
    <div ref={modalRef} onKeyDown={handleKeyDown} role="dialog" aria-modal="true">
      {children}
    </div>
  );
};
```

### Keyboard Shortcuts

#### Global Shortcuts
```javascript
const keyboardShortcuts = {
  'Ctrl+/': 'Show keyboard shortcuts',
  'Ctrl+K': 'Quick search',
  'Ctrl+N': 'New conversation',
  'Ctrl+B': 'Toggle sidebar',
  'Alt+M': 'Focus medical team panel',
  'Alt+V': 'Focus visualization panel',
  'Escape': 'Close current panel/modal'
};
```

#### Implementation
```jsx
useEffect(() => {
  const handleKeyboard = (e) => {
    // Ctrl+K for search
    if (e.ctrlKey && e.key === 'k') {
      e.preventDefault();
      focusSearch();
    }
    
    // Alt+M for medical team
    if (e.altKey && e.key === 'm') {
      e.preventDefault();
      focusMedicalTeam();
    }
  };
  
  document.addEventListener('keydown', handleKeyboard);
  return () => document.removeEventListener('keydown', handleKeyboard);
}, []);
```

## Screen Reader Support

### Semantic HTML Structure
```html
<main role="main" aria-label="Health conversation">
  <section aria-label="Chat messages">
    <h2 className="sr-only">Conversation History</h2>
    <!-- Messages -->
  </section>
  
  <aside aria-label="Medical team status">
    <h2>Medical Team</h2>
    <!-- Team visualization -->
  </aside>
</main>
```

### ARIA Labels & Descriptions

#### Interactive Elements
```jsx
{/* Button with clear purpose */}
<button 
  aria-label="Start new health conversation"
  aria-keyshortcuts="Control+N"
>
  <Plus className="w-4 h-4" />
  <span>New Conversation</span>
</button>

{/* Complex interactive element */}
<div 
  role="button"
  tabIndex={0}
  aria-label={`${specialist.name}, ${specialist.specialty} specialist, currently ${specialist.status}`}
  aria-describedby={`specialist-${specialist.id}-description`}
  onClick={handleSpecialistClick}
  onKeyPress={(e) => e.key === 'Enter' && handleSpecialistClick()}
>
  {/* Specialist card content */}
</div>
<div id={`specialist-${specialist.id}-description`} className="sr-only">
  {specialist.status === 'active' 
    ? `${specialist.name} is currently analyzing your health data. Progress: ${specialist.progress}%`
    : `${specialist.name} has completed analysis with ${specialist.confidence}% confidence`
  }
</div>
```

### Live Regions for Updates

#### Agent Status Updates
```jsx
{/* Announce status changes */}
<div 
  role="status" 
  aria-live="polite" 
  aria-atomic="true"
  className="sr-only"
>
  {latestUpdate && `${latestUpdate.agent} is now ${latestUpdate.status}`}
</div>

{/* Critical alerts */}
<div 
  role="alert" 
  aria-live="assertive"
  className="sr-only"
>
  {criticalAlert && criticalAlert.message}
</div>
```

#### Progress Announcements
```jsx
const ProgressAnnouncer = ({ specialists }) => {
  const [announcement, setAnnouncement] = useState('');
  
  useEffect(() => {
    // Announce significant progress milestones
    specialists.forEach(specialist => {
      if (specialist.progress === 25 || 
          specialist.progress === 50 || 
          specialist.progress === 75 || 
          specialist.progress === 100) {
        setAnnouncement(
          `${specialist.name} analysis is ${specialist.progress}% complete`
        );
      }
    });
  }, [specialists]);
  
  return (
    <div role="status" aria-live="polite" className="sr-only">
      {announcement}
    </div>
  );
};
```

### Data Tables as Alternatives

#### Chart Alternative
```jsx
const ChartWithTable = ({ data, type }) => (
  <>
    {/* Visual chart */}
    <div aria-hidden="true">
      <LineChart data={data} />
    </div>
    
    {/* Accessible data table */}
    <table className="sr-only" role="table" aria-label={`${type} data in table format`}>
      <caption>
        {type} data from {data[0].date} to {data[data.length - 1].date}
      </caption>
      <thead>
        <tr>
          <th scope="col">Date</th>
          <th scope="col">Value</th>
          <th scope="col">Unit</th>
          <th scope="col">Status</th>
        </tr>
      </thead>
      <tbody>
        {data.map((row, i) => (
          <tr key={i}>
            <th scope="row">{row.date}</th>
            <td>{row.value}</td>
            <td>{row.unit}</td>
            <td>{row.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </>
);
```

## Motion & Animation

### Respecting User Preferences

```css
/* Reduce motion for users who prefer it */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  
  /* Keep essential animations but make them instant */
  .animate-pulse {
    animation: none;
    opacity: 0.8;
  }
  
  .thinking-dots::after {
    content: '...' !important;
    animation: none;
  }
}
```

### Safe Animation Patterns
```jsx
const SafeAnimation = ({ children, type = 'fade' }) => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  
  if (prefersReducedMotion) {
    return <div className="transition-none">{children}</div>;
  }
  
  const animations = {
    fade: 'animate-fadeIn',
    slide: 'animate-slideUp',
    pulse: 'animate-pulse'
  };
  
  return (
    <div className={animations[type]}>
      {children}
    </div>
  );
};
```

### Pause Controls for Continuous Animations
```jsx
const AnimatedSpecialist = ({ specialist }) => {
  const [isPaused, setIsPaused] = useState(false);
  
  return (
    <div className="relative">
      <div className={isPaused ? '' : 'animate-pulse'}>
        {/* Specialist content */}
      </div>
      
      <button
        onClick={() => setIsPaused(!isPaused)}
        aria-label={isPaused ? 'Resume animation' : 'Pause animation'}
        className="absolute top-0 right-0 p-1"
      >
        {isPaused ? <Play size={16} /> : <Pause size={16} />}
      </button>
    </div>
  );
};
```

## Form Accessibility

### Label Association
```jsx
{/* Visible labels */}
<div className="form-group">
  <label htmlFor="health-query" className="block text-sm font-medium mb-1">
    What health question can we help you with today?
  </label>
  <textarea
    id="health-query"
    name="query"
    aria-describedby="query-help query-error"
    aria-invalid={hasError}
    aria-required="true"
    maxLength={500}
  />
  <p id="query-help" className="text-sm text-gray-600 mt-1">
    Ask about labs, medications, or health trends
  </p>
  {hasError && (
    <p id="query-error" role="alert" className="text-sm text-red-600 mt-1">
      Please enter a health question
    </p>
  )}
</div>

{/* Screen reader only labels */}
<button aria-label="Submit health question">
  <Send className="w-5 h-5" />
</button>
```

### Error Handling
```jsx
const FormError = ({ error, inputId }) => (
  <div
    id={`${inputId}-error`}
    role="alert"
    aria-live="assertive"
    className="mt-2 text-sm text-red-600 flex items-center"
  >
    <AlertCircle className="w-4 h-4 mr-1" />
    <span>{error}</span>
  </div>
);
```

### Required Fields
```jsx
<form>
  <fieldset>
    <legend className="text-lg font-medium mb-4">
      Health Query Information
      <span className="text-sm font-normal text-gray-600 ml-2">
        * indicates required field
      </span>
    </legend>
    
    <div className="space-y-4">
      <div>
        <label htmlFor="query" className="block text-sm font-medium">
          Your Question <span aria-label="required" className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="query"
          required
          aria-required="true"
        />
      </div>
    </div>
  </fieldset>
</form>
```

## Touch Target Accessibility

### Minimum Sizes
```css
/* Ensure all interactive elements meet minimum size */
button, a, [role="button"] {
  min-width: 44px;
  min-height: 44px;
  padding: 12px;
}

/* Exception for inline text links */
a:not(.button) {
  min-height: auto;
  padding: 4px 0;
}

/* Touch-friendly spacing */
.touch-list > * + * {
  margin-top: 8px; /* Minimum spacing between targets */
}
```

## Cognitive Accessibility

### Clear Language
- Use simple, clear language for medical terms
- Provide glossary/tooltips for complex terms
- Break complex information into steps
- Use consistent terminology

### Progressive Disclosure
```jsx
const MedicalTermTooltip = ({ term, definition, children }) => (
  <span className="relative inline-block">
    <button
      className="underline decoration-dotted cursor-help"
      aria-label={`Definition of ${term}`}
      aria-describedby={`def-${term}`}
    >
      {children}
    </button>
    <span
      id={`def-${term}`}
      className="absolute bottom-full left-0 w-64 p-2 bg-gray-900 text-white text-sm rounded hidden hover:block"
    >
      {definition}
    </span>
  </span>
);
```

### Consistent Navigation
- Keep navigation in same location
- Use consistent icons and labels
- Provide breadcrumbs for context
- Clear indication of current location

## Testing Checklist

### Automated Testing
- [ ] axe-core validation passes
- [ ] WAVE tool shows no errors
- [ ] Lighthouse accessibility score > 95
- [ ] Color contrast validation passes

### Manual Testing
- [ ] Full keyboard navigation works
- [ ] Screen reader testing (NVDA/JAWS/VoiceOver)
- [ ] 200% zoom doesn't break layout
- [ ] Works without JavaScript
- [ ] Forms are accessible
- [ ] Error messages are clear

### User Testing
- [ ] Test with users who use assistive technology
- [ ] Test with users with various disabilities
- [ ] Gather feedback on medical term clarity
- [ ] Validate emergency alert effectiveness

## Resources & Tools

### Development Tools
- axe DevTools
- WAVE Browser Extension
- Stark (Figma/Sketch plugin)
- Screen readers for testing

### References
- WCAG 2.1 Guidelines
- ARIA Authoring Practices Guide
- WebAIM Resources
- A11y Project Checklist

By following these guidelines, the Health Insight Assistant ensures that all users, regardless of ability, can access and understand their health insights effectively and independently.