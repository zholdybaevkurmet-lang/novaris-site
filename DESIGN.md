---
name: Industrial Cybernetics
colors:
  surface: '#10131b'
  surface-dim: '#10131b'
  surface-bright: '#363941'
  surface-container-lowest: '#0b0e15'
  surface-container-low: '#181c23'
  surface-container: '#1c2027'
  surface-container-high: '#272a32'
  surface-container-highest: '#31353d'
  on-surface: '#e0e2ed'
  on-surface-variant: '#bccbb9'
  inverse-surface: '#e0e2ed'
  inverse-on-surface: '#2d3038'
  outline: '#869585'
  outline-variant: '#3d4a3d'
  surface-tint: '#4ae176'
  primary: '#4be277'
  on-primary: '#003915'
  primary-container: '#22c55e'
  on-primary-container: '#004b1e'
  inverse-primary: '#006e2f'
  secondary: '#c3c6cf'
  on-secondary: '#2d3137'
  secondary-container: '#454950'
  on-secondary-container: '#b5b8c1'
  tertiary: '#ffb5ab'
  on-tertiary: '#60130d'
  tertiary-container: '#ff8b7c'
  on-tertiary-container: '#76231b'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#6bff8f'
  primary-fixed-dim: '#4ae176'
  on-primary-fixed: '#002109'
  on-primary-fixed-variant: '#005321'
  secondary-fixed: '#dfe2eb'
  secondary-fixed-dim: '#c3c6cf'
  on-secondary-fixed: '#181c22'
  on-secondary-fixed-variant: '#43474e'
  tertiary-fixed: '#ffdad5'
  tertiary-fixed-dim: '#ffb4a9'
  on-tertiary-fixed: '#410001'
  on-tertiary-fixed-variant: '#7f2a21'
  background: '#10131b'
  on-background: '#e0e2ed'
  surface-variant: '#31353d'
  text-primary: '#FFFFFF'
  text-secondary: rgba(255, 255, 255, 0.55)
  border-subtle: rgba(255, 255, 255, 0.1)
  glow-green: rgba(34, 197, 94, 0.4)
typography:
  display-lg:
    fontFamily: Space Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '500'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Space Grotesk
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Space Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-sm:
    fontFamily: Space Grotesk
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
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
  margin-desktop: 64px
---

## Brand & Style

The design system is engineered for a high-tech, industrial aesthetic tailored to the electrical infrastructure sector. It evokes a sense of precision, power, and technical expertise. 

The style is a fusion of **Dark Minimalism** and **Glassmorphism**, utilizing a "Terminal-inspired" color palette. The UI should feel like a high-end control interface—sophisticated, efficient, and reliable. Visual interest is generated through light-emissive effects (glows) rather than heavy textures, maintaining a clean, systematic feel that prioritizes technical data and product clarity.

## Colors

The palette is anchored by a deep-space black background to ensure maximum contrast for the vibrant accent. 

- **Primary:** A high-visibility "Signal Green" used for interactive states, status indicators, and focal points.
- **Surface:** A slightly lighter charcoal-navy for cards and containers to create depth without breaking the dark aesthetic.
- **Glass Effects:** Semi-transparent overlays should use the secondary color with a background blur (12px-20px) to simulate high-tech frosted panels.
- **Functional Glows:** Use the primary green for box-shadows on active elements to simulate electrical luminescence.

## Typography

The design system utilizes **Space Grotesk** exclusively. Its geometric, technical character and open apertures make it perfect for an industrial context. 

Headlines should be set with tighter letter-spacing to feel impactful and structural. Body text requires generous line-height to maintain readability against the dark background. Small labels and metadata should use uppercase styling with increased letter-spacing to mimic technical blueprints and spec sheets.

## Layout & Spacing

The layout follows a **Rigid Grid** philosophy. Content is organized on a 12-column grid for desktop and a 4-column grid for mobile. 

- **Alignment:** Use hard-edged alignments. Components should feel "snapped" into place.
- **Rhythm:** An 8px linear scale governs all padding and margins to maintain mathematical consistency.
- **Structure:** Use thin 1px borders (`border-subtle`) to define sections rather than large gaps of whitespace, reinforcing the "panelized" industrial look.

## Elevation & Depth

Depth in this design system is achieved through **Luminance and Blur** rather than traditional shadows.

1.  **Base Layer:** The background (#060910).
2.  **Raised Layer:** Surfaces (#0D1117) with a 1px border of `rgba(255,255,255,0.1)`.
3.  **Interactive Layer:** Elements that are hovered or active emit a soft green outer glow (`0px 0px 15px rgba(34, 197, 94, 0.3)`).
4.  **Glass Panels:** Used for overlays and navigation bars. Use `backdrop-filter: blur(16px)` with a slightly transparent surface color to create a sense of sophisticated layering.

## Shapes

The shape language is **Strict and Architectural**. 

Small border radii (4px-8px) are used to prevent the UI from feeling aggressive while maintaining a sharp, precision-machined appearance. Larger elements like hero cards should never exceed 8px of rounding. Interactive elements like buttons may use a 4px radius to feel "solid."

## Components

- **Buttons:** Primary buttons use a solid green background with black text for maximum contrast. On hover, they trigger an outer glow. Secondary buttons use a transparent background with a 1px green border.
- **Cards:** Use the glassmorphism effect. A subtle 1px border on the top and left edges should be slightly brighter than the bottom and right to simulate a technical "beveled" light source.
- **Input Fields:** Dark backgrounds with subtle white borders. Upon focus, the border turns primary green with a faint glow.
- **Status Indicators:** Use small, pulsing green dots for "In Stock" or "System Active" statuses, reinforcing the electrical theme.
- **Data Tables:** Highly structured with thin dividers. Header rows should use the `label-sm` typographic style.
- **Navigation:** Fixed header with a high-blur glass effect to allow content to scroll underneath while maintaining legibility.