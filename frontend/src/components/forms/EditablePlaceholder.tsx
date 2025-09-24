/**
 * EditablePlaceholder Component
 * Component cho phép edit inline với Popover UI
 * Được "hydrate" vào các placeholder HTML thông qua createRoot
 */

import React, { useState, useRef, useEffect, useCallback } from "react";
import { Edit3, Save, X } from "lucide-react";
import "./EditablePlaceholder.css";

export interface EditablePlaceholderProps {
  fieldName: string; // Tên field (VD: "scan_ho_ten", "form_ngay_sinh")
  value?: string; // Giá trị hiện tại từ state trung tâm
  placeholder?: string; // Placeholder text trong input
  onSave: (fieldName: string, value: string) => void; // Callback khi save
  cccdValue?: string; // Giá trị từ CCCD scan (readonly reference)
}

export const EditablePlaceholder: React.FC<EditablePlaceholderProps> = ({
  fieldName,
  value = "",
  placeholder = "Nhập thông tin...",
  onSave,
  cccdValue,
}) => {
  const [inputValue, setInputValue] = useState(value);
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);

  const popoverRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Sync input value when prop value changes
  useEffect(() => {
    setInputValue(value);
  }, [value]);

  // Auto focus input when popover opens
  useEffect(() => {
    if (isPopoverOpen && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isPopoverOpen]);

  const handleClick = () => {
    setIsPopoverOpen(true);
  };

  const handleSave = () => {
    onSave(fieldName, inputValue);
    setIsPopoverOpen(false);
  };

  const handleCancel = useCallback(() => {
    setInputValue(value); // Reset to original value
    setIsPopoverOpen(false);
  }, [value]);

  // Close popover when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(event.target as Node)
      ) {
        handleCancel();
      }
    };

    if (isPopoverOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isPopoverOpen, handleCancel]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSave();
    } else if (e.key === "Escape") {
      handleCancel();
    }
  };

  // Display logic - Ưu tiên: Manual Input > CCCD Data > Placeholder
  const displayValue = value || cccdValue || "[Cần điền]";
  const hasValue = Boolean(value);
  const hasCCCDValue = Boolean(cccdValue);

  return (
    <div className="editable-placeholder-container">
      {/* Main display element */}
      <span
        className={`editable-placeholder ${
          hasValue ? "has-value" : "needs-input"
        } ${hasCCCDValue ? "has-cccd" : ""}`}
        onClick={handleClick}
        title={`Click để chỉnh sửa • Field: ${fieldName}${
          cccdValue ? ` • CCCD: ${cccdValue}` : ""
        }`}
      >
        {displayValue}
        <Edit3 className="edit-icon" size={12} />
      </span>

      {/* Popover */}
      {isPopoverOpen && (
        <div className="popover-overlay">
          <div ref={popoverRef} className="popover-content">
            <div className="popover-header">
              <h4>Chỉnh sửa thông tin</h4>
              <button className="close-button" onClick={handleCancel}>
                <X size={14} />
              </button>
            </div>

            <div className="popover-body">
              <label className="field-label">
                {fieldName
                  .replace(/_/g, " ")
                  .replace(/^./, (str) => str.toUpperCase())}
              </label>

              {/* CCCD Reference nếu có */}
              {cccdValue && (
                <div className="cccd-reference">
                  <span className="cccd-label">📱 Từ CCCD:</span>
                  <span className="cccd-value">{cccdValue}</span>
                </div>
              )}

              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder={placeholder}
                className="popover-input"
              />
            </div>

            <div className="popover-footer">
              <button className="cancel-button" onClick={handleCancel}>
                Hủy
              </button>
              <button className="save-button" onClick={handleSave}>
                <Save size={14} />
                Lưu
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
