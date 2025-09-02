# 🎨 CẤU TRÚC STYLES ĐÚNG CÁCH

## ❌ Cấu trúc hiện tại (lộn xộn):

```
styles/
├── chat.css              # ← Trùng lặp
├── ChatPage.css           # ← Trùng lặp
├── components/            # ← Quá nhiều file nhỏ
│   ├── admin-header.css
│   ├── chat-footer.css
│   ├── chat-header.css
│   └── ... (20+ files)
├── design-system/
├── layouts/
└── pages/
```

## ✅ Cấu trúc mới (theo component):

```
src/
├── pages/
│   ├── ChatPage.tsx
│   ├── ChatPage.css       # ← Style đi cùng component
│   ├── AdminPage.tsx
│   ├── AdminPage.css      # ← Style đi cùng component
│   ├── OCRPage.tsx
│   └── OCRPage.css        # ← Style đi cùng component
├── components/
│   ├── SimpleNavigation.tsx
│   ├── SimpleNavigation.css
│   └── ui/
│       ├── button.tsx
│       └── button.css
└── styles/
    ├── globals.css        # ← Chỉ global styles
    ├── variables.css      # ← CSS variables
    └── tailwind.css       # ← Tailwind base
```

## Nguyên tắc:

- **1 component = 1 CSS file** (nằm cùng folder)
- **Global styles** → `styles/globals.css`
- **Component styles** → cùng cấp với `.tsx`
