# Icons Inventory — Before

## Current State: NO ICON LIBRARY

**The application currently uses ZERO icons.** All visual indicators are text/color-based.

### What exists:
- **Desktop app**: Hardcoded Unicode glyphs `✓` (checkmark) and `⚠` (warning) in DashboardPage
- **Desktop app window icon**: `assets/icons/app.ico` — only used for window/taskbar
- **Web app**: No icons whatsoever — status badges use colored text only
- **PWA**: `vite.config.js` references `/icons/icon-192.png` but the file is MISSING from `public/`

### Status indicators — all text/color only:
| Status    | Desktop Color | Web Tailwind Class    |
|-----------|---------------|----------------------|
| Draft     | #6B7280 gray  | text-slate-600       |
| Approved  | #059669 green | text-emerald-600     |
| Rejected  | #DC2626 red   | text-red-600         |
| Archived  | #D97706 amber | text-amber-600       |
| Cancelled | #6B7280 gray  | text-slate-600       |

### Missing:
- Sidebar navigation icons (no visual distinction between pages)
- Action button icons (all text-based: عرض, تعديل, حذف)
- Status icons (no checkmark, X, archive icons)
- Form field icons (no search, calendar, dropdown indicators)
- Notification icons (no bell, alert icons)
- Export icons (no download/upload icons)
- Navigation icons (no home, back, next icons)
- Sort indicators in table headers
- Filter indicators
- Pagination icons (prev/next are text-only: السابق/التالي)
- Organizational logo/default avatar
- File type icons in attachments

### Recommendation:
Adopt a single SVG icon library (e.g., Lucide, Material Symbols, or FontAwesome) and implement consistently across both desktop and web UIs.
