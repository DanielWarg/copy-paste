# UI Style Tokens - Exact Design Specification

**Syfte:** Definiera exakta design-tokens från nuvarande UI för att säkerställa 1:1 visuell matchning vid rebuild.

**Senast uppdaterad:** 2025-12-25

---

## Typography

### Font Families

**Primary (Sans-serif):**
- Font: `Inter` (Google Fonts)
- Fallback: `-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'sans-serif'`
- Weights: 400, 500, 600
- Font-feature-settings: `"cv11", "ss01"`

**Serif:**
- Font: `Merriweather` (Google Fonts)
- Fallback: `serif`
- Weights: 300, 400, 700

**Monospace:**
- Font: `JetBrains Mono` (Google Fonts)
- Fallback: `ui-monospace, SFMono-Regular, Menlo, monospace`
- Weights: 400, 500

**Font Loading:**
```html
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Merriweather:wght@300;400;700&display=swap');
```

### Font Sizes

- `text-[10px]` - Section labels (uppercase, tracking-widest)
- `text-xs` - Small text (12px)
- `text-sm` - Body text (14px)
- `text-lg` - Large text (18px)
- `text-xl` - Extra large (20px)

### Font Weights

- `font-medium` - 500
- `font-bold` - 700

### Line Heights & Tracking

- `tracking-tight` - Tighter letter spacing
- `tracking-wider` - Wider letter spacing (uppercase labels)
- `tracking-widest` - Widest (section labels)

---

## Colors

### Light Mode

