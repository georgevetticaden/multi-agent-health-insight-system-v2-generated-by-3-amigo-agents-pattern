# Animation Specifications

## Overview

Animations in the Health Insight Assistant serve to enhance user understanding of the multi-agent system's real-time processes, provide feedback, and create a smooth, professional experience. All animations are purposeful, performant, and respect user preferences for reduced motion.

## Animation Principles

1. **Purposeful**: Every animation has a clear function
2. **Subtle**: Enhance without overwhelming
3. **Consistent**: Same easing and timing patterns
4. **Performant**: GPU-accelerated, no layout thrashing
5. **Accessible**: Respect prefers-reduced-motion

## Core Animation Values

### Timing
```css
:root {
  --duration-instant: 75ms;
  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;
  --duration-deliberate: 700ms;
  --duration-orchestration: 1000ms;
}
```

### Easing Functions
```css
:root {
  /* Standard easing - most UI transitions */
  --ease-standard: cubic-bezier(0.4, 0, 0.2, 1);
  
  /* Decelerate - enter animations */
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  
  /* Accelerate - exit animations */
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  
  /* Spring - delightful interactions */
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  
  /* Medical pulse - thinking states */
  --ease-pulse: cubic-bezier(0.4, 0, 0.6, 1);
}
```

## Loading States

### Specialist Thinking Animation
The signature animation showing specialists are processing:

```css
@keyframes thinking-pulse {
  0%, 100% { 
    opacity: 1; 
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(var(--specialist-color-rgb), 0.4);
  }
  50% { 
    opacity: 0.8; 
    transform: scale(1.05);
    box-shadow: 0 0 0 10px rgba(var(--specialist-color-rgb), 0);
  }
}

.specialist-thinking {
  animation: thinking-pulse 2s var(--ease-pulse) infinite;
}

/* Color-specific versions */
.specialist-thinking.cardiology {
  --specialist-color-rgb: 239, 68, 68;
}

.specialist-thinking.laboratory {
  --specialist-color-rgb: 16, 185, 129;
}
```

### Dots Loading Indicator
For inline loading states:

```css
@keyframes dot-pulse {
  0%, 60%, 100% { 
    opacity: 0.4;
    transform: scale(1);
  }
  30% { 
    opacity: 1;
    transform: scale(1.2);
  }
}

.loading-dots {
  display: inline-flex;
  gap: 4px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  animation: dot-pulse 1.4s var(--ease-standard) infinite;
}

.loading-dots span:nth-child(1) { animation-delay: 0s; }
.loading-dots span:nth-child(2) { animation-delay: 0.15s; }
.loading-dots span:nth-child(3) { animation-delay: 0.3s; }
```

### Skeleton Loading
For content placeholders:

```css
@keyframes skeleton-pulse {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.skeleton {
  background: linear-gradient(
    90deg,
    #F3F4F6 25%,
    #E5E7EB 50%,
    #F3F4F6 75%
  );
  background-size: 200% 100%;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}
```

## Transitions

### Panel Switching
Smooth transitions between panels:

```css
/* Slide animations for panels */
@keyframes slideInRight {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

@keyframes slideOutRight {
  from { transform: translateX(0); opacity: 1; }
  to { transform: translateX(100%); opacity: 0; }
}

.panel-enter {
  animation: slideInRight var(--duration-normal) var(--ease-out);
}

.panel-exit {
  animation: slideOutRight var(--duration-normal) var(--ease-in);
}
```

### Message Appearance
New messages slide up:

```css
@keyframes slideUp {
  from { 
    opacity: 0; 
    transform: translateY(20px);
  }
  to { 
    opacity: 1; 
    transform: translateY(0);
  }
}

.message-appear {
  animation: slideUp var(--duration-normal) var(--ease-out);
  animation-fill-mode: both;
}
```

### Tool Call Expansion
Smooth expand/collapse:

```css
.tool-call-content {
  max-height: 0;
  overflow: hidden;
  transition: max-height var(--duration-normal) var(--ease-standard);
}

.tool-call-content.expanded {
  max-height: 500px; /* Adjust based on content */
}

/* Chevron rotation */
.tool-call-chevron {
  transition: transform var(--duration-fast) var(--ease-standard);
}

.tool-call-chevron.expanded {
  transform: rotate(180deg);
}
```

### Medical Team Connections
Animated lines between CMO and specialists:

