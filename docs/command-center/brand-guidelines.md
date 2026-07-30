# Brand Guidelines — Lyons Command Center

**Visual Identity Standards**

---

## Table of Contents

1. [Brand Colors](#brand-colors)
2. [Typography](#typography)
3. [Logo Usage](#logo-usage)
4. [UI Components](#ui-components)
5. [Terminal Display](#terminal-display)
6. [Presentation Materials](#presentation-materials)
7. [Do Not Use](#do-not-use)

---

## Brand Colors

| Element | Value | Usage |
|---------|-------|-------|
| **Navy** | `#05060A` | Primary brand color, backgrounds, headers |
| **Gold** | `#C9A844` | Primary accent, highlights, action buttons |
| **Gold-Light** | `#E8C96A` | Secondary accent, hover states, gradients |
| **Dark Gold** | `#A8883A` | Tertiary accent, disabled states |
| **Text Primary** | `#FFFFFF` | Main text on dark backgrounds |
| **Text Secondary** | `#A0A0A0` | Secondary text, labels |
| **Text Muted** | `#606060` | Disabled/muted text |

---

## Typography

### Terminal/UI
- **Font Family:** JetBrains Mono or similar monospace
- **Size:** 14-16px base
- **Line Height:** 1.5
- **Font Weight:** Regular for body, Medium for headers

### Headers
- **Font Size:** 18-24px
- **Font Weight:** Medium to Bold
- **Color:** Gold (#C9A844) for accents, White for main headers

### Body Text
- **Font Size:** 14-16px
- **Line Height:** 1.5-1.6
- **Color:** Text Primary (#FFFFFF)

---

## Logo Usage

### Primary Logo
Use the navy-gold combination mark for all official materials.

### Clear Space
Maintain at least the height of the "L" logo around all logo usage.

### Minimum Size
- **Digital:** 24px height minimum
- **Print:** 0.5in height minimum

### Incorrect Usage
- ❌ Do not stretch or distort
- ❌ Do not change colors
- ❌ Do not rotate
- ❌ Do not place on busy backgrounds

---

## UI Components

### Buttons
```
Primary: Navy background, Gold text, Gold border
Secondary: Gold background, Navy text, Navy border
Disabled: Muted background, Muted text
```

### Cards
```
Background: Navy (#05060A)
Border: Gold accent (2px)
Shadow: Subtle, dark
Padding: 16px
```

### Status Indicators
```
✅ Success: Gold (#C9A844)
⚠️ Warning: Amber (#FFA500)
❌ Error: Red (#FF4444)
🔵 Info: Blue (#44AAFF)
⏳ Pending: Gray (#888888)
```

---

## Terminal Display

### Banner Style
```
┌─────────────────────────────────────────┐
│  Hermes Agent v0.19.0 (2026.7.20)       │
│  ─────────────────────────────────────── │
│  Repository: arthurlyons6/hermes-agent  │
│  Branch: main                           │
│  Commit: acfd376d                       │
└─────────────────────────────────────────┘
```

### Prompt Symbol
```
❯  (Gold symbol on navy background)
```

### Spinner Faces
```
Thinking: 🤔 💭 ⏳ 📚
Waiting: ⏳ 🔍 📡
```

### Tool Prefix
```
▏  (Gold pipe character for tool output)
```

---

## Presentation Materials

### Slide Deck Structure
1. **Cover:** Navy background, Gold text, White accent
2. **Agenda:** Bullet points with Gold icons
3. **Content:** Dark background, White text, Gold highlights
4. **Data:** Tables with Gold headers, Navy rows
5. **Conclusion:** Call to action with Gold button

### Color Usage in Presentations
- **Headers:** Gold (#C9A844)
- **Body:** White (#FFFFFF)
- **Background:** Navy (#05060A)
- **Accent:** Gold-Light (#E8C96A)
- **Warning:** Amber (#FFA500)

---

## Do Not Use

### ❌ Generic UI Patterns
- Glassmorphism
- Purple gradients
- Default library styling
- Repetitive card grids
- Emoji clutter

### ❌ Color Schemes
- Pastel colors
- Neon colors
- Low contrast combinations
- Bright reds (use Amber for warnings)

### ❌ Typography
- Comic Sans
- Papyrus
- Default system fonts without styling
- Overly decorative fonts for body text

### ❌ Layout Patterns
- Generic dashboard layouts
- Default data table styling
- Standard card grids
- Cookie-cutter modal designs

---

## Accessibility

### Contrast Ratios
- **Text on Navy:** 15:1 (exceeds 4.5:1)
- **Gold on Navy:** 4.5:1 (minimum)
- **White on Gold:** 4.5:1 (minimum)

### Focus States
- **Focus Ring:** Gold (2px solid)
- **Hover States:** Gold-Light background

---

## Implementation Notes

### CSS Variables
```css
--lyons-navy: #05060A;
--lyons-gold: #C9A844;
--lyons-gold-light: #E8C96A;
--lyons-dark-gold: #A8883A;
--lyons-text-primary: #FFFFFF;
--lyons-text-secondary: #A0A0A0;
--lyons-text-muted: #606060;
```

### Terminal Escape Codes
```bash
# Gold text
\033[38;2;201;168;68m

# Navy background
\033[48;2;5;6;10m
```

---

## Contact

For brand guideline questions or exceptions, contact Marcus (Chief of Staff).