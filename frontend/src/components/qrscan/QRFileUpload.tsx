import React, { useRef, useState } from "react";
import { Upload, FileImage, AlertCircle } from "lucide-react";
import "./QRFileUpload.css";

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
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (file: File) => {
    setError(null);

    // Validate file type
    if (!file.type.startsWith("image/")) {
      const errorMsg = "Please select an image file (JPG, PNG, etc.)";
      setError(errorMsg);
      return;
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      const errorMsg = "File size must be less than 10MB";
      setError(errorMsg);
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      if (result) {
        onFileSelected(result);
      }
    };

    reader.onerror = () => {
      setError("Failed to read file");
    };

    reader.readAsDataURL(file);
  };

  const handleButtonClick = () => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
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

    if (disabled) return;

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setDragOver(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  return (
    <div className={`qr-file-upload ${className}`}>
      <div
        className={`upload-area ${dragOver ? "drag-over" : ""} ${
          disabled ? "disabled" : ""
        } ${error ? "error" : ""}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleButtonClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          disabled={disabled}
          className="file-input"
        />

        <div className="upload-content">
          <div className="upload-icon">
            {error ? (
              <AlertCircle className="icon error-icon" />
            ) : (
              <FileImage className="icon" />
            )}
          </div>

          <div className="upload-text">
            {error ? (
              <>
                <p className="error-title">Upload Failed</p>
                <p className="error-message">{error}</p>
              </>
            ) : disabled ? (
              <>
                <p className="upload-title">Upload Disabled</p>
                <p className="upload-description">Please wait...</p>
              </>
            ) : (
              <>
                <p className="upload-title">
                  {dragOver ? "Drop image here" : "Upload CCCD Image"}
                </p>
                <p className="upload-description">
                  Drag & drop an image or{" "}
                  <span className="upload-link">click to browse</span>
                </p>
                <p className="upload-formats">
                  Supports: JPG, PNG, WEBP • Max size: 10MB
                </p>
              </>
            )}
          </div>

          <div className="upload-button-wrapper">
            <Upload className="button-icon" />
            <span>Choose File</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="error-details">
          <AlertCircle className="error-detail-icon" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