```css
@keyframes drawLine {
  from { 
    stroke-dashoffset: 100;
    opacity: 0;
  }
  to { 
    stroke-dashoffset: 0;
    opacity: 1;
  }
}

.connection-line {
  stroke-dasharray: 100;
  stroke-dashoffset: 100;
  opacity: 0;
}

.connection-line.active {
  animation: drawLine var(--duration-slow) var(--ease-out) forwards;
}

/* Stagger the animations */
.connection-line:nth-child(1) { animation-delay: 0ms; }
.connection-line:nth-child(2) { animation-delay: 100ms; }
.connection-line:nth-child(3) { animation-delay: 200ms; }
```

## Micro-interactions

### Button Interactions
```css
.btn {
  transition: all var(--duration-fast) var(--ease-standard);
  transform: translateY(0);
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition-duration: var(--duration-instant);
}

/* Primary button glow effect */
.btn-primary {
  position: relative;
  overflow: hidden;
}

.btn-primary::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  transition: width var(--duration-normal), height var(--duration-normal);
}

.btn-primary:active::after {
  width: 300px;
  height: 300px;
}
```

### Card Hover Effects
```css
.specialist-card {
  transition: all var(--duration-normal) var(--ease-standard);
  transform: translateY(0);
}

.specialist-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

/* Glow effect for active specialists */
.specialist-card.active {
  box-shadow: 0 0 0 3px rgba(var(--specialist-color-rgb), 0.2);
}
```

### Focus Animations
```css
*:focus {
  outline: none;
}

*:focus-visible {
  outline: 2px solid #3B82F6;
  outline-offset: 2px;
  transition: outline-offset var(--duration-fast) var(--ease-standard);
}

*:focus-visible:active {
  outline-offset: 0;
}
```

## Agent Status Changes

### State Transition Sequences

#### Idle → Thinking
```css
@keyframes activateSpecialist {
  0% { 
    opacity: 0.5;
    transform: scale(0.95);
    filter: grayscale(50%);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.02);
  }
  100% { 
    opacity: 1;
    transform: scale(1);
    filter: grayscale(0%);
  }
}

.specialist-activating {
  animation: activateSpecialist var(--duration-normal) var(--ease-out);
}
```

#### Thinking → Complete
```css
@keyframes completeAnalysis {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.specialist-completing {
  animation: completeAnalysis var(--duration-normal) var(--ease-spring);
}

/* Check mark appearance */
@keyframes checkMarkDraw {
  0% { 
    stroke-dashoffset: 30;
    opacity: 0;
  }
  100% { 
    stroke-dashoffset: 0;
    opacity: 1;
  }
}

.check-mark {
  stroke-dasharray: 30;
  animation: checkMarkDraw var(--duration-normal) var(--ease-out) 
             var(--duration-fast) forwards;
}
```

### Connection Line Animations
Dynamic connection states:

```javascript
// CSS for different connection states
const connectionStates = {
  waiting: {
    stroke: '#E5E7EB',
    strokeDasharray: '4 2',
    opacity: 0.5
  },
  active: {
    stroke: '#3B82F6',
    strokeDasharray: 'none',
    opacity: 1,
    animation: 'pulse 2s infinite'
  },
  complete: {
    stroke: '#10B981',
    strokeDasharray: 'none',
    opacity: 0.8
  }
};
```

## Progress Indicators

### Linear Progress Bar
```css
.progress-bar {
  height: 4px;
  background: #E5E7EB;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(
    90deg, 
    var(--color-primary) 0%, 
    var(--color-primary-light) 100%
  );
  border-radius: 2px;
  transition: width var(--duration-slow) var(--ease-out);
  position: relative;
}

/* Shimmer effect for active progress */
.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.4),
    transparent
  );
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
```

### Circular Progress
```css
.circular-progress {
  --progress: 0;
  --size: 60px;
  --stroke-width: 4px;
  
  width: var(--size);
  height: var(--size);
}

.circular-progress circle {
  fill: none;
  stroke-width: var(--stroke-width);
}

.circular-progress .track {
  stroke: #E5E7EB;
}

.circular-progress .fill {
  stroke: var(--color-primary);
  stroke-linecap: round;
  stroke-dasharray: calc(var(--size) * 3.14);
  stroke-dashoffset: calc(var(--size) * 3.14 * (1 - var(--progress) / 100));
  transform: rotate(-90deg);
  transform-origin: center;
  transition: stroke-dashoffset var(--duration-slow) var(--ease-out);
}
```

## Notification Animations

