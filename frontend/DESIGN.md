---
name: Sustainably Minimalist
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#3d4a3d'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#6d7b6c'
  outline-variant: '#bccbb9'
  surface-tint: '#006e2f'
  primary: '#006e2f'
  on-primary: '#ffffff'
  primary-container: '#22c55e'
  on-primary-container: '#004b1e'
  inverse-primary: '#4ae176'
  secondary: '#516072'
  on-secondary: '#ffffff'
  secondary-container: '#d2e1f7'
  on-secondary-container: '#556477'
  tertiary: '#735c00'
  on-tertiary: '#ffffff'
  tertiary-container: '#cfa800'
  on-tertiary-container: '#4f3e00'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#6bff8f'
  primary-fixed-dim: '#4ae176'
  on-primary-fixed: '#002109'
  on-primary-fixed-variant: '#005321'
  secondary-fixed: '#d4e4fa'
  secondary-fixed-dim: '#b9c8de'
  on-secondary-fixed: '#0d1c2d'
  on-secondary-fixed-variant: '#39485a'
  tertiary-fixed: '#ffe083'
  tertiary-fixed-dim: '#eec200'
  on-tertiary-fixed: '#231b00'
  on-tertiary-fixed-variant: '#574500'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.05em
  data-mono:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 16px
  md: 24px
  lg: 48px
  xl: 80px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
---

## Brand & Style
The design system for this eco-mobility platform focuses on "Transparent Efficiency." The visual narrative balances high-tech data processing with environmental stewardship. The aesthetic is *Sustainably Minimalist*: a fusion of clean corporate structures and organic breathability.

The target audience includes urban planners, eco-conscious commuters, and logistics managers who require immediate clarity. The UI must evoke a sense of hope and precision, moving away from "doom-and-gloom" environmentalism toward actionable, data-driven optimism. We prioritize heavy whitespace to reduce cognitive load and use vibrant accent colors only to denote impact or urgency.

## Colors
This design system utilizes a high-clarity palette centered on environmental health.
- *Sustainability Green (#22C55E):* Used for primary actions, positive data trends, and "Eco-Action" triggers. It represents growth and carbon-neutral success.
- *Cloud Gray (#94A3B8):* Reserved for technical markers, pollution data, and inactive states. It provides a neutral, clinical contrast to the green.
- *Alert Yellow (#FACC15):* Used sparingly for sensitive ecological zones or areas approaching threshold limits.
- *Backgrounds:* We use a pure White (#FFFFFF) for the base canvas to maximize the "fresh" feel, with light-wash grays for structural containment.

## Typography
We use *Inter* exclusively for its exceptional legibility in data-heavy environments and its neutral, modern tone. 
- *Headlines:* Use tighter letter-spacing and bold weights to create a strong information hierarchy.
- *Body:* Standard weight for maximum readability against white backgrounds.
- *Data Display:* For numerical values in charts and gauges, ensure tabular figures (tnum) are enabled to maintain alignment in moving data streams.

## Layout & Spacing
The layout follows a *Fluid Grid* model to accommodate complex data visualizations across varying screen sizes. 
- *Desktop:* 12-column grid with 24px gutters. Content is often housed in "Data Tiles" that span 3, 4, or 6 columns.
- *Mobile:* 4-column grid with 16px margins.
- *Spacing Philosophy:* We utilize an 8pt linear scale. Large vertical gaps (48px+) are encouraged between disparate data sections to prevent visual clutter and maintain the "Minimalist" promise.

## Elevation & Depth
In alignment with the "Sustainably Minimalist" style, depth is achieved through *Tonal Layers* rather than heavy shadows.
- *Level 0 (Base):* White (#FFFFFF) for the main application background.
- *Level 1 (Cards/Tiles):* Light Gray (#F1F5F9) surfaces with a 1px border (#E2E8F0) to define boundaries without adding weight.
- *Interactive States:* Use a very subtle, highly diffused shadow (0px 4px 20px rgba(15, 23, 42, 0.05)) only when a user hovers over an actionable data card.

## Shapes
The shape language is "Approachable Tech." We avoid sharp industrial corners in favor of generous radii that feel more organic and modern.
- *Standard Radius:* 12px for cards and primary buttons.
- *Large Radius:* 16px for main dashboard containers.
- *Circular:* Used exclusively for status indicators, circular gauges, and user avatars.

## Components
### Buttons
- *Primary (Eco-Action):* Solid Green (#22C55E) with White text. Bold weight. High contrast (exceeding WCAG AAA).
- *Secondary:* Ghost style with Cloud Gray (#94A3B8) borders and text.

### Data Visualization
- *Circular Gauges:* Use a thick stroke (8px-12px) with rounded caps. The "track" should be a very light gray (#F1F5F9) and the "fill" should be Sustainability Green.
- *Line Charts:* Use a 2px stroke width. Avoid area fills unless the opacity is below 10%. Use dots only for specific data points upon interaction.

### Inputs & Cards
- *Input Fields:* White background with a 1px Gray border. On focus, the border transitions to Green.
- *Data Cards:* Content-heavy tiles using the Level 1 surface. Headers within cards should use the label-md typography style for clear categorization.

### Status Indicators
- Use a "Traffic Light" system using the primary, tertiary, and neutral gray colors for impact levels, always accompanied by text labels for accessibility.