# Health Insight System UI Customization Guide

## Overview
This document provides health-specific customization guidance for the UX Designer Agent when creating the Multi-Agent Health Insight System interface.

## Domain-Specific Color Palette

### Medical Specialist Colors
Each medical specialist should have a unique color for instant recognition:
- **Cardiology (Dr. Heart)**: `#EF4444` - Heart health (red)
- **Laboratory (Dr. Lab)**: `#10B981` - Test results (green)
- **Endocrinology (Dr. Hormone)**: `#8B5CF6` - Hormones (purple)
- **Data Analysis (Dr. Analytics)**: `#F59E0B` - Analytics (amber)
- **Preventive (Dr. Prevention)**: `#F97316` - Prevention (orange)
- **Pharmacy (Dr. Pharma)**: `#FB923C` - Medications (light orange)
- **Nutrition (Dr. Nutrition)**: `#84CC16` - Diet (lime)
- **General Practice (Dr. Vitality/CMO)**: `#06B6D4` - Overall care (cyan)

### Health-Specific Semantic Colors
- Normal Range: `#10B981` (green) - Healthy values
- Borderline: `#F59E0B` (amber) - Attention needed
- Critical: `#EF4444` (red) - Immediate attention
- Improving: `#3B82F6` (blue) - Positive trends

## Medical Team Visualization

### CMO (Chief Medical Officer) Positioning
- Center position with 80px circle
- Title: "Dr. Vitality - CMO"
- Larger size indicates orchestrator role

### Specialist Layout
- Arranged in arc around CMO
- 60px circles for each specialist
- Connected to CMO with animated lines when active
- Specialty icon + name displayed

### Status States
- **Waiting**: Gray border, 0.5 opacity
- **Thinking**: Pulsing animation (2s cycle)
- **Active**: Solid color, animated border
- **Complete**: Check mark overlay, full opacity

## Health Data Visualizations

### Time Series for Lab Results
- Show reference ranges as shaded areas
- Highlight values outside normal range
- Use color coding (green/amber/red)
- Include trend indicators

### Medication Timeline
- Visual timeline showing medication changes
- Correlation with lab results
- Dosage adjustments highlighted

### Vital Signs Dashboard
- Blood pressure gauge
- Heart rate monitor style
- Temperature indicator
- Weight trend chart

## Medical Icons and Imagery

### Specialist Icons
```
Cardiology: 🫀 or heart icon
Laboratory: 🧪 or test tube icon
Endocrinology: 🧬 or hormone icon
Data Analysis: 📊 or chart icon
Preventive: 🛡️ or shield icon
Pharmacy: 💊 or pill icon
Nutrition: 🥗 or food icon
General Practice: 👨‍⚕️ or stethoscope icon
```

### Medical Patterns
- Subtle medical cross pattern for backgrounds
- DNA helix for loading animations
- Heartbeat line for progress indicators

## Health-Specific UI Components

### Lab Result Card
```html
<div class="lab-result-card">
  <div class="result-header">
    <span class="test-name">Cholesterol</span>
    <span class="result-value critical">245 mg/dL</span>
  </div>
  <div class="reference-range">
    <span>Normal: &lt; 200 mg/dL</span>
  </div>
  <div class="trend-indicator">
    <span class="trend up">↑ 15% from last test</span>
  </div>
</div>
```

### Medication Card
```html
<div class="medication-card">
  <div class="med-header">
    <span class="med-icon">💊</span>
    <span class="med-name">Metformin</span>
  </div>
  <div class="med-details">
    <span class="dosage">500mg twice daily</span>
    <span class="duration">Started 3 months ago</span>
  </div>
</div>
```

## Health Query Examples

### Simple Queries (1 specialist)
- "What's my latest cholesterol level?"
- "Show my blood pressure trends"

### Standard Queries (2-3 specialists)
- "How are my diabetes markers?"
- "Analyze my heart health"

### Complex Queries (4-6 specialists)
- "Give me a complete health overview"
- "How do my medications affect my lab results?"

## Trust-Building Elements

### Medical Credibility
- Display specialist "credentials" (e.g., "Board Certified in Cardiology")
- Show confidence levels for insights
- Include medical disclaimers appropriately

### Transparency Features
- Show which data sources were analyzed
- Display reasoning process
- Highlight areas needing physician review

## Accessibility Considerations

### Health-Specific Needs
- High contrast for vision-impaired users
- Clear labeling of critical values
- Audio alerts for critical findings
- Printable reports for physician visits

### Medical Terminology
- Tooltips for medical terms
- Plain language explanations
- Expandable detail sections

## Animation Guidelines

### Health-Appropriate Animations
- Heartbeat pulse for cardiology analysis
- Flowing particles for blood/circulation
- Gentle waves for breathing/respiratory
- DNA helix rotation for genetic factors

### Loading States
- Use medical-themed animations
- Show which specialists are being consulted
- Progress indicators with health metaphors

## Voice and Tone

### Medical Professional
- Authoritative but approachable
- Clear and precise language
- Empathetic to health concerns
- Educational without condescension

### Example Copy
- "Dr. Heart is analyzing your cardiovascular health..."
- "Your medical team has identified 3 key insights"
- "Based on 15 years of health data"

## Mobile Considerations

### Health on the Go
- Quick access to critical values
- Emergency contact integration
- Offline access to recent results
- Large touch targets for accessibility

This customization guide should be provided to the UX Designer Agent along with the generic multi-agent requirements to create a health-specific interface while maintaining the flexibility of the core agent system.