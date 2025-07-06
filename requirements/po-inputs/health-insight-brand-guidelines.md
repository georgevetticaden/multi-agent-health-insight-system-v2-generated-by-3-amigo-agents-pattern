# Health Insight Assistant Brand Guidelines

## Brand Overview

The Health Insight Assistant represents the intersection of advanced AI technology and compassionate healthcare. Our brand embodies trust, expertise, and accessibility—making complex health analysis feel approachable and actionable.

### Brand Values
- **Trustworthy**: Medical-grade accuracy with transparent processes
- **Intelligent**: Powered by cutting-edge AI orchestration
- **Accessible**: Complex insights made simple
- **Professional**: Clinical expertise with a human touch
- **Responsive**: Real-time analysis and adaptive interactions

## Visual Identity

### Logo & Identity
- **Primary Logo**: Blue medical briefcase icon with stethoscope element
- **Application Name**: "Health Insight Assistant"
- **Tagline**: "Powered by Multi-Agent AI • Snowflake Cortex"
- **Logo Usage**: Always maintain clear space equal to the height of the icon

### Color Palette

#### Primary Colors
- **Primary Blue**: `#3B82F6` (RGB: 59, 130, 246)
  - Used for: Primary buttons, logo, active states, links
  - Represents: Trust, stability, medical professionalism

- **Pure White**: `#FFFFFF` (RGB: 255, 255, 255)
  - Used for: Primary backgrounds, cards
  - Represents: Cleanliness, clarity

#### Medical Specialist Colors
Each specialist has a unique color for instant recognition:

- **Cardiology Red**: `#EF4444` (RGB: 239, 68, 68) - Heart health
- **Laboratory Green**: `#10B981` (RGB: 16, 185, 129) - Test results
- **Endocrinology Purple**: `#8B5CF6` (RGB: 139, 92, 246) - Hormones
- **Data Analysis Yellow**: `#F59E0B` (RGB: 245, 158, 11) - Analytics
- **Preventive Orange**: `#F97316` (RGB: 249, 115, 22) - Prevention
- **Pharmacy Orange**: `#FB923C` (RGB: 251, 146, 60) - Medications
- **Nutrition Lime**: `#84CC16` (RGB: 132, 204, 22) - Diet
- **General Practice Blue**: `#06B6D4` (RGB: 6, 182, 212) - Overall care

#### Neutral Colors
- **Background Gray**: `#F9FAFB` (RGB: 249, 250, 251)
- **Border Gray**: `#E5E7EB` (RGB: 229, 231, 235)
- **Text Primary**: `#111827` (RGB: 17, 24, 39)
- **Text Secondary**: `#6B7280` (RGB: 107, 114, 128)
- **Text Muted**: `#9CA3AF` (RGB: 156, 163, 175)

#### Semantic Colors
- **Success Green**: `#10B981` (RGB: 16, 185, 129)
- **Warning Amber**: `#F59E0B` (RGB: 245, 158, 11)
- **Error Red**: `#EF4444` (RGB: 239, 68, 68)
- **Info Blue**: `#3B82F6` (RGB: 59, 130, 246)

### Typography

#### Font Family
- **Primary Font**: System UI stack for optimal performance
  ```css
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, 
               "Helvetica Neue", Arial, sans-serif;
  ```

#### Type Scale
- **Heading 1**: 24px / 32px line-height / 600 weight
- **Heading 2**: 20px / 28px line-height / 600 weight
- **Heading 3**: 18px / 24px line-height / 600 weight
- **Body Large**: 16px / 24px line-height / 400 weight
- **Body**: 14px / 20px line-height / 400 weight
- **Small**: 12px / 16px line-height / 400 weight
- **Micro**: 11px / 14px line-height / 400 weight

### Spacing System
8-point grid system for consistent spacing:
- **xs**: 4px
- **sm**: 8px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **2xl**: 48px
- **3xl**: 64px

### UI Components

