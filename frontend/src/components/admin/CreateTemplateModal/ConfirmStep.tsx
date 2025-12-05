/**
 * ConfirmStep Component
 * Step 3: Review and confirm template creation
 */

import { Check, FileText, Hash } from 'lucide-react';
import styles from './CreateTemplateModal.module.css';

interface ConfirmStepProps {
  formName: string;
  description: string;
  selectedCount: number;
  fileName: string;
  onConfirm: () => void;
  onBack: () => void;
  creating: boolean;
}

export const ConfirmStep = ({
  formName,
  description,
  selectedCount,
  fileName,
  onConfirm,
  onBack,
  creating,
}: ConfirmStepProps) => {
  return (
    <div className={styles.stepForm}>
      <div className={styles.stepContent}>
        <h3 className={styles.stepTitle}>Bước 3: Xác nhận tạo mẫu</h3>
        <p className={styles.stepDescription}>Kiểm tra lại thông tin trước khi tạo mẫu biểu mẫu</p>

        {/* Summary Cards */}
        <div className={styles.summaryCards}>
          <div className={styles.summaryCard}>
            <div className={styles.summaryIcon}>
              <FileText size={24} />
            </div>
            <div className={styles.summaryContent}>
              <h4 className={styles.summaryLabel}>File gốc</h4>
              <p className={styles.summaryValue}>{fileName}</p>
            </div>
          </div>

          <div className={styles.summaryCard}>
            <div className={styles.summaryIcon}>
              <Check size={24} />
            </div>
            <div className={styles.summaryContent}>
              <h4 className={styles.summaryLabel}>Tên biểu mẫu</h4>
              <p className={styles.summaryValue}>{formName}</p>
            </div>
          </div>

          <div className={styles.summaryCard}>
            <div className={styles.summaryIcon}>
              <Hash size={24} />
            </div>
            <div className={styles.summaryContent}>
              <h4 className={styles.summaryLabel}>Số trường điền</h4>
              <p className={styles.summaryValue}>
                {selectedCount} trường ({'{'}field_1{'}'}, {'{'}field_2{'}'}, ...)
              </p>
            </div>
          </div>

          {description && (
            <div className={styles.summaryCard}>
              <div className={styles.summaryContent}>
                <h4 className={styles.summaryLabel}>Mô tả</h4>
                <p className={styles.summaryValue}>{description}</p>
              </div>
            </div>
          )}
        </div>

        {/* Info Box */}
        <div className={styles.infoBox}>
          <p>
            <strong>Lưu ý:</strong> Sau khi tạo, hệ thống sẽ tự động tạo file DOCX mới với các
            placeholder {'{'}field_1{'}'}, {'{'}field_2{'}'}, ... tại các vị trí bạn đã chọn. File
            này sẽ được lưu vào MinIO và có thể sử dụng để điền thông tin tự động.
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className={styles.stepActions}>
        <button type="button" onClick={onBack} disabled={creating} className={styles.backButton}>
          ← Quay lại
        </button>
        <div className={styles.stepInfo}>Bước 3/3</div>
        <button
          type="button"
          onClick={onConfirm}
          disabled={creating}
          className={styles.confirmButton}
        >
          {creating ? (
            <>
              <div className={styles.spinner} />
              Đang tạo mẫu...
            </>
          ) : (
            <>
              <Check size={16} />
              Xác nhận tạo mẫu
            </>
          )}
        </button>
      </div>
    </div>
  );
};
