import React, { useRef, useEffect, useState, useCallback } from "react";
import { Camera, CameraOff, RotateCcw } from "lucide-react";
import "./CameraComponent.css";

interface CameraComponentProps {
  onImageCapture: (imageData: string) => void;
  onError?: (error: string) => void;
  isCapturing?: boolean;
  captureButtonText?: string;
  className?: string;
}

export const CameraComponent: React.FC<CameraComponentProps> = ({
  onImageCapture,
  onError,
  isCapturing = false,
  captureButtonText = "Capture",
  className = "",
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const isStartingRef = useRef(false);

  const [isStreaming, setIsStreaming] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cameraStarted, setCameraStarted] = useState(false);
  const [facingMode, setFacingMode] = useState<"user" | "environment">(
    "environment"
  );

  // Stop camera stream
  const stopCamera = useCallback(() => {
    console.log("🛑 Stopping camera...");

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        track.stop();
        console.log(`🔇 Stopped ${track.kind} track`);
      });
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsStreaming(false);
    setError(null);
    setCameraStarted(false);
    isStartingRef.current = false;
    console.log("✅ Camera stopped");
  }, []);

  // Start camera stream - simplified version without dependency issues
  const startCamera = useCallback(async () => {
    // Prevent multiple simultaneous starts
    if (streamRef.current || isStartingRef.current) {
      console.log("🔄 Camera already active or starting, skipping...");
      return;
    }

    try {
      isStartingRef.current = true;
      setIsStarting(true);
      setError(null);
      console.log("🎥 Requesting camera access...");

      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Camera not supported in this browser");
      }

      const constraints: MediaStreamConstraints = {
        video: {
          width: { ideal: 1920, min: 1280 },
          height: { ideal: 1080, min: 720 },
          facingMode: facingMode,
        },
      };

      console.log("📱 Camera constraints:", constraints);
      const stream = await navigator.mediaDevices.getUserMedia(constraints);

      // Double-check we haven't been stopped while waiting
      if (!isStartingRef.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }

      streamRef.current = stream;
      console.log("✅ Camera stream obtained");

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setIsStreaming(true);
        setCameraStarted(true);
        console.log("🎬 Camera streaming started");
      }
    } catch (err: unknown) {
      const error = err as Error;
      console.error("❌ Camera access failed:", error);
      let errorMessage = "Failed to access camera";

      if (
        error.name === "NotAllowedError" ||
        error.name === "PermissionDeniedError"
      ) {
        errorMessage =
          "Camera permission denied. Please allow camera access and try again.";
      } else if (
        error.name === "NotFoundError" ||
        error.name === "DevicesNotFoundError"
      ) {
        errorMessage =
          "No camera found. Please connect a camera and try again.";
      } else if (
        error.name === "NotReadableError" ||
        error.name === "TrackStartError"
      ) {
        errorMessage =
          "Camera is being used by another application. Please close other apps and try again.";
      } else if (
        error.name === "OverconstrainedError" ||
        error.name === "ConstraintNotSatisfiedError"
      ) {
        errorMessage =
          "Camera does not meet requirements. Trying with basic settings...";
        // Try with basic constraints as fallback
        try {
          const basicStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: facingMode },
          });

          if (!isStartingRef.current) {
            basicStream.getTracks().forEach((track) => track.stop());
            return;
          }

          streamRef.current = basicStream;
          if (videoRef.current) {
            videoRef.current.srcObject = basicStream;
            await videoRef.current.play();
            setIsStreaming(true);
            setCameraStarted(true);
            console.log("🎬 Camera streaming started with basic settings");
            return;
          }
        } catch {
          errorMessage = "Camera configuration not supported.";
        }
      } else if (error.message) {
        errorMessage = error.message;
      }

      setError(errorMessage);
      // Call onError if provided, but don't make it a dependency to avoid loops
      if (onError) {
        onError(errorMessage);
      }
    } finally {
      isStartingRef.current = false;
      setIsStarting(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [facingMode]); // onError intentionally excluded to prevent infinite loops

  // Capture image from video stream
  const captureImage = useCallback(() => {
    if (
      !videoRef.current ||
      !canvasRef.current ||
      !isStreaming ||
      isCapturing
    ) {
      console.log("❌ Cannot capture: missing refs or not streaming");
      return;
    }

    try {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");

      if (!ctx) {
        throw new Error("Could not get canvas context");
      }

      // Set canvas size to match video dimensions
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      console.log(`📸 Capturing image: ${canvas.width}x${canvas.height}`);

      // Draw the video frame to canvas
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert to data URL (base64)
      const imageData = canvas.toDataURL("image/jpeg", 0.9);
      console.log(`📷 Image captured: ${imageData.length} characters`);

      setCapturedImage(imageData);
      onImageCapture(imageData);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to capture image";
      console.error("❌ Capture failed:", errorMessage);
      setError(errorMessage);
      if (onError) {
        onError(errorMessage);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isStreaming, isCapturing, onImageCapture]); // onError intentionally excluded

  // Switch between front and back camera
  const switchCamera = useCallback(async () => {
    if (isStartingRef.current) return;

    console.log("🔄 Switching camera...");
    stopCamera();

    // Wait a bit for camera to stop completely
    await new Promise((resolve) => setTimeout(resolve, 200));

    setFacingMode((current) => (current === "user" ? "environment" : "user"));

    // Start with new facing mode after state update
    setTimeout(() => {
      if (!capturedImage) {
        startCamera();
      }
    }, 100);
  }, [stopCamera, startCamera, capturedImage]);

  // Reset captured image
  const resetCapture = useCallback(() => {
    setCapturedImage(null);
    setError(null);
    // Restart camera when resetting capture
    if (!isStreaming && !isStartingRef.current) {
      startCamera();
    }
  }, [isStreaming, startCamera]);

  // Single useEffect - only mount and unmount (no auto-start)
  useEffect(() => {
    return () => {
      console.log("🧹 Component unmounting, cleaning up...");
      // Cleanup streams on unmount
      isStartingRef.current = false;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
      setIsStreaming(false);
    };
  }, []); // Empty dependency array - only run on mount/unmount

  return (
    <div className={`camera-component ${className}`}>
      {capturedImage ? (
        /* Preview captured image */
        <div className="capture-preview">
          <img src={capturedImage} alt="Captured" className="captured-image" />
          <div className="preview-overlay">
            <div className="preview-actions">
              <button
                onClick={resetCapture}
                className="action-button secondary"
                disabled={isCapturing}
              >
                <RotateCcw className="button-icon" />
                Retake
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* Live camera view */
        <>
          <div className="camera-viewport">
            {/* Show start camera button if not started */}
            {!cameraStarted && !error && (
              <div className="camera-start">
                <Camera className="start-icon" />
                <p>Sẵn sàng để quét</p>
                <button
                  onClick={startCamera}
                  className="start-camera-button"
                  disabled={isStarting}
                >
                  {isStarting ? "Starting..." : "🎥 Mở Camera"}
                </button>
              </div>
            )}

            {error && (
              <div className="camera-error">
                <CameraOff className="error-icon" />
                <p>{error}</p>
                <button onClick={startCamera} className="retry-button">
                  Thử lại
                </button>
              </div>
            )}

            {isStarting && (
              <div className="camera-loading">
                <Camera className="loading-icon" />
                <p>Đang khởi động camera...</p>
              </div>
            )}

            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className={`camera-video ${isStreaming ? "active" : "hidden"}`}
            />

            {/* Camera viewfinder overlay */}
            {isStreaming && !error && (
              <div className="viewfinder-overlay">
                <div className="viewfinder-frame">
                  <div className="frame-corner frame-corner-tl"></div>
                  <div className="frame-corner frame-corner-tr"></div>
                  <div className="frame-corner frame-corner-bl"></div>
                  <div className="frame-corner frame-corner-br"></div>
                </div>
                <div className="viewfinder-guide">
                  <p>Position your CCCD within the frame</p>
                  <p>Ensure QR code is visible and clear</p>
                </div>
              </div>
            )}
          </div>

          {/* Camera controls */}
          <div className="camera-controls">
            <button
              onClick={switchCamera}
              className="control-button"
              disabled={!isStreaming || isStarting}
              title="Switch camera"
            >
              <RotateCcw className="button-icon" />
            </button>

            <button
              onClick={captureImage}
              className="capture-button"
              disabled={!isStreaming || isCapturing || isStarting}
            >
              <Camera className="button-icon" />
              {captureButtonText}
            </button>

            <button
              onClick={stopCamera}
              className="control-button"
              disabled={!isStreaming}
              title="Stop camera"
            >
              <CameraOff className="button-icon" />
            </button>
          </div>
        </>
      )}

      {/* Hidden canvas for image capture */}
      <canvas ref={canvasRef} style={{ display: "none" }} />
    </div>
  );
};
