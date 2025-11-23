# Admin Layout - Sidebar Navigation

## 📋 Tổng quan

Admin Dashboard với **Sidebar Navigation** theo thiết kế chuẩn enterprise:

- **Desktop**: Sidebar cố định bên trái (260px width)
- **Mobile**: Sidebar overlay (slide in/out) với backdrop
- **Header**: Compact header cho admin, full header cho public chat
- **Responsive**: Tự động điều chỉnh layout theo kích thước màn hình

---

## 🎨 Thiết kế Layout

```
┌──────────────┬─────────────────────────────────┐
│              │  Admin Header (Compact)         │
│              ├─────────────────────────────────┤
│   Sidebar    │                                 │
│   260px      │   Content Area                  │
│   (Dark)     │   (Light gray background)       │
│              │                                 │
│              │   - DashboardPage               │
│  Navigation  │   - CollectionsPage             │
│   Menu       │   - DocumentsPage (TODO)        │
│              │   - StatsPage (TODO)            │
│  Logout      │   - SettingsPage (TODO)         │
└──────────────┴─────────────────────────────────┘
```

---

## 🗂️ Components Structure

### 1. **Sidebar Component** (`frontend/src/components/layout/Sidebar/`)

**File**: `Sidebar.tsx`

```tsx
import {
  LayoutDashboard,
  FolderOpen,
  FileText,
  BarChart3,
  Settings,
  LogOut,
} from "lucide-react";

const menuItems = [
  { path: "/admin", icon: LayoutDashboard, label: "Tổng quan", exact: true },
  { path: "/admin/collections", icon: FolderOpen, label: "Bộ sưu tập" },
  { path: "/admin/documents", icon: FileText, label: "Tài liệu" },
  { path: "/admin/stats", icon: BarChart3, label: "Thống kê" },
  { path: "/admin/settings", icon: Settings, label: "Cài đặt" },
];
```

**Tính năng**:

- ✅ Logo section với LOGO_HCC.jpg
- ✅ Navigation menu với icons
- ✅ Active state highlighting (màu đỏ `#dc2626`)
- ✅ Logout button ở footer
- ✅ Dark theme (`#1e293b` background)
- ✅ Hover effects với smooth transitions
- ✅ Mobile: Slide in/out với overlay backdrop

**File**: `Sidebar.module.css`

**Key Styles**:

- `.sidebar`: Fixed position, dark background, full height
- `.logoSection`: Logo + title at top
- `.nav`: Navigation menu with flex column
- `.navItem`: Link items with hover + active states
- `.logoutBtn`: Logout button at bottom
- `.overlay`: Mobile backdrop (rgba black 60%)

---

### 2. **AdminLayout** (`frontend/src/layouts/AdminLayout/`)

**File**: `AdminLayout.tsx`

```tsx
export const AdminLayout = () => {
  const { sidebarOpen, toggleSidebar } = useUIStore();

  return (
    <div className={styles.adminLayout}>
      <Sidebar isOpen={sidebarOpen} onClose={toggleSidebar} />
      <div className={styles.contentWrapper}>
        <Header variant="admin" />
        <main className={styles.content}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};
```

**File**: `AdminLayout.module.css`

**Key Styles**:

- `.adminLayout`: Flex container (horizontal layout)
- `.contentWrapper`: Takes remaining space, margin-left 260px on desktop
- `.content`: Padding + light gray background (`#f8fafc`)

---

### 3. **Header Component** (`frontend/src/components/layout/Header/`)

**File**: `Header.tsx`

**Two Variants**:

1. **Admin Variant** (Compact):

   ```tsx
   <header className={styles.adminHeader}>
     <button onClick={toggleSidebar}>Menu</button>
     <div>Admin Dashboard</div>
     <Link to="/">Trang chủ</Link>
   </header>
   ```

2. **Chat Variant** (Full):
   - Logo section (25%)
   - Organization name (50%) - Red color
   - Assistant info (25%) with Settings button

**File**: `Header.module.css`

**Key Features**:

- `.adminHeader`: Compact header for admin pages
- `.header`: Full header for public chat page
- Menu button hidden on desktop (`@media min-width: 1024px`)

---

## 📄 Pages Structure

### 1. **DashboardPage** (`/admin`)

- Overview with stats cards (Collections, Documents, Processing status)
- Placeholder for future dashboard features
- 4 stat cards: 📁 Bộ sưu tập, 📄 Tài liệu, ✅ Đã xử lý, ⏳ Đang xử lý

