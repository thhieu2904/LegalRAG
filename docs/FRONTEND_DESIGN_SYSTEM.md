# Frontend Design System - Documentation

## 📋 Tổng quan

Hệ thống design system mới đã được tái cấu trúc để tách biệt rõ ràng giữa logic code và styling, tạo ra một kiến trúc dễ bảo trì và mở rộng.

## 🗂️ Cấu trúc thư mục

```
src/
├── styles/
│   ├── design-system/          # Core design tokens
│   │   ├── tokens.css          # CSS custom properties
│   │   ├── typography.css      # Typography system
│   │   ├── utilities.css       # Utility classes
│   │   └── index.css          # Design system entry
│   ├── components/             # Component-specific styles
│   │   ├── chat.css           # Chat interface styles
│   │   ├── chat-message.css   # Chat message styles
│   │   ├── speech.css         # Speech controls styles
│   │   └── ui.css             # UI component styles
│   ├── layouts/               # Layout styles
│   │   ├── app.css            # Application layout
│   │   └── admin.css          # Admin layout
│   ├── pages/                 # Page-specific styles
│   │   ├── chat-page.css      # Chat page styles
│   │   └── admin-pages.css    # Admin pages styles
│   └── main.css              # Main styles entry
├── components/
│   └── ui/
│       └── shared/            # Reusable UI components
│           ├── Button.tsx     # Button component
│           ├── Input.tsx      # Input component
│           ├── Card.tsx       # Card component
│           ├── Badge.tsx      # Badge component
│           └── index.ts       # Components export
└── lib/
    └── utils.ts              # Utility functions
```

## 🎨 Design Tokens

### Colors

```css
/* Primary Colors */
--color-primary-600: #2563eb;
--color-primary-700: #1d4ed8;

/* Status Colors */
--color-success-600: #16a34a;
--color-warning-600: #d97706;
--color-error-600: #dc2626;

/* Semantic Colors */
--color-background: var(--color-neutral-50);
--color-surface: #ffffff;
--color-text-primary: var(--color-neutral-900);
--color-text-secondary: var(--color-neutral-600);
```

### Typography

```css
/* Font Sizes */
--font-size-xs: 0.75rem; /* 12px */
--font-size-sm: 0.875rem; /* 14px */
--font-size-base: 1rem; /* 16px */
--font-size-lg: 1.125rem; /* 18px */

/* Font Weights */
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;
```

### Spacing

```css
--spacing-1: 0.25rem; /* 4px */
--spacing-2: 0.5rem; /* 8px */
--spacing-3: 0.75rem; /* 12px */
--spacing-4: 1rem; /* 16px */
--spacing-6: 1.5rem; /* 24px */
--spacing-8: 2rem; /* 32px */
```

## 🧩 Shared Components

### Button Component

```tsx
import { Button } from '@/components/ui/shared';

// Basic usage
<Button variant="primary">Click me</Button>

// With loading state
<Button loading variant="success">
  Saving...
</Button>

// Different sizes
<Button size="sm">Small</Button>
<Button size="lg">Large</Button>
<Button size="icon">🔍</Button>
```

### Input Component

```tsx
import { Input } from "@/components/ui/shared";

// With label and validation
<Input
  label="Email"
  type="email"
  required
  helperText="Enter a valid email address"
  error={hasError}
/>;
```

### Card Component

```tsx
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/shared";

<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Card description</CardDescription>
  </CardHeader>
  <CardContent>Card content goes here</CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>;
```

### Badge Component

```tsx
import { Badge } from '@/components/ui/shared';

<Badge variant="success">Active</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="error">Failed</Badge>
```

## 🎯 Typography Classes

### Headings

```css
.heading-1  /* 36px, bold */
/* 36px, bold */
.heading-2  /* 30px, bold */
.heading-3  /* 24px, semibold */
.heading-4  /* 20px, semibold */
.heading-5  /* 18px, medium */
.heading-6; /* 16px, medium */
```

### Body Text

```css
.body-large  /* 18px, relaxed line-height */
/* 18px, relaxed line-height */
.body-base   /* 16px, normal line-height */
.body-small  /* 14px, normal line-height */
.caption; /* 12px, muted color */
```