**Backgrounds:**
- `bg-zinc-50` - Main background (#fafafa)
- `bg-white` - Surface/panels
- `bg-zinc-100` - Active nav item background
- `bg-zinc-50/50` - Content area background (50% opacity)

**Text:**
- `text-zinc-900` - Primary text (#18181b)
- `text-zinc-500` - Muted text (#71717a)
- `text-zinc-400` - Secondary muted text (#a1a1aa)
- `text-zinc-600` - Medium text (#52525b)

**Borders:**
- `border-zinc-200` - Default borders (#e4e4e7)
- `border-zinc-100` - Subtle borders (#f4f4f5)

**Accents:**
- `bg-red-600` - Status indicator (#dc2626)
- `bg-emerald-600` - Success/primary actions (#059669)
- `bg-emerald-700` - Success hover (#047857)
- `bg-zinc-900` - Dark buttons (#18181b)

### Dark Mode

**Backgrounds:**
- `bg-[#09090b]` - Main background (zinc-950)
- `bg-[#18181b]` - Surface/panels (zinc-900)
- `bg-white/10` - Active nav item background
- `bg-black/20` - Content area background (20% opacity)
- `bg-zinc-800` - Avatar background (#27272a)
- `bg-zinc-900/50` - Code blocks (#18181b at 50%)

**Text:**
- `text-white` - Primary text
- `text-zinc-400` - Muted text (#a1a1aa)
- `text-zinc-500` - Secondary muted text (#71717a)
- `text-zinc-600` - Section labels (#52525b)
- `text-zinc-200` - Secondary text (#e4e4e7)

**Borders:**
- `border-white/5` - Default borders (5% opacity)
- `border-zinc-800` - Code block borders (#27272a)

**Accents:**
- `bg-white` - Dark mode buttons (with `dark:text-black`)
- `bg-emerald-600` - Success actions (same as light)

### Editorial Color Palette (from Tailwind config)

```javascript
editorial: {
  bg: '#09090b',       // zinc-950
  surface: '#18181b',  // zinc-900
  border: '#27272a',   // zinc-800
  text: '#e4e4e7',     // zinc-200
  muted: '#a1a1aa',    // zinc-400
  accent: '#18181b',   // zinc-900
  success: '#10b981',  // emerald-500
  warning: '#f59e0b',  // amber-500
  error: '#ef4444',    // red-500
}
```

---

## Spacing Scale

**Padding:**
- `p-4` - 16px (1rem)
- `p-5` - 20px (1.25rem)
- `p-6` - 24px (1.5rem)
- `px-3` - 12px horizontal (0.75rem)
- `px-4` - 16px horizontal (1rem)
- `px-6` - 24px horizontal (1.5rem)
- `py-2` - 8px vertical (0.5rem)
- `py-1.5` - 6px vertical (0.375rem)

**Gaps:**
- `gap-2` - 8px (0.5rem)
- `gap-3` - 12px (0.75rem)
- `gap-4` - 16px (1rem)

**Margins:**
- `mb-0.5` - 2px bottom (0.125rem)
- `mb-3` - 12px bottom (0.75rem)
- `mt-8` - 32px top (2rem)
- `ml-2` - 8px left (0.5rem)
- `ml-6` - 24px left (1.5rem)

**Space (for flex/grid):**
- `space-y-1` - 4px vertical gap (0.25rem)
- `space-y-6` - 24px vertical gap (1.5rem)

---

## Border Radius

- `rounded` - 4px (default)
- `rounded-sm` - 2px
- `rounded-md` - 6px
- `rounded-full` - 9999px (circles)

---

## Shadows

**Box Shadows:**
- `shadow-sm` - Small shadow (used on buttons)
- No heavy shadows (minimal design)

**Borders (used instead of shadows):**
- `border-r` - Right border
- `border-b` - Bottom border
- `border-t` - Top border

---

## Layout Dimensions

**Sidebar:**
- Width: `w-64` - 256px (16rem)
- Header height: `h-16` - 64px (4rem)

**Main Content:**
- Header height: `h-14` - 56px (3.5rem)
- Max width: `max-w-5xl` - 1024px (64rem)

**Icons:**
- Small: `size={14}` - 14px
- Default: `size={16}` - 16px
- Medium: `size={18}` - 18px
- Large: `size={20}` - 20px
- Stroke width: `strokeWidth={2}`

**Status Indicator:**
- Size: `w-2 h-2` - 8px × 8px
- Animation: `animate-pulse`

**Avatar:**
- Size: `w-6 h-6` - 24px × 24px

---

## Scrollbar Styling

```css
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #52525b; /* zinc-600 */
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #71717a; /* zinc-500 */
}
```

---

## Transitions & Animations

**Transitions:**
- `transition-all duration-150` - All properties, 150ms
- `transition-opacity` - Opacity only
- `transition-colors` - Colors only

**Animations:**
- `animate-pulse` - Pulsing animation (status indicator)

**Hover States:**
- `hover:opacity-90` - 90% opacity
- `hover:opacity-100` - 100% opacity
- `hover:bg-zinc-50` - Light background
- `hover:bg-white/5` - Dark mode background (5% opacity)
- `hover:text-zinc-900` - Light mode text
- `hover:text-white` - Dark mode text

---

## Opacity

- `opacity-60` - 60% (user profile)
- `opacity-75` - 75% (muted elements)

---

## Component-Specific Tokens

### Navigation Items

**Active:**
- Background: `bg-zinc-100` (light) / `bg-white/10` (dark)
- Text: `text-zinc-900` (light) / `text-white` (dark)
- Icon: `text-zinc-900` (light) / `text-white` (dark)

**Inactive:**
- Text: `text-zinc-500` (light) / `text-zinc-400` (dark)
- Icon: `text-zinc-400` (light) / `text-zinc-500` (dark)
- Hover: `hover:bg-zinc-50` (light) / `hover:bg-white/5` (dark)

### Buttons

**Primary (Success):**
- Background: `bg-emerald-600`
- Hover: `bg-emerald-700`
- Text: `text-white`
- Padding: `px-4 py-2`
- Radius: `rounded-sm`
- Shadow: `shadow-sm`

**Secondary (Dark):**
- Background: `bg-zinc-900` (light) / `bg-white` (dark)
- Text: `text-white` (light) / `text-black` (dark)
- Hover: `hover:opacity-90`

### Section Labels

- Font size: `text-[10px]` (10px)
- Weight: `font-bold`
- Color: `text-zinc-400` (light) / `text-zinc-600` (dark)
- Transform: `uppercase`
- Tracking: `tracking-widest`
- Margin: `mb-3`
- Padding: `px-3`

### Content Area

- Background: `bg-zinc-50/50` (light) / `bg-black/20` (dark)
- Padding: `p-6`

---

## Dark Mode Implementation

**Toggle:**
- Uses `class` strategy (not `media`)
- HTML element: `<html class="dark">`
- Tailwind config: `darkMode: 'class'`

**Color Strategy:**
- Light mode: Zinc palette (zinc-50 to zinc-900)
- Dark mode: Custom hex values matching zinc-950/900/800
- Borders: Use opacity (`white/5`) for subtle borders in dark mode

---

## Implementation Notes

1. **Tailwind CDN:** Current implementation uses Tailwind CDN with custom config
2. **CSS Variables:** Should be implemented for easier theming
3. **Font Loading:** Google Fonts via @import
4. **Antialiasing:** `antialiased` class on body
5. **Selection:** `selection:bg-zinc-200 dark:selection:bg-zinc-800`

---

**Version:** 1.0.0  
**Senast uppdaterad:** 2025-12-25