### 2. **CollectionsPage** (`/admin/collections`)

- Collections management interface
- Create button at top-right
- Placeholder for CRUD grid
- Future: CollectionCard grid, modals for Create/Edit/Delete

### 3. **AdminPage** (`/admin/old`)

- Legacy placeholder page
- Will be removed after migration

---

## 🎯 Routing Configuration

**File**: `frontend/src/app/router.tsx`

```tsx
{
  path: ROUTES.ADMIN, // '/admin'
  element: <AdminLayout />,
  children: [
    { index: true, element: <DashboardPage /> },
    { path: 'collections', element: <CollectionsPage /> },
    // TODO: documents, stats, settings
  ],
}
```

**Navigation URLs**:

- `/admin` → Dashboard (overview)
- `/admin/collections` → Collections management
- `/admin/documents` → Documents management (TODO)
- `/admin/stats` → Statistics page (TODO)
- `/admin/settings` → Settings page (TODO)

---

## 🎨 Design System

### Colors

- **Primary Red**: `#dc2626` (Active states, buttons, government branding)
- **Dark Slate**: `#1e293b` (Sidebar background)
- **Light Gray**: `#f8fafc` (Content area background)
- **White**: `#ffffff` (Cards, modals)
- **Text Primary**: `#1e293b` (Headings)
- **Text Secondary**: `#64748b` (Body text)

### Sidebar Theme

- Background: `#1e293b` (Dark)
- Text: `#e2e8f0` (Light)
- Active: `#dc2626` (Red accent)
- Hover: `rgba(255, 255, 255, 0.1)`

### Transitions

- Duration: `0.2s` or `var(--transition-duration)`
- Timing: `ease-in-out` or `var(--transition-timing)`

---

## 📱 Responsive Behavior

### Desktop (≥1024px)

- Sidebar: Fixed, always visible (260px width)
- Content: Margin-left 260px
- Menu button: Hidden
- Layout: Horizontal (sidebar | content)

### Mobile (<1024px)

- Sidebar: Overlay with slide-in animation
- Content: Full width (no margin)
- Menu button: Visible in header
- Backdrop: Dark overlay (60% opacity)
- Click outside → Close sidebar

---

## 🚀 Next Steps

### Immediate (Task 2.3.4):

1. Build **CollectionsPage** full UI:

   - CollectionsGrid component
   - CollectionCard with icon/color/stats
   - CreateCollectionModal with form validation
   - EditCollectionModal
   - DeleteConfirmDialog with CASCADE warning
   - IconPicker and ColorPicker

2. Integrate with **adminStore**:
   - fetchCollections()
   - addCollection()
   - editCollection()
   - removeCollection()

### Future Tasks:

- DocumentsPage UI (Task 2.4)
- StatsPage (analytics dashboard)
- SettingsPage (system configuration)
- Public ChatPage at `/` (Task 2.5)

---

## ✅ Completed Features

- ✅ Sidebar navigation with dark theme
- ✅ AdminLayout with responsive design
- ✅ Header variants (admin compact vs chat full)
- ✅ DashboardPage placeholder
- ✅ CollectionsPage placeholder
- ✅ Routing configuration
- ✅ Mobile responsive (overlay sidebar)
- ✅ Logout functionality
- ✅ Active state navigation highlighting
- ✅ Smooth transitions and hover effects

---

## 📝 Notes

- **Logo**: `/LOGO_HCC.jpg` (48x48px in sidebar, logo section)
- **Organization**: TRUNG TÂM PHỤC VỤ HÀNH CHÍNH CÔNG XÃ LONG PHÚ
- **Auth**: Simple localStorage check (`isAdminLoggedIn`)
- **State Management**: Zustand (`useUIStore` for sidebar toggle)
- **Icons**: lucide-react library
- **Styling**: CSS Modules with BEM-like naming

---

## 🔧 Testing Checklist

When frontend runs:

- [ ] Desktop: Sidebar visible, menu button hidden
- [ ] Mobile: Sidebar hidden, menu button shows
- [ ] Click menu → Sidebar slides in
- [ ] Click backdrop → Sidebar closes
- [ ] Navigation links work (/admin, /admin/collections)
- [ ] Active state highlights current page
- [ ] Logout redirects to /admin/login
- [ ] "Trang chủ" button navigates to /
- [ ] Responsive breakpoints work correctly
- [ ] Smooth transitions on all interactions
