/**
 * CreateTemplateModal Component
 * Multi-step modal for hybrid form template creation
 */

import { useState } from 'react';
import { X } from 'lucide-react';
import { apiClient } from '@/services/api/client';
import { ENDPOINTS } from '@/services/api/endpoints';
import { UploadStep } from './UploadStep';
import { PositionSelectionStep, type FieldGroup } from './PositionSelectionStep';
import { PositionSelectionStepVisual } from './PositionSelectionStepVisual_v2';
import { ConfirmStep } from './ConfirmStep';
import type { DetectedPosition, DetectResponse, FinalizeResponse } from '@/types/template.types';
import styles from './CreateTemplateModal.module.css';

interface CreateTemplateModalProps {
  isOpen: boolean;
  documentId: string;
  onClose: () => void;
  onSuccess: () => void;
}

type Step = 1 | 2 | 3;

export const CreateTemplateModal = ({
  isOpen,
  documentId,
  onClose,
  onSuccess,
}: CreateTemplateModalProps) => {
  const [currentStep, setCurrentStep] = useState<Step>(1);
  const [file, setFile] = useState<File | null>(null);
  const [formName, setFormName] = useState('');
  const [description, setDescription] = useState('');
  const [detectedPositions, setDetectedPositions] = useState<DetectedPosition[]>([]);
  const [selectedIndices, setSelectedIndices] = useState<number[]>([]);
  const [fieldGroups, setFieldGroups] = useState<FieldGroup[]>([]);
  const [viewMode, setViewMode] = useState<'preview' | 'visual'>('preview');
  const [uploading, setUploading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleReset = () => {
    setCurrentStep(1);
    setFile(null);
    setFormName('');
    setDescription('');
    setDetectedPositions([]);
    setSelectedIndices([]);
    setFieldGroups([]);
    setViewMode('preview');
    setUploading(false);
    setCreating(false);
    setError(null);
  };

  const handleClose = () => {
    if (!uploading && !creating) {
      handleReset();
      onClose();
    }
  };

  // Step 1: Upload & Detect
  const handleUpload = async (uploadedFile: File, name: string, desc: string) => {
    try {
      setUploading(true);
      setError(null);
      setFile(uploadedFile);
      setFormName(name);
      setDescription(desc);

      const formData = new FormData();
      formData.append('file', uploadedFile);
      formData.append('document_id', documentId);
      formData.append('form_name', name);

      const response = await apiClient.post<DetectResponse>(
        ENDPOINTS.ADMIN.PROCESS_TEMPLATE_DETECT,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      if (response.data.success) {
        setDetectedPositions(response.data.positions);
        setCurrentStep(2);
      } else {
        setError('Không thể phát hiện vị trí điền. Vui lòng thử lại.');
      }
    } catch (err) {
      console.error('Detect error:', err);
      setError(err instanceof Error ? err.message : 'Lỗi khi phát hiện vị trí điền');
    } finally {
      setUploading(false);
    }
  };

  // Step 2: Select Positions
  const handlePositionsSelected = (indices: number[], groups: number[][]) => {
    setSelectedIndices(indices);

    // Convert groups to FieldGroup format
    const groupObjects: FieldGroup[] = groups.map((indices, idx) => ({
      id: idx + 1,
      name: `Nhóm ${idx + 1}`,
      indices,
    }));
    setFieldGroups(groupObjects);

    // Debug log for field groups
    console.log('Field groups created:', fieldGroups.length > 0 ? fieldGroups : 'none');

    setCurrentStep(3);
  };

  // Step 3: Finalize Template
  const handleConfirm = async () => {
    if (!file) return;

    try {
      setCreating(true);
      setError(null);

      // Expand field groups into individual indices
      // Example: If group [1, 2, 3] → backend will create {{field_1}} for all 3 positions
      // Or we can send groups as-is if backend supports it
      const expandedIndices = [...selectedIndices];

      // For now, keep individual selection logic
      // Backend can be enhanced later to support grouping metadata

      const formData = new FormData();
      formData.append('file', file);
      formData.append('document_id', documentId);
      formData.append('form_name', formName);
      if (description) {
        formData.append('description', description);
      }
      formData.append('selected_indices', expandedIndices.join(','));

      const response = await apiClient.post<FinalizeResponse>(
        ENDPOINTS.ADMIN.PROCESS_TEMPLATE_FINALIZE,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      if (response.data.success) {
        onSuccess();
        handleReset();
        onClose();
      } else {
        setError('Không thể tạo mẫu. Vui lòng thử lại.');
      }
    } catch (err) {
      console.error('Finalize error:', err);
      setError(err instanceof Error ? err.message : 'Lỗi khi tạo mẫu biểu mẫu');
    } finally {
      setCreating(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay} onClick={handleClose}>
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>Tạo mẫu biểu mẫu tự động</h2>
          <button
            onClick={handleClose}
            className={styles.closeButton}
            disabled={uploading || creating}
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        </div>

        {/* Progress Indicator */}
        <div className={styles.progressBar}>
          <div className={styles.progressStep}>
            <div
              className={`${styles.progressDot} ${currentStep >= 1 ? styles.progressDotActive : ''}`}
            >
              1
            </div>
            <span className={styles.progressLabel}>Tải lên</span>
          </div>
          <div
            className={`${styles.progressLine} ${currentStep >= 2 ? styles.progressLineActive : ''}`}
          />
          <div className={styles.progressStep}>
            <div
              className={`${styles.progressDot} ${currentStep >= 2 ? styles.progressDotActive : ''}`}
            >
              2
            </div>
            <span className={styles.progressLabel}>Chọn vị trí</span>
          </div>
          <div
            className={`${styles.progressLine} ${currentStep >= 3 ? styles.progressLineActive : ''}`}
          />
          <div className={styles.progressStep}>
            <div
              className={`${styles.progressDot} ${currentStep >= 3 ? styles.progressDotActive : ''}`}
            >
              3
            </div>
            <span className={styles.progressLabel}>Xác nhận</span>
          </div>
        </div>

        {/* Step Content */}
        {currentStep === 1 && (
          <UploadStep onUpload={handleUpload} uploading={uploading} error={error} />
        )}

        {currentStep === 2 && (
          <>
            {/* Mode toggle */}
            <div className={styles.modeToggle}>
              <button
                onClick={() => setViewMode('preview')}
                className={`${styles.modeButton} ${viewMode === 'preview' ? styles.modeButtonActive : ''}`}
              >
                Preview Mode
              </button>
              <button
                onClick={() => setViewMode('visual')}
                className={`${styles.modeButton} ${viewMode === 'visual' ? styles.modeButtonActive : ''}`}
              >
                Visual Mode
              </button>
            </div>

            {/* Conditional rendering based on viewMode */}
            {viewMode === 'preview' ? (
              <PositionSelectionStep
                positions={detectedPositions}
                onNext={handlePositionsSelected}
                onBack={() => setCurrentStep(1)}
              />
            ) : (
              <PositionSelectionStepVisual
                positions={detectedPositions}
                documentFile={file!}
                onNext={handlePositionsSelected}
                onBack={() => setCurrentStep(1)}
              />
            )}
          </>
        )}

        {currentStep === 3 && (
          <ConfirmStep
            formName={formName}
            description={description}
            selectedCount={selectedIndices.length}
            fileName={file?.name || ''}
            onConfirm={handleConfirm}
            onBack={() => setCurrentStep(2)}
            creating={creating}
          />
        )}
      </div>
    </div>
  );
};
