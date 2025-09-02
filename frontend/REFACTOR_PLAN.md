# 🚀 REFACTOR PLAN - FRONTEND RESTRUCTURE

## 📋 **PHASE 1: BACKUP & PREPARATION**

### ✅ To-Do List Phase 1:

- [ ] 1.1. Backup toàn bộ src folder hiện tại
- [ ] 1.2. Tạo branch mới cho refactor
- [ ] 1.3. Document cấu trúc hiện tại
- [ ] 1.4. Test current build để đảm bảo working state

### 🛠️ Commands Phase 1:

```bash
# Backup
cp -r src src_backup_$(date +%Y%m%d_%H%M%S)

# Create new branch
git checkout -b refactor/simple-structure

# Test current build
npm run build
npm run dev
```

---

## 📋 **PHASE 2: MOVE PAGES STRUCTURE**

### ✅ To-Do List Phase 2:

- [ ] 2.1. Move `pages/simple/*.tsx` lên `pages/*.tsx`
- [ ] 2.2. Update import paths trong App.tsx/SimpleApp.tsx
- [ ] 2.3. Update import paths trong routing
- [ ] 2.4. Xóa folder `pages/simple/` (nếu empty)
- [ ] 2.5. Test routing hoạt động

### 📁 File Changes Phase 2:

```
BEFORE:                    AFTER:
pages/simple/ChatPage.tsx  →  pages/ChatPage.tsx
pages/simple/AdminPage.tsx →  pages/AdminPage.tsx
pages/simple/OCRPage.tsx   →  pages/OCRPage.tsx
```

### 🔧 Import Updates Phase 2:

```tsx
// BEFORE
import ChatPage from "./pages/simple/ChatPage";

// AFTER
import ChatPage from "./pages/ChatPage";
```

---

## 📋 **PHASE 3: MOVE CSS TO COMPONENT LEVEL**

### ✅ To-Do List Phase 3:

- [ ] 3.1. Tạo CSS files cùng cấp với pages
- [ ] 3.2. Move styles từ `styles/` sang component level
- [ ] 3.3. Update import CSS trong components
- [ ] 3.4. Clean up `styles/` folder (chỉ giữ globals)
- [ ] 3.5. Test styling hoạt động đúng

### 📁 File Changes Phase 3:

```
CREATE:
pages/ChatPage.css
pages/AdminPage.css
pages/OCRPage.css
components/SimpleNavigation.css

MOVE FROM styles/:
styles/ChatPage.css → pages/ChatPage.css
styles/components/admin-*.css → pages/AdminPage.css
styles/components/chat-*.css → pages/ChatPage.css
```

---

## 📋 **PHASE 4: SIMPLIFY APP STRUCTURE**

### ✅ To-Do List Phase 4:

- [ ] 4.1. Rename/Replace App.tsx với SimpleApp.tsx
- [ ] 4.2. Update main.tsx to use SimpleApp
- [ ] 4.3. Remove old complex routing
- [ ] 4.4. Test toàn bộ routing
- [ ] 4.5. Clean up unused imports

### 🔧 Changes Phase 4:

```tsx
// main.tsx
import SimpleApp from "./SimpleApp.tsx";
// Instead of import App from './App.tsx';
```

---

## 📋 **PHASE 5: CLEANUP & OPTIMIZATION**

### ✅ To-Do List Phase 5:

- [ ] 5.1. Remove unused files từ styles/
- [ ] 5.2. Remove unused components (nếu có)
- [ ] 5.3. Clean up domain/ architecture/ folders (không cần)
- [ ] 5.4. Update package imports nếu cần
- [ ] 5.5. Run linter và fix errors

---

## 📋 **PHASE 6: TESTING & VALIDATION**

### ✅ To-Do List Phase 6:

- [ ] 6.1. Test build production: `npm run build`
- [ ] 6.2. Test dev server: `npm run dev`
- [ ] 6.3. Test routing: `/`, `/admin`, `/ocr`
- [ ] 6.4. Test API calls với RAG service (port 8000)
- [ ] 6.5. Test API calls với OCR service (port 8001)
- [ ] 6.6. Test components render correctly
- [ ] 6.7. Test styling hoạt động
- [ ] 6.8. Cross-browser testing (Chrome, Edge)

---

## 📋 **PHASE 7: DOCUMENTATION & FINALIZE**

### ✅ To-Do List Phase 7:

- [ ] 7.1. Update README.md với cấu trúc mới
- [ ] 7.2. Document API usage examples
- [ ] 7.3. Create component usage guide
- [ ] 7.4. Git commit changes
- [ ] 7.5. Create PR description

---

## 🎯 **EXPECTED FINAL STRUCTURE:**

```
src/
├── api/                    # ✅ API tập trung
│   ├── axios-config.ts
│   ├── rag-api.ts
│   ├── ocr-api.ts
│   └── index.ts
├── pages/                  # ✅ Pages đơn giản
│   ├── ChatPage.tsx
│   ├── ChatPage.css
│   ├── AdminPage.tsx
│   ├── AdminPage.css
│   ├── OCRPage.tsx
│   └── OCRPage.css
├── components/             # ✅ Components cần thiết
│   ├── SimpleNavigation.tsx
│   ├── SimpleNavigation.css
│   ├── ui/                 # Shadcn components
│   └── chat/               # Chat components (keep)
├── hooks/                  # ✅ Custom hooks
│   ├── useChat.ts
│   ├── useVoice.ts
│   └── useModal.ts
├── contexts/               # ✅ React contexts
│   └── VoiceContext.tsx
├── services/               # ✅ Services
│   ├── chatService.ts
│   └── textToSpeech.ts
├── styles/                 # ✅ Chỉ global styles
│   ├── globals.css
│   ├── variables.css
│   └── tailwind.css
├── types/                  # ✅ TypeScript types
├── SimpleApp.tsx           # ✅ Main App
└── main.tsx                # ✅ Entry point
```

---

## ⚠️ **RISKS & MITIGATION:**

### 🚨 Potential Issues:

1. **Import path breaks** → Fix systematically phase by phase
2. **CSS missing** → Test styling after each move
3. **Routing breaks** → Test each route individually
4. **TypeScript errors** → Use VS Code problems panel
5. **Build fails** → Rollback to previous working state

### 🛡️ Safety Measures:

- Backup before each phase
- Test after each phase
- Commit after successful phase
- Keep working version available

---

## 🚀 **READY TO START?**

**Next step:** Execute Phase 1 - Backup & Preparation

Would you like me to start with Phase 1? Y/N
