/**
 * CCCDScanner Component
 *
 * Features:
 * - Upload CCCD image
 * - Call scan API
 * - Display scanned data
 * - Reset functionality
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Camera,
  Upload,
  X,
  CheckCircle,
  AlertCircle,
  Loader,
  CameraOff,
  RefreshCw,
  RotateCcw,
} from 'lucide-react';
import type { CCCDData } from '../types';
import styles from './CCCDScanner.module.css';

interface CCCDScannerProps {
  cccdData: CCCDData | null;
  scanning: boolean;
  onScan: (imageData: string) => void;
  onReset: () => void;
}

export const CCCDScanner = ({ cccdData, scanning, onScan, onReset }: CCCDScannerProps) => {
  const [dragActive, setDragActive] = useState(false);
  const [scanMode, setScanMode] = useState<'upload' | 'camera'>('upload');
  const [cameraStarting, setCameraStarting] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [facingMode, setFacingMode] = useState<'environment' | 'user'>('environment');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const previousFacingModeRef = useRef(facingMode);
  const streamRef = useRef<MediaStream | null>(null);

  // Start camera stream
  const startCamera = useCallback(async () => {
    if (cameraStarting || isCameraActive) return;

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraError('Trình duyệt không hỗ trợ camera');
        return;
      }

      setCameraStarting(true);
      setCameraError(null);

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode,
        },
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      setIsCameraActive(true);
    } catch (error) {
      console.error('Camera error:', error);
      const err = error as Error;
      setCameraError(err.message || 'Không thể truy cập camera. Vui lòng kiểm tra quyền truy cập.');
      setIsCameraActive(false);
    } finally {
      setCameraStarting(false);
    }
  }, [cameraStarting, isCameraActive, facingMode]);

  // Stop camera
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsCameraActive(false);
  }, []);

  const restartCamera = useCallback(() => {
    stopCamera();
    startCamera();
  }, [startCamera, stopCamera]);

  const switchFacingMode = () => {
    setFacingMode((prev) => (prev === 'environment' ? 'user' : 'environment'));
  };

  // Capture photo from camera
  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current || !isCameraActive || cameraStarting) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(video, 0, 0);

    // Convert to base64
    canvas.toBlob(
      (blob) => {
        if (!blob) return;

        const reader = new FileReader();
        reader.onload = (e) => {
          const base64 = e.target?.result as string;
          const base64Data = base64.split(',')[1];
          if (base64Data) {
            onScan(base64Data);
            // keep camera active for next capture
          }
        };
        reader.readAsDataURL(blob);
      },
      'image/jpeg',
      0.9
    );
  };

  // Cleanup camera on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  // Handle tab changes
  useEffect(() => {
    if (scanMode === 'camera') {
      startCamera();
    } else {
      stopCamera();
    }
  }, [scanMode, startCamera, stopCamera]);

  // Restart when facing mode changes while camera tab active
  useEffect(() => {
    if (scanMode === 'camera' && previousFacingModeRef.current !== facingMode) {
      restartCamera();
    }
    previousFacingModeRef.current = facingMode;
  }, [facingMode, scanMode, restartCamera]);

  // Stop camera once data has been captured
  useEffect(() => {
    if (cccdData) {
      stopCamera();
    }
  }, [cccdData, stopCamera]);

  // Handle file upload
  const handleFileUpload = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('Vui lòng chọn file ảnh');
      return;
    }

    // Convert to base64
    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = e.target?.result as string;
      // Remove data:image/...;base64, prefix
      const base64Data = base64.split(',')[1];
      if (base64Data) {
        onScan(base64Data);
      }
    };
    reader.readAsDataURL(file);
  };

  // Handle file input change
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  // Handle drag events
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  // Handle drop
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  // Trigger file input
  const handleClickUpload = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Camera size={20} />
        <h2 className={styles.title}>Quét CCCD</h2>
      </div>

      {!cccdData ? (
        <>
          <div className={styles.modeTabs}>
            <button
              className={`${styles.modeTab} ${scanMode === 'camera' ? styles.modeTabActive : ''}`}
              onClick={() => setScanMode('camera')}
            >
              <Camera size={16} />
              <span>Quét bằng camera</span>
            </button>
            <button
              className={`${styles.modeTab} ${scanMode === 'upload' ? styles.modeTabActive : ''}`}
              onClick={() => setScanMode('upload')}
            >
              <Upload size={16} />
              <span>Tải ảnh từ thư viện</span>
            </button>
          </div>

          {scanMode === 'camera' ? (
            <div className={styles.cameraSection}>
              <div className={styles.cameraHeader}>
                <div>
                  <p className={styles.cameraTitle}>Chế độ camera</p>
                  <p className={styles.cameraSubtitle}>
                    Đặt mặt trước CCCD trong khung, đảm bảo ánh sáng tốt
                  </p>
                </div>
                <div className={styles.cameraActions}>
                  <button onClick={switchFacingMode} className={styles.actionButton}>
                    <RefreshCw size={14} />
                    <span>Đổi camera</span>
                  </button>
                  <button onClick={restartCamera} className={styles.actionButton}>
                    <RotateCcw size={14} />
                    <span>Làm mới</span>
                  </button>
                </div>
              </div>

              <div className={styles.cameraViewport}>
                {!isCameraActive && !cameraStarting && !cameraError && (
                  <div className={styles.cameraPlaceholder}>
                    <Camera size={32} />
                    <p>Nhấn "Mở camera" để bắt đầu quét mã QR trên CCCD</p>
                    <button
                      onClick={startCamera}
                      className={styles.primaryButton}
                      disabled={cameraStarting}
                    >
                      {cameraStarting ? 'Đang mở camera...' : 'Mở camera'}
                    </button>
                  </div>
                )}

                {cameraError && (
                  <div className={styles.cameraError}>
                    <CameraOff size={28} />
                    <p>{cameraError}</p>
                    <button onClick={startCamera} className={styles.primaryButton}>
                      Thử lại
                    </button>
                  </div>
                )}

                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  className={`${styles.cameraVideo} ${isCameraActive ? styles.visible : ''}`}
                />
                <canvas ref={canvasRef} style={{ display: 'none' }} />

                {isCameraActive && !cameraError && (
                  <div className={styles.cameraOverlay}>
                    <div className={styles.overlayFrame}>
                      <div className={styles.overlayCorners}>
                        <span className={styles.corner} />
                        <span className={styles.corner} />
                        <span className={styles.corner} />
                        <span className={styles.corner} />
                      </div>
                      <p className={styles.overlayText}>
                        Căn chỉnh CCCD trong khung để quét QR rõ nét
                      </p>
                    </div>
                  </div>
                )}
              </div>

              <div className={styles.cameraFooter}>
                <button
                  onClick={isCameraActive ? capturePhoto : startCamera}
                  className={styles.capturePrimary}
                  disabled={cameraStarting || scanning}
                >
                  {cameraStarting ? (
                    <Loader className={styles.spinner} size={18} />
                  ) : (
                    <Camera size={18} />
                  )}
                  <span>
                    {cameraStarting
                      ? 'Đang mở camera...'
                      : isCameraActive
                        ? 'Chụp & quét'
                        : 'Mở camera'}
                  </span>
                </button>
                <button onClick={stopCamera} className={styles.captureGhost}>
                  <X size={16} />
                  <span>Đóng camera</span>
                </button>
              </div>
            </div>
          ) : (
            <>
              <div
                className={`${styles.uploadArea} ${dragActive ? styles.dragActive : ''} ${scanning ? styles.scanning : ''}`}
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
                onClick={!scanning ? handleClickUpload : undefined}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className={styles.fileInput}
                  disabled={scanning}
                />

                {scanning ? (
                  <div className={styles.scanningState}>
                    <Loader className={styles.spinner} size={40} />
                    <p className={styles.scanningText}>Đang quét CCCD...</p>
                  </div>
                ) : (
                  <div className={styles.uploadState}>
                    <Upload size={40} className={styles.uploadIcon} />
                    <p className={styles.uploadText}>Kéo thả ảnh CCCD vào đây</p>
                    <p className={styles.uploadSubtext}>
                      Hỗ trợ JPG, PNG, độ phân giải &gt;= 1000px
                    </p>
                    <button className={styles.uploadButton}>Chọn ảnh CCCD</button>
                  </div>
                )}
              </div>

              <p className={styles.uploadHint}>
                Gợi ý: Nếu chụp ảnh trực tiếp thuận tiện hơn, chuyển sang tab "Quét bằng camera" bên
                trên.
              </p>
            </>
          )}
        </>
      ) : (
        // Scanned Data Display
        <div className={styles.dataDisplay}>
          <div className={styles.successHeader}>
            <CheckCircle size={20} className={styles.successIcon} />
            <span className={styles.successText}>Đã quét thành công</span>
          </div>

          <div className={styles.dataGrid}>
            <DataField label="Số CCCD" value={cccdData.scan_cccd} />
            <DataField label="Họ và tên" value={cccdData.scan_ho_ten} />
            <DataField label="Ngày sinh" value={cccdData.scan_ngay_sinh} />
            <DataField label="Giới tính" value={cccdData.scan_gioi_tinh} />
            <DataField label="Địa chỉ" value={cccdData.scan_dia_chi} fullWidth />
            <DataField label="Ngày cấp" value={cccdData.scan_ngay_cap} />
          </div>

          <button onClick={onReset} className={styles.resetButton}>
            <X size={16} />
            <span>Quét lại</span>
          </button>
        </div>
      )}

      {/* Info */}
      <div className={styles.info}>
        <AlertCircle size={16} />
        <p className={styles.infoText}>Bạn có thể bỏ qua bước quét CCCD và điền thủ công</p>
      </div>
    </div>
  );
};

// Helper component for displaying data fields
const DataField = ({
  label,
  value,
  fullWidth = false,
}: {
  label: string;
  value: string;
  fullWidth?: boolean;
}) => (
  <div className={`${styles.dataField} ${fullWidth ? styles.fullWidth : ''}`}>
    <span className={styles.dataLabel}>{label}</span>
    <span className={styles.dataValue}>{value}</span>
  </div>
);
