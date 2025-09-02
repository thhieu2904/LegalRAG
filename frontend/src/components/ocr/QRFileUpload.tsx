import React, { useRef, useState } from "react";
import { Upload, FileImage, AlertCircle } from "lucide-react";

interface QRFileUploadProps {
  onFileSelected: (imageData: string) => void;
  disabled?: boolean;
  className?: string;
}

export const QRFileUpload: React.FC<QRFileUploadProps> = ({
  onFileSelected,
  disabled = false,
  className = "",
}) => {
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (file: File) => {
    if (!file.type.startsWith("image/")) {
      alert("Vui lòng chọn file ảnh (JPG, PNG, etc.)");
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      if (result) {
        onFileSelected(result);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  return (
    <div className={`qr-file-upload ${className}`}>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        style={{ display: "none" }}
        disabled={disabled}
      />

      <div
        className={`upload-zone ${dragOver ? "drag-over" : ""} ${
          disabled ? "disabled" : ""
        }`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={!disabled ? handleButtonClick : undefined}
      >
        <div className="upload-content">
          <div className="upload-icon">
            {dragOver ? <FileImage size={48} /> : <Upload size={48} />}
          </div>

          <div className="upload-text">
            <h3>Tải ảnh QR từ thẻ CCCD</h3>
            <p>
              {dragOver
                ? "Thả ảnh vào đây..."
                : "Click để chọn ảnh hoặc kéo thả ảnh vào đây"}
            </p>

            <div className="upload-tips">
              <div className="tip-item">
                <AlertCircle size={16} />
                <span>Đảm bảo QR code rõ nét và không bị cắt</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