#### Buttons
- **Primary Button**: 
  - Background: Primary Blue
  - Text: White
  - Padding: 12px 24px
  - Border radius: 8px
  - Hover: 10% darker

- **Secondary Button**:
  - Background: White
  - Border: 1px solid Border Gray
  - Text: Text Primary
  - Same dimensions as primary

#### Cards
- Background: White
- Border: 1px solid Border Gray
- Border radius: 12px
- Padding: 16px or 24px
- Shadow: `0 1px 3px rgba(0, 0, 0, 0.1)`

#### Medical Team Cards
- Specialist icon: 48px circle with colored background
- Status indicator: 8px dot (green/orange/gray)
- Progress bar: 4px height with rounded ends

#### Input Fields
- Height: 40px
- Border: 1px solid Border Gray
- Border radius: 8px
- Focus: Primary Blue border
- Padding: 0 16px

### Icons & Imagery

#### Icon Style
- Line icons with 2px stroke weight
- Consistent 24px base size
- Medical-appropriate iconography
- Rounded line caps and joins

#### Medical Specialist Icons
Each specialist has a unique icon:
- Heart for Cardiology
- Microscope for Laboratory
- Pills for Endocrinology
- Chart for Data Analysis
- Shield for Preventive
- Syringe for Pharmacy
- Apple for Nutrition
- Stethoscope for General Practice

### Motion & Animation

#### Timing
- **Fast**: 150ms - Hover states, small transitions
- **Normal**: 300ms - Most UI transitions
- **Slow**: 500ms - Page transitions, complex animations

#### Easing
- Use `ease-out` for enter animations
- Use `ease-in-out` for state changes
- CSS: `cubic-bezier(0.4, 0, 0.2, 1)`

#### Loading States
- Specialist cards: Pulse animation on colored background
- Progress bars: Smooth fill from left to right
- Skeleton screens for content loading

### Layout Principles

#### 3-Panel Layout
- **Left Panel** (Sidebar): 280px fixed width
- **Center Panel** (Chat): Flexible, min 600px
- **Right Panel** (Context): 400px flexible

#### Responsive Breakpoints
- **Mobile**: < 768px (stack panels)
- **Tablet**: 768px - 1024px (hide sidebar)
- **Desktop**: > 1024px (full 3-panel)

### Voice & Tone

#### Professional yet Approachable
- Use medical terminology with lay explanations
- Confident but not authoritative
- Empathetic and supportive
- Clear and concise

#### UI Copy Guidelines
- Action buttons: Verb + Noun ("New Health Conversation")
- Status messages: Present progressive ("Dr. Heart is analyzing...")
- Completions: Past tense with metric ("Analysis complete with 85% confidence")
- Errors: Helpful and actionable

### Accessibility

#### Color Contrast
- All text meets WCAG AA standards (4.5:1 minimum)
- Interactive elements: 3:1 minimum
- Never rely on color alone for meaning

#### Interactive Elements
- Focus indicators: 2px Primary Blue outline
- Minimum touch target: 44x44px
- Keyboard navigation support
- Screen reader labels for all icons

### Implementation Notes

#### CSS Variables
```css
:root {
  --color-primary: #3B82F6;
  --color-background: #FFFFFF;
  --color-surface: #F9FAFB;
  --color-border: #E5E7EB;
  --radius-sm: 8px;
  --radius-md: 12px;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

#### Component Classes
- Use semantic naming: `.health-card`, `.specialist-status`
- Maintain consistency with design system
- Implement dark mode variables for future use

### Brand Applications

#### Marketing Materials
- Always include the multi-agent diagram
- Emphasize the medical team concept
- Show real-time analysis capabilities
- Include trust indicators (security, compliance)

#### Product Screenshots
- Always show populated states
- Include diverse health scenarios
- Highlight the specialist collaboration
- Show successful outcomes

---

*These guidelines ensure the Health Insight Assistant maintains a consistent, professional, and trustworthy presence across all touchpoints while making advanced AI health analysis accessible to everyone.*