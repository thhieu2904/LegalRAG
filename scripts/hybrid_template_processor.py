# -*- coding: utf-8 -*-
"""
Test script for hybrid template workflow.
Tests the new TemplateProcessor and FormFiller with dot-padding.

Run: python scripts/hybrid_template_processor.py
"""
import sys
import os

# Add form-service to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'form-service', 'src'))

from services.template_processor import TemplateProcessor, analyze_template


def test_analyze():
    """Test analyzing DOCX for fillable fields."""
    print("\n" + "="*70)
    print("TEST: Analyze hotich.docx")
    print("="*70 + "\n")
    
    docx_path = r'd:\Personal\LegalRAG\docs\thamkhao\form_thamkhao\hotich.docx'
    
    with open(docx_path, 'rb') as f:
        content = f.read()
    
    processor = TemplateProcessor()
    result = processor.analyze(content)
    
    print(f"Success: {result.success}")
    print(f"Total fields: {result.total_fields}")
    print(f"\nDetected fields:")
    
    for f in result.fields:
        conf = "★★★" if f.confidence > 0.8 else "★★☆" if f.confidence > 0.5 else "★☆☆"
        print(f"  {conf} {f.suggested_name:<25} | {f.label[:30]:<30} | {f.field_type}")
    
    return result


def test_create_template():
    """Test creating template with placeholders."""
    print("\n" + "="*70)
    print("TEST: Create template from forms gốc.docx")
    print("="*70 + "\n")
    
    docx_path = r'd:\Personal\LegalRAG\docs\thamkhao\form_thamkhao\forms gốc.docx'
    output_path = r'd:\Personal\LegalRAG\docs\thamkhao\form_thamkhao\forms_goc_template_new.docx'
    
    with open(docx_path, 'rb') as f:
        content = f.read()
    
    # Step 1: Analyze
    processor = TemplateProcessor()
    analysis = processor.analyze(content)
    
    print(f"Analyzed: {analysis.total_fields} fields")
    
    # Step 2: Simulate admin confirmation (use all detected fields)
    confirmed_fields = []
    for f in analysis.fields:
        confirmed_fields.append({
            'paragraph_index': f.paragraph_index,
            'field_name': f.suggested_name,
            'label': f.label
        })
    
    print(f"Confirmed: {len(confirmed_fields)} fields")
    
    # Step 3: Create template
    result = processor.create_template(content, confirmed_fields)
    
    if result.success:
        # Save for verification
        with open(output_path, 'wb') as f:
            f.write(result.template_bytes)
        print(f"✓ Template saved: {output_path}")
        print(f"✓ Placeholders: {result.placeholders}")
    else:
        print(f"✗ Failed: {result.errors}")
    
    return result


def test_extract_placeholders():
    """Test extracting placeholders from template."""
    print("\n" + "="*70)
    print("TEST: Extract placeholders")
    print("="*70 + "\n")
    
    template_path = r'd:\Personal\LegalRAG\docs\thamkhao\form_thamkhao\forms_goc_template_new.docx'
    
    if not os.path.exists(template_path):
        print("⚠ Template not found. Run test_create_template first.")
        return
    
    with open(template_path, 'rb') as f:
        content = f.read()
    
    processor = TemplateProcessor()
    placeholders = processor.extract_placeholders(content)
    
    print(f"Found {len(placeholders)} placeholders:")
    for p in placeholders:
        print(f"  - {p}")


if __name__ == "__main__":
    test_analyze()
    test_create_template()
    test_extract_placeholders()
    
    print("\n" + "="*70)
    print("ALL TESTS COMPLETE")
    print("="*70)
