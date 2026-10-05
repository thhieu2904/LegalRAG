/**
 * CCCDScanner Component
 *
 * Features:
 * - Upload/capture an image containing an identity-card QR code
 * - Call the QR-only scan API (not OCR)
 * - Display scanned data
 * - Reset functionality
 */

import { useState, useRef, useEffect, useCallback, useId } from 'react';
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
  QrCode,
} from 'lucide-react';
import type { CCCDData } from '../types';
import { captureQrFrame } from '../cameraCapture';
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
  const [capturing, setCapturing] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraDevices, setCameraDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedCameraId, setSelectedCameraId] = useState('');
  const [activeCameraName, setActiveCameraName] = useState('');
  const [cameraListError, setCameraListError] = useState<string | null>(null);
  const cameraSelectId = useId();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const cameraPendingRef = useRef(false);
  const cameraGenerationRef = useRef(0);
  const cameraListGenerationRef = useRef(0);
  const readerRef = useRef<FileReader | null>(null);
  const capturePendingRef = useRef(false);

  // Listing devices does not open the camera or request permission.
  const refreshCameraDevices = useCallback(async () => {
    const generation = ++cameraListGenerationRef.current;
    if (!navigator.mediaDevices?.enumerateDevices) return;
    try {
      const devices = (await navigator.mediaDevices.enumerateDevices())
        .filter((device) => device.kind === 'videoinput' && device.deviceId);
      if (generation !== cameraListGenerationRef.current) return;
      setCameraDevices(devices);
      setCameraListError(null);
      setSelectedCameraId((previous) => devices.some((device) => device.deviceId === previous) ? previous : '');
    } catch {
      if (generation === cameraListGenerationRef.current) {
        setCameraListError('Chưa lấy được danh sách camera. Bấm Làm mới để thử lại.');
      }
    }
  }, []);

  const stopCamera = useCallback(() => {
    cameraGenerationRef.current++;
    cameraPendingRef.current = false;
    capturePendingRef.current = false;
    setCameraStarting(false);
    setCapturing(false);
    readerRef.current?.abort();
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        track.onended = null;
        track.stop();
      });
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setIsCameraActive(false);
    setActiveCameraName('');
  }, []);

  // Start camera stream
  const startCamera = useCallback(async (deviceId = selectedCameraId) => {
    if (cameraPendingRef.current || streamRef.current) return;
    const generation = ++cameraGenerationRef.current;

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraError('Trình duyệt không hỗ trợ camera');
        return;
      }

      setCameraStarting(true);
      cameraPendingRef.current = true;
      setCameraError(null);

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: {
          ...(deviceId ? { deviceId: { exact: deviceId } } : { facingMode: 'environment' }),
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
      });

      if (generation !== cameraGenerationRef.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }

      streamRef.current = stream;
      const track = stream.getVideoTracks()[0];
      if (!track) throw new Error('Thiết bị không cung cấp luồng camera.');
      track.onended = () => {
        if (generation !== cameraGenerationRef.current) return;
        stopCamera();
        setCameraError('Camera đã bị ngắt. Hãy kết nối lại hoặc chọn camera khác.');
        void refreshCameraDevices();
      };
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      if (generation !== cameraGenerationRef.current) {
        stream.getTracks().forEach((item) => item.stop());
        return;
      }
      const actualDeviceId = track.getSettings().deviceId;
      if (actualDeviceId) setSelectedCameraId(actualDeviceId);
      setActiveCameraName(track.label || 'Camera đã chọn');
      setIsCameraActive(true);
      // Permission can reveal additional devices and their names.
      void refreshCameraDevices();
    } catch (error) {
      if (generation !== cameraGenerationRef.current) return;
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      if (videoRef.current) videoRef.current.srcObject = null;
      const err = error as Error;
      const messages: Record<string, string> = {
        NotAllowedError: 'Chưa được cấp quyền camera. Hãy cho phép trang truy cập camera rồi thử lại.',
        NotFoundError: 'Không tìm thấy camera đã chọn. Hãy kết nối camera hoặc chọn nguồn khác.',
        NotReadableError: 'Không mở được camera đã chọn. Hãy kiểm tra ứng dụng webcam đang chạy và camera không bị ứng dụng khác giữ.',
        OverconstrainedError: 'Camera đã chọn không còn sẵn sàng. Bấm Làm mới hoặc chọn nguồn khác.',
      };
      setCameraError(messages[err.name] || err.message || 'Không thể truy cập camera. Vui lòng kiểm tra quyền truy cập.');
      setActiveCameraName('');
      setIsCameraActive(false);
    } finally {
      if (generation === cameraGenerationRef.current) {
        cameraPendingRef.current = false;
        setCameraStarting(false);
      }
    }
  }, [selectedCameraId, stopCamera, refreshCameraDevices]);

  const restartCamera = useCallback(() => {
    void refreshCameraDevices();
    if (streamRef.current) {
      stopCamera();
      void startCamera();
    }
  }, [refreshCameraDevices, startCamera, stopCamera]);

  const changeCamera = (deviceId: string) => {
    const wasActive = !!streamRef.current;
    stopCamera();
    setSelectedCameraId(deviceId);
    setCameraError(null);
    if (wasActive) void startCamera(deviceId);
  };

  const switchCamera = () => {
    if (cameraDevices.length < 2) return;
    const current = cameraDevices.findIndex((device) => device.deviceId === selectedCameraId);
    const nextCamera = cameraDevices[(current + 1) % cameraDevices.length];
    if (nextCamera) changeCamera(nextCamera.deviceId);
  };

  // Capture photo from camera
  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current || !isCameraActive || cameraStarting || scanning || capturePendingRef.current) return;

    const video = videoRef.current;
    const generation = cameraGenerationRef.current;
    const finish = () => {
      if (generation !== cameraGenerationRef.current) return;
      capturePendingRef.current = false;
      setCapturing(false);
    };
    capturePendingRef.current = true;
    setCapturing(true);
    setCameraError(null);
    try {
      captureQrFrame(video, canvasRef.current, (blob) => {
        if (generation !== cameraGenerationRef.current) return;
        if (!blob || blob.size > 10_000_000) {
          finish();
          setCameraError(blob ? 'Ảnh camera quá lớn. Chọn độ phân giải thấp hơn hoặc tải ảnh mã QR lên.' : 'Chưa lấy được ảnh. Hãy thử chụp lại.');
          return;
        }
        const reader = new FileReader();
        readerRef.current?.abort();
        readerRef.current = reader;
        reader.onerror = () => {
          if (generation !== cameraGenerationRef.current) return;
          finish();
          setCameraError('Không đọc được ảnh camera. Hãy thử lại.');
        };
        reader.onload = (e) => {
          if (generation !== cameraGenerationRef.current) return;
          const base64 = e.target?.result as string;
          const base64Data = base64.split(',')[1];
          finish();
          if (base64Data) {
            onScan(base64Data);
          }
        };
        reader.readAsDataURL(blob);
      });
    } catch (error) {
      finish();
      setCameraError(error instanceof Error ? error.message : 'Không lấy được ảnh camera.');
    }
  };

  // Cleanup camera on unmount
  useEffect(() => {
    const generation = cameraGenerationRef;
    const listGeneration = cameraListGenerationRef;
    const reader = readerRef;
    const stream = streamRef;
    return () => {
      generation.current++;
      listGeneration.current++;
      reader.current?.abort();
      stream.current?.getTracks().forEach((track) => {
        track.onended = null;
        track.stop();
      });
      stream.current = null;
    };
  }, []);

  // Handle tab changes
  useEffect(() => {
    if (scanMode !== 'camera') {
      stopCamera();
      return;
    }
    const mediaDevices = navigator.mediaDevices;
    void refreshCameraDevices();
    const handleDeviceChange = () => { void refreshCameraDevices(); };
    mediaDevices?.addEventListener('devicechange', handleDeviceChange);
    return () => { mediaDevices?.removeEventListener('devicechange', handleDeviceChange); };
  }, [scanMode, stopCamera, refreshCameraDevices]);

  // Stop camera once data has been captured
  useEffect(() => {
    if (cccdData) {
      stopCamera();
    }
  }, [cccdData, stopCamera]);

  // Handle file upload
  const handleFileUpload = async (file: File) => {
    if (scanning || capturing) return;
    if (!file.type.startsWith('image/')) {
      alert('Vui lòng chọn file ảnh');
      return;
    }

    // Convert to base64
    readerRef.current?.abort();
    const reader = new FileReader();
    readerRef.current = reader;
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
        <QrCode size={20} />
        <h2 className={styles.title}>Quét QR căn cước</h2>
      </div>

      {!cccdData ? (
        <>
          <div className={styles.modeTabs}>
            <button
              className={`${styles.modeTab} ${scanMode === 'camera' ? styles.modeTabActive : ''}`}
              onClick={() => setScanMode('camera')}
              disabled={scanning || capturing}
            >
              <Camera size={16} />
              <span>Camera QR</span>
            </button>
            <button
              className={`${styles.modeTab} ${scanMode === 'upload' ? styles.modeTabActive : ''}`}
              onClick={() => setScanMode('upload')}
              disabled={scanning || capturing}
            >
              <Upload size={16} />
              <span>Ảnh mã QR</span>
            </button>
          </div>

          {scanMode === 'camera' ? (
            <div className={styles.cameraSection}>
              <div className={styles.cameraHeader}>
                <div>
                  <p className={styles.cameraTitle}>Đọc mã QR</p>
                  <p className={styles.cameraSubtitle}>
                    Đưa mã QR vào khung, giữ thẻ ổn định rồi bấm chụp
                  </p>
                </div>
                <div className={styles.cameraActions}>
                  <button
                    onClick={switchCamera}
                    className={styles.actionButton}
                    disabled={cameraDevices.length < 2 || cameraStarting || capturing || scanning}
                    title={cameraDevices.length < 2 ? 'Cần ít nhất hai camera để chuyển' : 'Chuyển sang camera kế tiếp'}
                  >
                    <RefreshCw size={14} />
                    <span>Đổi camera</span>
                  </button>
                  <button
                    onClick={restartCamera}
                    className={styles.actionButton}
                    disabled={cameraStarting || capturing || scanning}
                  >
                    <RotateCcw size={14} />
                    <span>Làm mới</span>
                  </button>
                </div>
              </div>

              <div className={styles.cameraSource}>
                <label htmlFor={cameraSelectId}>Nguồn camera</label>
                <select
                  id={cameraSelectId}
                  value={selectedCameraId}
                  onChange={(event) => changeCamera(event.target.value)}
                  disabled={cameraStarting || capturing || scanning}
                >
                  <option value="">Tự động (ưu tiên camera sau)</option>
                  {cameraDevices.map((device, index) => (
                    <option key={device.deviceId} value={device.deviceId}>
                      {device.label || `Camera ${index + 1}`}
                    </option>
                  ))}
                </select>
                {activeCameraName && <p className={styles.cameraDeviceHint}>Đang dùng: {activeCameraName}</p>}
                {cameraListError ? (
                  <p className={styles.cameraDeviceHint} role="alert">{cameraListError}</p>
                ) : !isCameraActive && (
                  <p className={styles.cameraDeviceHint}>
                    Mở camera để xem đầy đủ tên thiết bị. Nếu chưa thấy camera mới, bấm Làm mới.
                  </p>
                )}
              </div>

              <div className={styles.cameraViewport}>
                {!isCameraActive && !cameraStarting && !cameraError && (
                  <div className={styles.cameraPlaceholder}>
                    <Camera size={32} />
                    <p>Nhấn "Mở camera" rồi đưa mã QR trên căn cước vào khung</p>
                    <button
                      onClick={() => void startCamera()}
                      className={styles.primaryButton}
                      disabled={cameraStarting}
                    >
                      {cameraStarting ? 'Đang mở camera...' : 'Mở camera'}
                    </button>
                  </div>
                )}

                {cameraError && !isCameraActive && (
                  <div className={styles.cameraError}>
                    <CameraOff size={28} />
                    <p>{cameraError}</p>
                    <button onClick={() => void startCamera()} className={styles.primaryButton}>
                      Thử lại
                    </button>
                  </div>
                )}

                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className={`${styles.cameraVideo} ${isCameraActive ? styles.visible : ''}`}
                />
                <canvas ref={canvasRef} style={{ display: 'none' }} />

                {isCameraActive && (
                  <div className={styles.cameraOverlay}>
                    <div className={styles.overlayFrame}>
                      <div className={styles.overlayCorners}>
                        <span className={styles.corner} />
                        <span className={styles.corner} />
                        <span className={styles.corner} />
                        <span className={styles.corner} />
                      </div>
                      <p className={styles.overlayText}>
                        Căn mã QR vào giữa khung, tránh lóa sáng
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {cameraError && isCameraActive && <p className={styles.cameraDeviceHint} role="alert">{cameraError}</p>}

              <div className={styles.cameraFooter}>
                <button
                  onClick={isCameraActive ? capturePhoto : () => void startCamera()}
                  className={styles.capturePrimary}
                  disabled={cameraStarting || capturing || scanning}
                >
                  {cameraStarting || capturing || scanning ? (
                    <Loader className={styles.spinner} size={18} />
                  ) : (
                    <Camera size={18} />
                  )}
                  <span>
                    {scanning
                      ? 'Đang đọc mã QR...'
                      : capturing
                        ? 'Đang lấy ảnh...'
                        : cameraStarting
                      ? 'Đang mở camera...'
                      : isCameraActive
                        ? 'Chụp & đọc QR'
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
                    <p className={styles.scanningText}>Đang đọc mã QR...</p>
                  </div>
                ) : (
                  <div className={styles.uploadState}>
                    <Upload size={40} className={styles.uploadIcon} />
                    <p className={styles.uploadText}>Kéo thả ảnh có mã QR vào đây</p>
                    <p className={styles.uploadSubtext}>
                      JPG, PNG — mã QR rõ, đủ bốn góc, không lóa
                    </p>
                    <button className={styles.uploadButton}>Chọn ảnh mã QR</button>
                  </div>
                )}
              </div>

              <p className={styles.uploadHint}>
                Gợi ý: Nếu muốn chụp trực tiếp, chuyển sang tab "Camera QR" bên trên.
              </p>
            </>
          )}
        </>
      ) : (
        // Scanned Data Display
        <div className={styles.dataDisplay}>
          <div className={styles.successHeader}>
            <CheckCircle size={20} className={styles.successIcon} />
            <span className={styles.successText}>Đã đọc QR căn cước</span>
          </div>

          <div className={styles.dataGrid}>
            <DataField label="Số CCCD" value={cccdData.field_cccd} />
            <DataField label="Họ và tên" value={cccdData.field_ho_ten} />
            <DataField label="Ngày sinh" value={cccdData.field_ngay_sinh} />
            <DataField label="Giới tính" value={cccdData.field_gioi_tinh} />
            <DataField label="Địa chỉ" value={cccdData.field_dia_chi} fullWidth />
            <DataField label="Ngày cấp" value={cccdData.field_ngay_cap} />
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
        <p className={styles.infoText}>Chỉ đọc mã QR, không đọc chữ trên ảnh. Có thể bỏ qua và nhập bằng tay.</p>
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
