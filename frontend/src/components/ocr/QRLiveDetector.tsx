import React, { useRef, useEffect, useState, useCallback } from "react";
import { identifillService } from "../../services/identifillService";

interface QRLiveDetectorProps {
  onQRDetected: (imageData: string) => void;
  onError?: (error: string) => void;
  enabled?: boolean;
}

export const QRLiveDetector: React.FC<QRLiveDetectorProps> = ({
  onQRDetected,
  onError,
  enabled = false,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<number | null>(null);

  const [isScanning, setIsScanning] = useState(false);

  const startQRDetection = useCallback(async () => {
    if (!enabled || !videoRef.current || !canvasRef.current) return;

    try {
      const constraints = {
        video: {
          width: { ideal: 1920, min: 1280 },
          height: { ideal: 1080, min: 720 },
          facingMode: "environment",
          frameRate: { ideal: 30 },
        },
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setIsScanning(true);

        // Start periodic QR scanning (every 500ms)
        intervalRef.current = setInterval(() => {
          scanForQR();
        }, 500);
      }
    } catch (error) {
      onError?.("Không thể truy cập camera: " + (error as Error).message);
    }
  }, [enabled, onError, scanForQR]);

  const scanForQR = useCallback(async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas || video.readyState !== 4) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Capture current frame
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(video, 0, 0);

    const imageData = canvas.toDataURL("image/png");

    try {
      // Quick QR scan without UI blocking
      const result = await identifillService.scanQRCode(imageData);

      if (result.success && result.data) {
        console.log("🎯 QR detected automatically!");
        onQRDetected(imageData);
        stopDetection(); // Stop after first successful detection
      }
    } catch {
      // Silent fail for live detection
      console.log("QR scan attempt failed (silent)");
    }
  }, [onQRDetected]);

  const stopDetection = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    setIsScanning(false);
  }, []);

  useEffect(() => {
    if (enabled) {
      startQRDetection();
    } else {
      stopDetection();
    }

    return () => stopDetection();
  }, [enabled, startQRDetection, stopDetection]);

  if (!enabled) return null;

  return (
    <div className="qr-live-detector">
      <div className="live-detector-container">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="live-detector-video"
        />
        <canvas ref={canvasRef} style={{ display: "none" }} />

        {isScanning && (
          <div className="scanning-overlay">
            <div className="qr-finder">
              <div className="qr-corner qr-corner-tl"></div>
              <div className="qr-corner qr-corner-tr"></div>
              <div className="qr-corner qr-corner-bl"></div>
              <div className="qr-corner qr-corner-br"></div>
            </div>
            <p className="scanning-text">🔍 Đang quét QR tự động...</p>
          </div>
        )}
      </div>
    </div>
  );
};
