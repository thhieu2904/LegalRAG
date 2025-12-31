/**
 * PositionSelectionStepVisual Component - Version 2
 * NEW APPROACH: Ask backend to create temp template, then render it
 *
 * Flow:
 * 1. Call backend API: POST /admin/forms/preview-template
 *    - Send: file + selected_indices (all positions)
 *    - Receive: Modified DOCX binary with {{field_1}}, {{field_2}}...
 * 2. Render modified DOCX với docx-preview
 * 3. Find all {{field_N}} trong rendered HTML
 * 4. Make them clickable divs với highlight
 * 5. User click → toggle selection
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { renderAsync } from 'docx-preview';
import { CheckSquare, Square, Link2, Unlink, AlertCircle } from 'lucide-react';
import { apiClient } from '@/services/api/client';
import { ENDPOINTS } from '@/services/api/endpoints';
import type { DetectedPosition } from '@/types/template.types';
import styles from './CreateTemplateModal.module.css';

interface PositionSelectionStepVisualProps {
  positions: DetectedPosition[];
  documentFile: File;
  onNext: (selectedIndices: number[], fieldGroups: number[][]) => void;
  onBack: () => void;
}

export interface FieldGroup {
  id: number;
  name: string;
  indices: number[];
}

export const PositionSelectionStepVisual = ({
  positions,
  documentFile,
  onNext,
  onBack,
}: PositionSelectionStepVisualProps) => {
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());
  const [fieldGroups, setFieldGroups] = useState<FieldGroup[]>([]);
  const [groupingMode, setGroupingMode] = useState(false);
  const [tempGroup, setTempGroup] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [previewDocx, setPreviewDocx] = useState<Blob | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  // Toggle position selection (supports grouping mode)
  const togglePositionWithGrouping = useCallback((index: number, isGroupMode: boolean) => {
    if (isGroupMode) {
      setTempGroup((prev) => {
        if (prev.includes(index)) {
          return prev.filter((i) => i !== index);
        }
        return [...prev, index];
      });
    } else {
      setSelectedIndices((prev) => {
        const newSet = new Set(prev);
        if (newSet.has(index)) {
          newSet.delete(index);
        } else {
          newSet.add(index);
        }
        return newSet;
      });
    }
  }, []);

  // Step 3: Make {{field_N}} clickable
  const makeFieldsClickable = useCallback(() => {
    if (!containerRef.current) return;

    // Find all text nodes containing {{field_
    const walker = document.createTreeWalker(containerRef.current, NodeFilter.SHOW_TEXT, null);

    const fieldPattern = /\{\{field_(\d+)\}\}/g;
    const textNodes: Text[] = [];

    let node: Node | null;
    while ((node = walker.nextNode())) {
      if (node.textContent?.includes('{{field_')) {
        textNodes.push(node as Text);
      }
    }

    // Replace text nodes với clickable spans
    textNodes.forEach((textNode) => {
      const text = textNode.textContent || '';
      const parent = textNode.parentElement;
      if (!parent) return;

      // Split by field pattern
      const parts: (string | { index: number; text: string })[] = [];
      let lastIndex = 0;
      let match: RegExpExecArray | null;

      while ((match = fieldPattern.exec(text)) !== null) {
        // Add text before match
        if (match.index > lastIndex) {
          parts.push(text.substring(lastIndex, match.index));
        }
        // Add field match
        parts.push({
          index: parseInt(match[1] || '0', 10),
          text: match[0],
        });
        lastIndex = match.index + match[0].length;
      }
      // Add remaining text
      if (lastIndex < text.length) {
        parts.push(text.substring(lastIndex));
      }

      // Create fragment với spans
      const fragment = document.createDocumentFragment();
      parts.forEach((part) => {
        if (typeof part === 'string') {
          fragment.appendChild(document.createTextNode(part));
        } else {
          const span = document.createElement('span');
          span.className = styles.fieldPlaceholder || 'field-placeholder';
          span.dataset.index = String(part.index);
          span.textContent = part.text;

          const isSelected = selectedIndices.has(part.index);

          // Add tooltip
          span.title = isSelected ? `Click để bỏ chọn ${part.text}` : `Click để chọn ${part.text}`;

          span.style.cssText = `
            background: ${isSelected ? 'rgba(34, 197, 94, 0.35)' : 'rgba(59, 130, 246, 0.25)'};
            border: 2px solid ${isSelected ? 'rgba(34, 197, 94, 0.8)' : 'rgba(59, 130, 246, 0.6)'};
            border-radius: 4px;
            padding: 2px 4px;
            cursor: pointer;
            transition: all 0.15s ease;
            display: inline-block;
            user-select: none;
          `;

          // Add hover effect
          span.addEventListener('mouseenter', () => {
            span.style.transform = 'scale(1.05)';
            span.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.15)';
          });

          span.addEventListener('mouseleave', () => {
            span.style.transform = 'scale(1)';
            span.style.boxShadow = 'none';
          });

          // Add click handler with visual feedback
          span.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            // Click animation
            span.style.transform = 'scale(0.95)';
            setTimeout(() => {
              span.style.transform = 'scale(1)';
            }, 100);

            togglePositionWithGrouping(part.index, groupingMode);
          });

          fragment.appendChild(span);
        }
      });

      // Replace text node
      parent.replaceChild(fragment, textNode);
    });
  }, [selectedIndices, groupingMode, togglePositionWithGrouping]);

  // Auto-select all on mount
  useEffect(() => {
    const allIndices = positions.map((p) => p.index);
    setSelectedIndices(new Set(allIndices));
  }, [positions]);

  // Step 1: Create preview template từ backend
  useEffect(() => {
    const createPreviewTemplate = async () => {
      try {
        setLoading(true);
        setError(null);

        // Call backend API to create temp template
        const formData = new FormData();
        formData.append('file', documentFile);

        // Send ALL detected indices for preview
        const allIndices = positions.map((p) => p.index);
        formData.append('selected_indices', allIndices.join(','));

        const response = await apiClient.post(ENDPOINTS.ADMIN.PROCESS_TEMPLATE_PREVIEW, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          responseType: 'blob', // Receive binary DOCX
        });

        // Store preview DOCX blob
        setPreviewDocx(response.data);
      } catch (err) {
        console.error('Failed to create preview template:', err);
        setError('Không thể tạo preview. Backend chưa hỗ trợ API này.');
        setLoading(false);
      }
    };

    createPreviewTemplate();
  }, [documentFile, positions]);

  // Step 2: Render preview DOCX khi có blob
  useEffect(() => {
    const renderPreviewDoc = async () => {
      if (!previewDocx || !containerRef.current) return;

      try {
        setLoading(true);

        // Clear previous content
        containerRef.current.innerHTML = '';

        // Convert blob to file for renderAsync
        const previewFile = new File([previewDocx], 'preview.docx', {
          type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        });

        // Render preview DOCX
        await renderAsync(previewFile, containerRef.current, undefined, {
          className: styles.docxContainer,
          inWrapper: false,
          breakPages: true,
        });

        // Wait for render
        await new Promise((resolve) => setTimeout(resolve, 300));

        // Step 3: Find và make {{field_N}} clickable
        makeFieldsClickable();

        setLoading(false);
      } catch (err) {
        console.error('Failed to render preview:', err);
        setError('Không thể render văn bản.');
        setLoading(false);
      }
    };

    renderPreviewDoc();
  }, [previewDocx, makeFieldsClickable]);

  // Update field spans khi selection thay đổi
  useEffect(() => {
    if (!containerRef.current) return;

    const spans = containerRef.current.querySelectorAll('[data-index]');
    spans.forEach((span) => {
      const index = parseInt((span as HTMLElement).dataset.index || '0', 10);
      const isSelected = selectedIndices.has(index);
      const fieldText = (span as HTMLElement).textContent || '';

      (span as HTMLElement).style.background = isSelected
        ? 'rgba(34, 197, 94, 0.35)'
        : 'rgba(59, 130, 246, 0.25)';
      (span as HTMLElement).style.borderColor = isSelected
        ? 'rgba(34, 197, 94, 0.8)'
        : 'rgba(59, 130, 246, 0.6)';

      // Update tooltip
      (span as HTMLElement).title = isSelected
        ? `Click để bỏ chọn ${fieldText}`
        : `Click để chọn ${fieldText}`;
    });
  }, [selectedIndices]);

  const toggleAll = () => {
    if (selectedIndices.size === positions.length) {
      setSelectedIndices(new Set());
    } else {
      const allIndices = positions.map((p) => p.index);
      setSelectedIndices(new Set(allIndices));
    }
  };

  const createGroup = () => {
    if (tempGroup.length < 2) {
      alert('Vui lòng chọn ít nhất 2 vị trí để nhóm');
      return;
    }

    const newGroup: FieldGroup = {
      id: fieldGroups.length + 1,
      name: `Nhóm ${fieldGroups.length + 1}`,
      indices: [...tempGroup].sort((a, b) => a - b),
    };

    setFieldGroups([...fieldGroups, newGroup]);
    setTempGroup([]);
    setGroupingMode(false);
  };

  const removeGroup = (groupId: number) => {
    setFieldGroups(fieldGroups.filter((g) => g.id !== groupId));
  };

  const handleNext = () => {
    if (selectedIndices.size === 0) {
      alert('Vui lòng chọn ít nhất một vị trí');
      return;
    }

    const groups = fieldGroups.map((g) => g.indices);
    onNext(
      Array.from(selectedIndices).sort((a, b) => a - b),
      groups
    );
  };

  const allSelected = selectedIndices.size === positions.length;

  return (
    <div className={styles.stepForm}>
      <div className={styles.stepContent}>
        <h3 className={styles.stepTitle}>Bước 2: Chọn vị trí điền thông tin (Visual Mode)</h3>
        <p className={styles.stepDescription}>
          <span style={{ display: 'block', marginBottom: '8px' }}>
            Click vào các trường <code>{'{{field_N}}'}</code> trong văn bản để chọn/bỏ chọn.
          </span>
          <span style={{ display: 'flex', gap: '16px', fontSize: '0.875rem', color: '#666' }}>
            <span>
              <span
                style={{
                  display: 'inline-block',
                  width: '12px',
                  height: '12px',
                  background: 'rgba(34, 197, 94, 0.35)',
                  border: '2px solid rgba(34, 197, 94, 0.8)',
                  borderRadius: '2px',
                  marginRight: '4px',
                  verticalAlign: 'middle',
                }}
              ></span>
              = Đã chọn
            </span>
            <span>
              <span
                style={{
                  display: 'inline-block',
                  width: '12px',
                  height: '12px',
                  background: 'rgba(59, 130, 246, 0.25)',
                  border: '2px solid rgba(59, 130, 246, 0.6)',
                  borderRadius: '2px',
                  marginRight: '4px',
                  verticalAlign: 'middle',
                }}
              ></span>
              = Chưa chọn
            </span>
          </span>
        </p>

        {/* Stats bar */}
        <div className={styles.visualStats}>
          <div className={styles.statItem}>
            <CheckSquare size={16} />
            <span>
              Đã chọn: {selectedIndices.size}/{positions.length}
            </span>
          </div>
          {fieldGroups.length > 0 && (
            <div className={styles.statItem}>
              <Link2 size={16} />
              <span>Nhóm: {fieldGroups.length}</span>
            </div>
          )}
        </div>

        {/* Toolbar */}
        <div className={styles.visualToolbar}>
          <button
            onClick={toggleAll}
            className={styles.toolbarButton}
            title={allSelected ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
          >
            {allSelected ? <Square size={16} /> : <CheckSquare size={16} />}
            {allSelected ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
          </button>

          <button
            onClick={() => {
              if (groupingMode) {
                setTempGroup([]);
              }
              setGroupingMode(!groupingMode);
            }}
            className={`${styles.toolbarButton} ${groupingMode ? styles.toolbarButtonActive : ''}`}
            title="Chế độ nhóm"
          >
            {groupingMode ? <Unlink size={16} /> : <Link2 size={16} />}
            {groupingMode ? 'Hủy nhóm' : 'Nhóm vị trí'}
          </button>

          {groupingMode && tempGroup.length >= 2 && (
            <button onClick={createGroup} className={styles.toolbarButtonPrimary}>
              Tạo nhóm ({tempGroup.length})
            </button>
          )}
        </div>

        {/* Document viewer */}
        <div className={styles.visualViewerContainer}>
          {loading && (
            <div className={styles.visualLoading}>
              <div className={styles.spinner}></div>
              <p>Đang render văn bản...</p>
            </div>
          )}

          {error && (
            <div className={styles.visualError}>
              <AlertCircle size={48} />
              <p>{error}</p>
              <p style={{ fontSize: '0.75rem', marginTop: '8px' }}>
                Cần implement backend API: POST /admin/forms/preview-template
              </p>
            </div>
          )}

          <div
            ref={containerRef}
            className={styles.visualDocumentViewer}
            style={{ display: loading || error ? 'none' : 'block' }}
          />
        </div>

        {/* Field Groups */}
        {fieldGroups.length > 0 && (
          <div className={styles.visualGroups}>
            <h4 className={styles.groupsTitle}>
              <Link2 size={16} />
              Nhóm đã tạo ({fieldGroups.length})
            </h4>
            <div className={styles.groupsList}>
              {fieldGroups.map((group) => (
                <div key={group.id} className={styles.groupItem}>
                  <div className={styles.groupHeader}>
                    <input
                      type="text"
                      value={group.name}
                      onChange={(e) => {
                        const updated = fieldGroups.map((g) =>
                          g.id === group.id ? { ...g, name: e.target.value } : g
                        );
                        setFieldGroups(updated);
                      }}
                      className={styles.groupNameInput}
                    />
                    <button
                      onClick={() => removeGroup(group.id)}
                      className={styles.removeGroupButton}
                      title="Xóa nhóm"
                    >
                      ×
                    </button>
                  </div>
                  <div className={styles.groupIndices}>Vị trí: {group.indices.join(', ')}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className={styles.stepActions}>
        <button onClick={onBack} className={styles.secondaryButton}>
          Quay lại
        </button>
        <button
          onClick={handleNext}
          disabled={selectedIndices.size === 0}
          className={styles.primaryButton}
        >
          Tiếp tục
        </button>
      </div>
    </div>
  );
};