### Usage Example

```tsx
<h1 className="heading-1">Main Title</h1>
<h2 className="heading-2">Section Title</h2>
<p className="body-large">Important paragraph</p>
<p className="body-base">Regular paragraph</p>
<span className="caption">Small note</span>
```

## 🔧 Utility Classes

### Layout

```css
.flex          /* display: flex */
/* display: flex */
.flex-col      /* flex-direction: column */
.items-center  /* align-items: center */
.justify-between /* justify-content: space-between */
.gap-4; /* gap: 1rem */
```

### Spacing

```css
.p-4    /* padding: 1rem */
/* padding: 1rem */
.mt-2   /* margin-top: 0.5rem */
.mb-4   /* margin-bottom: 1rem */
.mx-auto; /* margin-left/right: auto */
```

### Background & Borders

```css
.bg-surface     /* background: white */
/* background: white */
.bg-primary     /* background: primary color */
.border-border  /* border: 1px solid border color */
.rounded-lg; /* border-radius: 0.5rem */
```

## 📱 Responsive Design

### Breakpoints

```css
/* Mobile First Approach */
@media (min-width: 768px) {
  /* Tablet */
  .md:grid-cols-2 {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  /* Desktop */
  .lg:grid-cols-3 {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

### Grid System

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
</div>
```

## 🎨 Theming

### Dark Mode Support

```css
[data-theme="dark"] {
  --color-background: var(--color-neutral-900);
  --color-surface: var(--color-neutral-800);
  --color-text-primary: var(--color-neutral-50);
}
```

### Usage

```tsx
// Toggle theme
document.documentElement.setAttribute("data-theme", "dark");
```

## 📋 Migration Guide

### From Old CSS to New System

**Old:**

```css
.my-component {
  background: #ffffff;
  color: #374151;
  padding: 16px;
  border-radius: 8px;
}
```

**New:**

```css
.my-component {
  background: var(--color-surface);
  color: var(--color-text-primary);
  padding: var(--spacing-4);
  border-radius: var(--radius-lg);
}
```

**Or use utility classes:**

```tsx
<div className="bg-surface text-primary p-4 rounded-lg">Content</div>
```

### Component Migration

**Old:**

```tsx
<button className="bg-blue-600 text-white px-4 py-2 rounded">Click me</button>
```

**New:**

```tsx
<Button variant="primary">Click me</Button>
```

## 🚀 Performance Benefits

1. **Smaller Bundle Size**: Modular CSS imports only what's needed
2. **Better Caching**: Separate CSS files for better browser caching
3. **CSS Custom Properties**: Efficient theming and customization
4. **Tree Shaking**: Unused styles are eliminated in production
5. **Component Isolation**: Styles don't leak between components

## 🔄 Development Workflow

### Adding New Components

1. Create component in `src/components/ui/shared/`
2. Add styles to appropriate CSS file in `src/styles/components/`
3. Export component in `src/components/ui/shared/index.ts`
4. Update documentation

### Adding New Styles

1. Use design tokens from `tokens.css`
2. Follow BEM naming convention for component styles
3. Use utility classes for simple styling
4. Create component-specific CSS modules when needed

### Testing Styles

1. Use the `DesignSystemDemo` component to test changes
2. Check responsive behavior at different breakpoints
3. Verify dark mode compatibility
4. Test accessibility (focus states, contrast)

## 📚 Best Practices

1. **Use Design Tokens**: Always use CSS custom properties instead of hardcoded values
2. **Semantic Classes**: Use semantic class names (.btn-primary vs .blue-button)
3. **Component Composition**: Build complex UIs by composing simple components
4. **Consistent Spacing**: Use the spacing scale for consistent layouts
5. **Accessibility**: Include focus states and ARIA attributes
6. **Mobile First**: Design for mobile, then enhance for larger screens

## 🛠️ Tools & Extensions

- **VS Code Extensions**: CSS Intellisense, Auto Rename Tag
- **Browser DevTools**: Inspect CSS custom properties
- **Design Tokens**: Use VS Code snippets for quick token insertion

---

Hệ thống design system mới này tạo ra một foundation vững chắc cho việc phát triển UI consistent, maintainable và scalable trong tương lai.
