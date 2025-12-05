# Test Case: Multiple Fields on Same Line

## Original Content

```
Giới tính:...... Dân tộc:.......................................................Quốc tịch:.....................
```

## Expected Behavior After Backend Processing

### With 3 fields selected (indices 0, 1, 2):

**Before Fix:**

```
Giới tính:{{field_0}}{{field_1}}{{field_2}}...... Dân tộc:.......................................................Quốc tịch:.....................
```

❌ All placeholders inserted at first position

**After Fix:**

```
Giới tính:{{field_0}}...... Dân tộc:{{field_1}}.......................................................Quốc tịch:{{field_2}}.....................
```

✅ Each placeholder at correct position

## Frontend Rendering

After docx-preview renders the document, TreeWalker will find:

1. `{{field_0}}` → wrap with clickable span at "Giới tính" position
2. `{{field_1}}` → wrap with clickable span at "Dân tộc" position
3. `{{field_2}}` → wrap with clickable span at "Quốc tịch" position

User can click each span independently to toggle selection.

## Fix Applied

**File:** `admin-service/src/routers/form_templates.py`

**Change:** Added `'{{field_' in run.text` check to skip runs that already have placeholders

```python
for run_idx, run in enumerate(para.runs):
    # Skip if this run was already replaced (has placeholder)
    if '{{field_' in run.text:
        continue  # <-- NEW: Prevents replacing same position multiple times

    if re.search(r'[\.…]{4,}', run.text):
        run.text = re.sub(...)
        return
```

## How to Test

1. Create DOCX with line: `Giới tính:...... Dân tộc:...... Quốc tịch:......`
2. Upload to Create Template modal
3. Backend detects 3 positions (same paragraph_index)
4. Click Visual Mode
5. Should see 3 separate `{{field_N}}` spans at correct positions
6. Click each span independently - they should toggle green/blue
7. Continue → finalize should create template with 3 fields at correct positions

## Alternative Test (Your Case)

```
Giới tính:{{field_7}}{{field_8}}{{field_9}}......Dân tộc:
```

This is actually **3 consecutive placeholders** without spacing - backend may have detected:

- field_7, field_8, field_9 all pointing to the SAME dots pattern

If this happens, the fix ensures each field gets its own position instead of stacking.
