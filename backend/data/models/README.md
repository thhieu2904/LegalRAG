# Models Directory

This directory is designed to store AI models but is protected by `.gitignore` to prevent accidental commits of large model files.

## Structure

```
backend/data/models/
├── .gitkeep                    # Preserves directory structure
├── README.md                   # This file
├── hf_cache/                   # HuggingFace cache (auto-created)
│   └── .gitkeep               # Protected from deletion
├── llm_dir/                   # LLM models directory
│   └── .gitkeep               # Protected from deletion
└── [other model directories]  # Created as needed
```

## Protection Rules

### ✅ ALWAYS COMMITTED:
- `.gitkeep` files (preserve directory structure)
- `README.md` files (documentation)
- Configuration files (`.json`, `.yaml`, `.txt`)

### ❌ NEVER COMMITTED:
- Large model files (`.bin`, `.safetensors`, `.pt`, `.pth`)
- HuggingFace cache directories
- Downloaded model directories
- Temporary files

## Usage

1. **Download models**: Use `python tools/1_setup_models.py`
2. **Verify setup**: Use `python tools/1_setup_models.py --verify-only`
3. **Manual placement**: Models can be manually placed here and will be ignored by git

## Safety Features

- **Directory preservation**: `.gitkeep` files ensure directories are never lost
- **Selective ignoring**: Only large files are ignored, not the structure
- **Clear documentation**: This README explains the purpose and rules

⚠️ **Important**: Never remove `.gitkeep` files - they protect the repository structure!