### Toast Notifications
```css
@keyframes slideInTop {
  from {
    transform: translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes slideOutTop {
  from {
    transform: translateY(0);
    opacity: 1;
  }
  to {
    transform: translateY(-100%);
    opacity: 0;
  }
}

.toast-enter {
  animation: slideInTop var(--duration-normal) var(--ease-out);
}

.toast-exit {
  animation: slideOutTop var(--duration-normal) var(--ease-in);
}
```

### Alert Pulse
For critical notifications:

```css
@keyframes alertPulse {
  0% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(239, 68, 68, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
  }
}

.alert-critical {
  animation: alertPulse 2s infinite;
}
```

## Orchestration Animations

### Team Assembly Sequence
```javascript
// Staggered appearance of specialists
const assembleTeam = (specialists) => {
  specialists.forEach((specialist, index) => {
    setTimeout(() => {
      specialist.element.classList.add('specialist-appear');
    }, index * 100);
  });
};
```

```css
@keyframes specialistAppear {
  0% {
    opacity: 0;
    transform: scale(0.8) translateY(20px);
  }
  50% {
    transform: scale(1.05) translateY(-5px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.specialist-appear {
  animation: specialistAppear var(--duration-normal) var(--ease-spring);
  animation-fill-mode: both;
}
```

### Data Flow Visualization
Show data moving between agents:

```css
@keyframes dataFlow {
  0% {
    offset-distance: 0%;
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    offset-distance: 100%;
    opacity: 0;
  }
}

.data-particle {
  offset-path: path('M 50 50 Q 100 25 150 50');
  animation: dataFlow 2s var(--ease-standard) infinite;
}
```

## Performance Optimization

### GPU Acceleration
```css
/* Use transform and opacity for smooth animations */
.gpu-accelerated {
  will-change: transform, opacity;
  transform: translateZ(0); /* Force GPU layer */
}

/* Remove after animation completes */
.animation-complete {
  will-change: auto;
}
```

### Reduced Motion Support
```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  
  /* Maintain functional states without motion */
  .specialist-thinking {
    opacity: 0.8;
    animation: none;
  }
  
  .loading-dots span {
    animation: none;
    opacity: 1;
  }
  
  /* Instant state changes */
  .progress-fill {
    transition: none;
  }
}
```

### Animation Frame Management
```javascript
// Throttle animations to 60fps
const animateProgress = (element, targetValue) => {
  let currentValue = 0;
  let animationId;
  
  const update = () => {
    currentValue += (targetValue - currentValue) * 0.1;
    
    if (Math.abs(targetValue - currentValue) < 0.5) {
      currentValue = targetValue;
    }
    
    element.style.setProperty('--progress', currentValue);
    
    if (currentValue !== targetValue) {
      animationId = requestAnimationFrame(update);
    }
  };
  
  update();
  
  return () => cancelAnimationFrame(animationId);
};
```

## Implementation Guidelines

### CSS Variables for Dynamic Animations
```javascript
// Set animation properties dynamically
const setSpecialistAnimation = (element, specialist) => {
  element.style.setProperty('--specialist-color', specialist.color);
  element.style.setProperty('--animation-delay', `${specialist.index * 100}ms`);
  element.style.setProperty('--pulse-intensity', specialist.urgency);
};
```

### Animation Lifecycle Management
```javascript
class AnimationController {
  constructor(element) {
    this.element = element;
    this.animations = new Set();
  }
  
  start(animationClass, duration = 300) {
    this.element.classList.add(animationClass);
    this.animations.add(animationClass);
    
    setTimeout(() => {
      this.element.classList.remove(animationClass);
      this.animations.delete(animationClass);
    }, duration);
  }
  
  cleanup() {
    this.animations.forEach(animation => {
      this.element.classList.remove(animation);
    });
    this.animations.clear();
  }
}
```

### Sequencing Complex Animations
```javascript
const orchestrateAnalysis = async () => {
  // 1. Fade in CMO
  await animate('.cmo', 'fadeIn', 300);
  
  // 2. Draw connection lines
  await animateAll('.connection-line', 'drawLine', 500, 100);
  
  // 3. Activate specialists
  await animateAll('.specialist', 'activate', 300, 150);
  
  // 4. Start progress animations
  startProgressAnimations();
};
```

These animation specifications ensure that the Health Insight Assistant provides smooth, meaningful motion that enhances understanding of the multi-agent system while maintaining excellent performance and accessibility.