/**
 * Enhanced PositionSelectionStep Component
 * - Visual preview với highlight
 * - Field grouping support
 * - Better context display
 */

import { useState, useEffect } from 'react';
import { CheckSquare, Square, Filter, Eye, Link2, Unlink } from 'lucide-react';
import type { DetectedPosition } from '@/types/template.types';
import styles from './CreateTemplateModal.module.css';

interface PositionSelectionStepProps {
  positions: DetectedPosition[];
  onNext: (selectedIndices: number[], fieldGroups: number[][]) => void;
  onBack: () => void;
}

export interface FieldGroup {
  id: number;
  name: string;
  indices: number[];
}

export const PositionSelectionStep = ({
  positions,
  onNext,
  onBack,
}: PositionSelectionStepProps) => {
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());
  const [filterType, setFilterType] = useState<'all' | 'dots' | 'tab'>('all');
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [fieldGroups, setFieldGroups] = useState<FieldGroup[]>([]);
  const [groupingMode, setGroupingMode] = useState(false);
  const [tempGroup, setTempGroup] = useState<number[]>([]);

  // Auto-select all on mount
  useEffect(() => {
    const allIndices = positions.map((p) => p.index);
    setSelectedIndices(new Set(allIndices));
  }, [positions]);

  const filteredPositions =
    filterType === 'all' ? positions : positions.filter((p) => p.pattern_type === filterType);

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

    // Convert field groups to array format for backend
    const groups = fieldGroups.map((g) => g.indices);
    onNext(
      Array.from(selectedIndices).sort((a, b) => a - b),
      groups
    );
  };

  const allSelected = selectedIndices.size === positions.length;
  const someSelected = selectedIndices.size > 0 && selectedIndices.size < positions.length;

  return (
    <div className={styles.stepForm}>
      <div className={styles.stepContent}>
        <h3 className={styles.stepTitle}>Bước 2: Chọn và nhóm vị trí điền thông tin</h3>
        <p className={styles.stepDescription}>
          Đã phát hiện {positions.length} vị trí có thể điền. Chọn các vị trí và nhóm chúng nếu cần
          (ví dụ: Họ, Chữ đệm, Tên → 1 trường "Họ tên").
        </p>

        {/* Split View: Preview + Table */}
        <div className={styles.splitView}>
          {/* Left: Visual Preview */}
          <div className={styles.previewPanel}>
            <div className={styles.previewHeader}>
              <Eye size={16} />
              <span>Xem trước ngữ cảnh</span>
            </div>
            <div className={styles.previewContent}>
              {hoveredIndex !== null ? (
                <div className={styles.previewDetail}>
                  <div className={styles.previewBadge}>Vị trí #{hoveredIndex}</div>

                  {/* Context before */}
                  {positions[hoveredIndex]?.context_before &&
                    positions[hoveredIndex].context_before.length > 0 && (
                      <div className={styles.contextBefore}>
                        {positions[hoveredIndex].context_before.map((text, i) => (
                          <p key={`before-${i}`}>{text}</p>
                        ))}
                      </div>
                    )}

                  {/* Main paragraph with highlight */}
                  <div className={styles.contextMain}>
                    {positions[hoveredIndex]?.label && (
                      <>
                        <mark className={styles.highlight}>
                          {positions[hoveredIndex].label}:{' '}
                          <span className={styles.placeholder}>________</span>
                        </mark>
                        {positions[hoveredIndex].full_paragraph
                          .replace(positions[hoveredIndex].label + ':', '')
                          .replace(/[\.…]{4,}/, '')}
                      </>
                    )}
                    {!positions[hoveredIndex]?.label && (
                      <mark className={styles.highlight}>
                        <span className={styles.placeholder}>________</span>
                      </mark>
                    )}
                  </div>

                  {/* Context after */}
                  {positions[hoveredIndex]?.context_after &&
                    positions[hoveredIndex].context_after.length > 0 && (
                      <div className={styles.contextAfter}>
                        {positions[hoveredIndex].context_after.map((text, i) => (
                          <p key={`after-${i}`}>{text}</p>
                        ))}
                      </div>
                    )}

                  <div className={styles.previewMeta}>
                    <span>Đoạn văn: #{positions[hoveredIndex]?.paragraph_index}</span>
                    <span className={styles.previewType}>
                      {positions[hoveredIndex]?.pattern_type === 'dots' ? 'Dấu chấm' : 'Tab'}
                    </span>
                  </div>
                </div>
              ) : (
                <div className={styles.previewPlaceholder}>
                  <Eye size={48} />
                  <p>Di chuột qua bảng để xem chi tiết</p>
                </div>
              )}
            </div>

            {/* Field Groups */}
            {fieldGroups.length > 0 && (
              <div className={styles.groupsList}>
                <h4 className={styles.groupsTitle}>
                  <Link2 size={16} />
                  Các nhóm đã tạo ({fieldGroups.length})
                </h4>
                {fieldGroups.map((group) => (
                  <div key={group.id} className={styles.groupItem}>
                    <div className={styles.groupInfo}>
                      <span className={styles.groupName}>{group.name}</span>
                      <span className={styles.groupCount}>{group.indices.length} vị trí</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeGroup(group.id)}
                      className={styles.removeGroupButton}
                    >
                      <Unlink size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right: Table */}
          <div className={styles.tablePanel}>
            {/* Controls */}
            <div className={styles.tableControls}>
              <div className={styles.filterGroup}>
                <Filter size={16} />
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value as 'all' | 'dots' | 'tab')}
                  className={styles.filterSelect}
                >
                  <option value="all">Tất cả ({positions.length})</option>
                  <option value="dots">
                    Dấu chấm ({positions.filter((p) => p.pattern_type === 'dots').length})
                  </option>
                  <option value="tab">
                    Tab ({positions.filter((p) => p.pattern_type === 'tab').length})
                  </option>
                </select>
              </div>

              <div className={styles.controlButtons}>
                {groupingMode ? (
                  <>
                    <button
                      type="button"
                      onClick={createGroup}
                      disabled={tempGroup.length < 2}
                      className={styles.createGroupButton}
                    >
                      <Link2 size={16} />
                      Tạo nhóm ({tempGroup.length})
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setGroupingMode(false);
                        setTempGroup([]);
                      }}
                      className={styles.cancelGroupButton}
                    >
                      Hủy
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      type="button"
                      onClick={() => setGroupingMode(true)}
                      className={styles.startGroupButton}
                    >
                      <Link2 size={16} />
                      Nhóm vị trí
                    </button>
                    <button type="button" onClick={toggleAll} className={styles.selectAllButton}>
                      {allSelected ? (
                        <>
                          <CheckSquare size={16} />
                          Bỏ chọn tất cả
                        </>
                      ) : (
                        <>
                          <Square size={16} />
                          Chọn tất cả
                        </>
                      )}
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Mode indicator */}
            {groupingMode && (
              <div className={styles.modeIndicator}>
                <Link2 size={16} />
                <span>Chế độ nhóm: Chọn các vị trí cần gộp thành 1 trường</span>
              </div>
            )}

            {/* Table */}
            <div className={styles.tableWrapper}>
              <table className={styles.positionsTable}>
                <thead>
                  <tr>
                    <th className={styles.checkboxCell}>
                      {!groupingMode && (
                        <button
                          type="button"
                          onClick={toggleAll}
                          className={styles.checkboxButton}
                          aria-label="Toggle all"
                        >
                          {allSelected ? (
                            <CheckSquare size={20} />
                          ) : someSelected ? (
                            <div className={styles.indeterminateCheckbox} />
                          ) : (
                            <Square size={20} />
                          )}
                        </button>
                      )}
                    </th>
                    <th className={styles.indexCell}>#</th>
                    <th className={styles.labelCell}>Nhãn</th>
                    <th className={styles.contextCell}>Ngữ cảnh</th>
                    <th className={styles.paragraphCell}>Đoạn</th>
                    <th className={styles.typeCell}>Loại</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPositions.map((position) => {
                    const isSelected = selectedIndices.has(position.index);
                    const isInTempGroup = tempGroup.includes(position.index);
                    const groupId = getPositionGroupId(position.index);
                    const rowClass = `${isSelected ? styles.selectedRow : ''} ${
                      isInTempGroup ? styles.tempGroupRow : ''
                    } ${groupId ? styles.groupedRow : ''}`;

                    return (
                      <tr
                        key={position.index}
                        className={rowClass}
                        onClick={() => togglePosition(position.index)}
                        onMouseEnter={() => setHoveredIndex(position.index)}
                        onMouseLeave={() => setHoveredIndex(null)}
                      >
                        <td className={styles.checkboxCell}>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              togglePosition(position.index);
                            }}
                            className={styles.checkboxButton}
                            aria-label={`Toggle position ${position.index}`}
                          >
                            {groupingMode ? (
                              isInTempGroup ? (
                                <CheckSquare size={20} />
                              ) : (
                                <Square size={20} />
                              )
                            ) : isSelected ? (
                              <CheckSquare size={20} />
                            ) : (
                              <Square size={20} />
                            )}
                          </button>
                        </td>
                        <td className={styles.indexCell}>
                          {position.index}
                          {groupId && <span className={styles.groupBadge}>G{groupId}</span>}
                        </td>
                        <td className={styles.labelCell}>
                          <span className={styles.labelText}>
                            {position.label || <em className={styles.noLabel}>Không có nhãn</em>}
                          </span>
                        </td>
                        <td className={styles.contextCell}>
                          <span className={styles.contextText}>{position.text}</span>
                        </td>
                        <td className={styles.paragraphCell}>#{position.paragraph_index}</td>
                        <td className={styles.typeCell}>
                          <span
                            className={`${styles.badge} ${
                              position.pattern_type === 'dots' ? styles.badgeDots : styles.badgeTab
                            }`}
                          >
                            {position.pattern_type === 'dots' ? 'Chấm' : 'Tab'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Selection Summary */}
            <div className={styles.selectionSummary}>
              <p>
                Đã chọn: <strong>{selectedIndices.size}</strong> / {positions.length} vị trí
                {fieldGroups.length > 0 && (
                  <span className={styles.groupSummary}> • {fieldGroups.length} nhóm</span>
                )}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className={styles.stepActions}>
        <button type="button" onClick={onBack} className={styles.backButton}>
          ← Quay lại
        </button>
        <div className={styles.stepInfo}>Bước 2/3</div>
        <button
          type="button"
          onClick={handleNext}
          disabled={selectedIndices.size === 0 || groupingMode}
          className={styles.nextButton}
        >
          Tiếp theo ({selectedIndices.size} trường) →
        </button>
      </div>
    </div>
  );
};
