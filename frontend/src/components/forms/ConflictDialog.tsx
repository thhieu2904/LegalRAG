/**
 * ConflictDialog Component
 * Xử lý conflicts khi quét CCCD mới có dữ liệu trùng với manual input
 */

import React from "react";
import { AlertTriangle, CheckCircle, X } from "lucide-react";
import "./ConflictDialog.css";

export interface ConflictField {
  fieldName: string;
  displayName: string;
  cccdValue: string;
  manualValue: string;
}

export interface ConflictDialogProps {
  isOpen: boolean;
  conflicts: ConflictField[];
  onResolve: (shouldOverride: boolean) => void;
  onClose: () => void;
}

export const ConflictDialog: React.FC<ConflictDialogProps> = ({
  isOpen,
  conflicts,
  onResolve,
  onClose,
}) => {
  if (!isOpen) return null;

  const handleOverride = () => {
    onResolve(true);
  };

  const handleKeepManual = () => {
    onResolve(false);
  };

  const formatFieldName = (fieldName: string): string => {
    return fieldName
      .replace(/^(form_|scan_|placeholder_)/, "") // Bỏ prefix
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  return (
    <div className="conflict-dialog-overlay">
      <div className="conflict-dialog">
        {/* Header */}
        <div className="dialog-header">
          <div className="header-content">
            <AlertTriangle className="warning-icon" size={24} />
            <h3>Phát hiện xung đột dữ liệu</h3>
          </div>
          <button className="close-button" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="dialog-content">
          <p className="dialog-description">
            Bạn đã chỉnh sửa một số thông tin. CCCD vừa quét có dữ liệu khác với
            những gì bạn đã nhập:
          </p>

          <div className="conflicts-list">
            {conflicts.map((conflict) => (
              <div key={conflict.fieldName} className="conflict-item">
                <div className="field-name">
                  📝{" "}
                  {conflict.displayName || formatFieldName(conflict.fieldName)}
                </div>
                <div className="value-comparison">
                  <div className="value-item manual">
                    <span className="value-label">✏️ Bạn đã nhập:</span>
                    <span className="value-text">{conflict.manualValue}</span>
                  </div>
                  <div className="value-item cccd">
                    <span className="value-label">📱 CCCD mới:</span>
                    <span className="value-text">{conflict.cccdValue}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="dialog-question">
            <strong>Bạn muốn sử dụng dữ liệu nào?</strong>
          </div>
        </div>

        {/* Actions */}
        <div className="dialog-actions">
          <button
            className="action-button keep-manual"
            onClick={handleKeepManual}
          >
            <CheckCircle size={16} />
            Giữ lại chỉnh sửa của tôi
          </button>
          <button className="action-button use-cccd" onClick={handleOverride}>
            <AlertTriangle size={16} />
            Sử dụng dữ liệu từ CCCD mới
          </button>
        </div>
      </div>
    </div>
  );
};
