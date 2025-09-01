# ⚡ QUICK SETUP - LegalRAG Backend Environment

## 🎯 TL;DR - Cách nhanh nhất

```bash
# 1. Mở x64 Native Tools Command Prompt (Windows)
# 2. Navigate to environment folder
cd path\to\LegalRAG_Fixed\backend\environment

# 3. Run auto setup
setup_environment.bat LegalRAG_Backend

# 4. Done! Environment ready to use
```

## ✅ Verify Setup

```bash
conda activate LegalRAG_Backend
python -c "
import torch, transformers, chromadb, fastapi
print('✅ All critical packages imported successfully!')
print(f'PyTorch CUDA: {torch.cuda.is_available()}')
"
```

## 🆘 If Problems

1. **Script failed?** → Check [`README.md`](README.md) for detailed troubleshooting
2. **GPU issues?** → Must use x64 Native Tools Command Prompt
3. **Package conflicts?** → Try manual installation following README.md

## 📁 Files Explanation

- `environment.yml` → Main config file (use this!)
- `setup_environment.bat/sh` → Auto setup scripts
- `README.md` → Complete detailed guide
- `conda-packages.txt` → Backup conda packages
- `pip-requirements.txt` → Backup pip packages
