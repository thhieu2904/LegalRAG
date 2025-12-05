/**
 * PositionSelectionStepVisual Component
 * Option 2: Render DOCX với placeholders thay vì overlays
 * Strategy: Replace detected patterns với {{field_N}} TRƯỚC KHI render
 * - Load DOCX binary
 * - Replace patterns using python-docx logic (mirrored from backend)
 * - Render modified DOCX
 * - Make {{field_N}} elements clickable
 */

import { useState, useEffect, useRef } from 'react';
import { renderAsync } from 'docx-preview';
import { CheckSquare, Square, Link2, Unlink, AlertCircle } from 'lucide-react';
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
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const fieldElementsRef = useRef<Map<number, HTMLElement>>(new Map());

  // Auto-select all on mount
  useEffect(() => {
    const allIndices = positions.map((p) => p.index);
    setSelectedIndices(new Set(allIndices));
  }, [positions]);

  // Create clickable overlay for a position
  const createOverlay = useCallback(
    (position: DetectedPosition, paragraph: HTMLElement, textOffset: number) => {
      if (!containerRef.current) return;

      const overlay = document.createElement('div');
      overlay.className = styles.positionOverlay || '';
      overlay.dataset.index = String(position.index);

      // Position overlay using offsetTop/offsetLeft relative to container
      const paragraphRect = paragraph.getBoundingClientRect();
      const containerRect = containerRef.current.getBoundingClientRect();

      // Calculate position relative to scrollable container
      const scrollTop = containerRef.current.scrollTop || 0;
      const scrollLeft = containerRef.current.scrollLeft || 0;

      // Calculate width: use pattern length or remaining paragraph width
      const charWidth = 7; // Approximate char width for 13px Times New Roman
      const estimatedWidth = Math.max(position.text.length * charWidth, 80);
      const remainingWidth = paragraphRect.width - textOffset * charWidth;
      const overlayWidth = Math.min(estimatedWidth, Math.max(remainingWidth, 80));

      overlay.style.position = 'absolute';
      overlay.style.top = `${paragraphRect.top - containerRect.top + scrollTop}px`;
      overlay.style.left = `${paragraphRect.left - containerRect.left + scrollLeft + textOffset * charWidth}px`;
      overlay.style.width = `${overlayWidth}px`;
      overlay.style.height = `${paragraphRect.height}px`;
      overlay.style.zIndex = '100';

      // Add data attributes for debugging
      overlay.title = `Vị trí #${position.index}: ${position.label || position.text}`;

      // Add click handler
      const handleClick = () => togglePosition(position.index);
      const handleEnter = () => setHoveredIndex(position.index);
      const handleLeave = () => setHoveredIndex(null);

      overlay.addEventListener('click', handleClick);
      overlay.addEventListener('mouseenter', handleEnter);
      overlay.addEventListener('mouseleave', handleLeave);

      // Add to container
      containerRef.current.appendChild(overlay);
      overlaysRef.current.set(position.index, overlay);

      // Initial state update
      updateOverlayState(position.index);
    },
    [styles.positionOverlay]
  ); // eslint-disable-line react-hooks/exhaustive-deps

  // Update overlay visual state
  const updateOverlayState = useCallback(
    (index: number) => {
      const overlay = overlaysRef.current.get(index);
      if (!overlay) return;

      const isSelected = selectedIndices.has(index);
      const groupId = getPositionGroupId(index);
      const isInTempGroup = tempGroup.includes(index);
      const isHovered = hoveredIndex === index;

      overlay.className = styles.positionOverlay || '';
      if (isSelected && styles.overlaySelected) overlay.classList.add(styles.overlaySelected);
      if (groupId && styles.overlayGrouped) overlay.classList.add(styles.overlayGrouped);
      if (isInTempGroup && styles.overlayTempGroup) overlay.classList.add(styles.overlayTempGroup);
      if (isHovered && styles.overlayHovered) overlay.classList.add(styles.overlayHovered);
    },
    [
      selectedIndices,
      fieldGroups,
      tempGroup,
      hoveredIndex,
      styles.positionOverlay,
      styles.overlaySelected,
      styles.overlayGrouped,
      styles.overlayTempGroup,
      styles.overlayHovered,
    ]
  ); // eslint-disable-line react-hooks/exhaustive-deps

  // Render DOCX document
  useEffect(() => {
    // Map detected positions to rendered DOM elements
    const mapPositionsToDom = () => {
      if (!containerRef.current) return;

      // Get all paragraphs from rendered document
      const paragraphs = containerRef.current.querySelectorAll('p, td, th, li');

      positions.forEach((position) => {
        // Find matching paragraph by index
        const targetParagraph = Array.from(paragraphs)[position.paragraph_index];

        if (!targetParagraph) {
          console.warn(
            `Paragraph ${position.paragraph_index} not found for position ${position.index}`
          );
          return;
        }

        // Find text node containing the pattern
        const textContent = targetParagraph.textContent || '';

        // Try exact match first
        let patternIndex = textContent.indexOf(position.text);

        // If not found, try fuzzy matching for dots and tabs
        if (patternIndex === -1) {
          // For dot patterns: look for multiple dots/periods/spaces
          if (position.pattern_type === 'dots' && position.text.includes('.')) {
            const dotPattern = /[.\s_-]{4,}/;
            const match = textContent.match(dotPattern);
            if (match && match.index !== undefined) {
              patternIndex = match.index;
              console.log(`✓ Found dots pattern at position ${position.index} using regex`);
            }
          }
          // For tab patterns: look for multiple spaces
          else if (position.pattern_type === 'tab' || position.text === '\t') {
            const tabPattern = /\s{2,}/;
            const match = textContent.match(tabPattern);
            if (match && match.index !== undefined) {
              patternIndex = match.index;
              console.log(`✓ Found tab pattern at position ${position.index} using regex`);
            }
          }
        }

        if (patternIndex === -1) {
          console.warn(
            `Pattern "${position.text}" (${position.pattern_type}) not found in paragraph ${position.paragraph_index}`
          );
          // Create overlay at paragraph start as fallback
          patternIndex = 0;
          console.log(`⚠️ Using paragraph start for position ${position.index}`);
        }

        // Create overlay for this position
        createOverlay(position, targetParagraph as HTMLElement, patternIndex);
      });
    };

    const renderDocument = async () => {
      if (!containerRef.current || !documentFile) return;

      try {
        setLoading(true);
        setError(null);

        // Clear previous content
        containerRef.current.innerHTML = '';

        // Render DOCX
        await renderAsync(documentFile, containerRef.current, undefined, {
          className: styles.docxContainer,
          inWrapper: false,
          ignoreWidth: false,
          ignoreHeight: false,
          ignoreFonts: false,
          breakPages: true,
          ignoreLastRenderedPageBreak: false,
          experimental: false,
          trimXmlDeclaration: true,
          useBase64URL: false,
          renderChanges: false,
          renderHeaders: true,
          renderFooters: true,
          renderFootnotes: true,
          renderEndnotes: true,
        });

        // Wait for render to complete
        await new Promise((resolve) => setTimeout(resolve, 500));

        // Map positions to DOM elements
        mapPositionsToDom();

        setLoading(false);
      } catch (err) {
        console.error('Failed to render document:', err);
        setError('Không thể render văn bản. Vui lòng thử lại hoặc chuyển sang Preview Mode.');
        setLoading(false);
      }
    };

    renderDocument();
  }, [documentFile, positions, createOverlay]);

  // Update all overlays when state changes
  useEffect(() => {
    overlaysRef.current.forEach((_, index) => {
      updateOverlayState(index);
    });
  }, [selectedIndices, fieldGroups, tempGroup, hoveredIndex, updateOverlayState]);

  const togglePosition = (index: number) => {
    if (groupingMode) {
      // Grouping mode: add to temp group
      setTempGroup((prev) => {
        if (prev.includes(index)) {
          return prev.filter((i) => i !== index);
        }
        return [...prev, index];
      });
    } else {
      // Normal mode: select/deselect
      const newSelected = new Set(selectedIndices);
      if (newSelected.has(index)) {
        newSelected.delete(index);
      } else {
        newSelected.add(index);
      }
      setSelectedIndices(newSelected);
    }
  };

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

  const getPositionGroupId = (index: number): number | null => {
    const group = fieldGroups.find((g) => g.indices.includes(index));
    return group?.id || null;
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
          Click vào các vùng được highlight trong văn bản để chọn/bỏ chọn. Sử dụng chế độ nhóm để
          gộp nhiều vị trí thành 1 trường.
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
          {hoveredIndex !== null && (
            <div className={styles.statItem}>
              <Eye size={16} />
              <span>Vị trí: #{hoveredIndex}</span>
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

        {/* Document viewer with overlays */}
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
            </div>
          )}

          <div
            ref={containerRef}
            className={styles.visualDocumentViewer}
            style={{ position: 'relative', display: loading || error ? 'none' : 'block' }}
          />
        </div>

        {/* Field Groups sidebar */}
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
