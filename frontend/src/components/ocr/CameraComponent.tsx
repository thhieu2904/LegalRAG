import React, { useRef, useEffect, useState, useCallback } from "react";
import { Camera, CameraOff, RotateCcw, Check, X } from "lucide-react";

interface CameraComponentProps {
  onCapture: (imageData: string, imageFormat: string) => void;
  onError?: (error: string) => void;
  isActive: boolean;
  onToggle: () => void;
  className?: string;
}

export const CameraComponent: React.FC<CameraComponentProps> = ({
  onCapture,
  onError,
  isActive,
  onToggle,
  className = "",
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [isStreaming, setIsStreaming] = useState(false);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [facingMode, setFacingMode] = useState<"user" | "environment">(
    "environment"
  );

  // Start camera stream
  const startCamera = useCallback(async () => {
    try {
      setError(null);

      const constraints: MediaStreamConstraints = {
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: facingMode,
        },
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        setIsStreaming(true);
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to access camera";
      setError(errorMessage);
      onError?.(errorMessage);
      console.error("Camera error:", err);
    }
  }, [facingMode, onError]);

  // Stop camera stream
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsStreaming(false);
  }, []);

  // Toggle camera
  const toggleCamera = useCallback(() => {
    if (isStreaming) {
      stopCamera();
    } else {
      startCamera();
    }
    onToggle();
  }, [isStreaming, startCamera, stopCamera, onToggle]);

  // Flip camera (front/back)
  const flipCamera = useCallback(() => {
    stopCamera();
    setFacingMode((prev) => (prev === "user" ? "environment" : "user"));
  }, [stopCamera]);

  // Capture photo
  const capturePhoto = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    if (!ctx) return;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw current video frame to canvas
    ctx.drawImage(video, 0, 0);

    // Get image data
    const imageData = canvas.toDataURL("image/jpeg", 0.8);
    setCapturedImage(imageData);

    // Don't call onCapture yet, wait for user confirmation
  }, []);

  // Confirm captured image
  const confirmCapture = useCallback(() => {
    if (capturedImage) {
      onCapture(capturedImage, "jpeg");
      setCapturedImage(null);
      stopCamera();
    }
  }, [capturedImage, onCapture, stopCamera]);

  // Retake photo
  const retakePhoto = useCallback(() => {
    setCapturedImage(null);
  }, []);

  // Start camera when component becomes active
  useEffect(() => {
    if (isActive && !isStreaming && !capturedImage) {
      startCamera();
    } else if (!isActive && isStreaming) {
      stopCamera();
    }
  }, [isActive, isStreaming, capturedImage, startCamera, stopCamera]);

  // Start camera when facing mode changes
  useEffect(() => {
    if (isStreaming) {
      startCamera();
    }
  }, [facingMode, startCamera, isStreaming]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  return (
    <div className={`relative w-full max-w-md mx-auto ${className}`}>
      {/* Video stream */}
      <div className="relative bg-gray-900 rounded-lg overflow-hidden aspect-[4/3]">
        {isStreaming && !capturedImage && (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />
        )}

        {/* Captured image preview */}
        {capturedImage && (
          <img
            src={capturedImage}
            alt="Captured"
            className="w-full h-full object-cover"
          />
        )}

        {/* Error state */}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-800 text-white p-4">
            <div className="text-center">
              <CameraOff className="w-12 h-12 mx-auto mb-2 text-gray-400" />
              <p className="text-sm">{error}</p>
              <button
                onClick={startCamera}
                className="mt-2 px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* Loading state */}
        {!isStreaming && !capturedImage && !error && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-800">
            <div className="text-center text-white">
              <Camera className="w-12 h-12 mx-auto mb-2 text-gray-400" />
              <p className="text-sm">Starting camera...</p>
            </div>
          </div>
        )}

        {/* Viewfinder overlay */}
        {isStreaming && !capturedImage && (
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute inset-4 border-2 border-white border-dashed rounded-lg opacity-50">
              <div className="absolute top-2 left-2 text-white text-xs bg-black bg-opacity-50 px-2 py-1 rounded">
                Align CCCD within frame
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Hidden canvas for capture */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Controls */}
      <div className="mt-4 flex justify-center space-x-4">
        {!capturedImage ? (
          <>
            <button
              onClick={toggleCamera}
              className={`p-3 rounded-full ${
                isStreaming
                  ? "bg-red-600 hover:bg-red-700 text-white"
                  : "bg-green-600 hover:bg-green-700 text-white"
              }`}
              title={isStreaming ? "Stop Camera" : "Start Camera"}
            >
              {isStreaming ? (
                <CameraOff className="w-6 h-6" />
              ) : (
                <Camera className="w-6 h-6" />
              )}
            </button>

            {isStreaming && (
              <>
                <button
                  onClick={flipCamera}
                  className="p-3 bg-gray-600 hover:bg-gray-700 text-white rounded-full"
                  title="Flip Camera"
                >
                  <RotateCcw className="w-6 h-6" />
                </button>

                <button
                  onClick={capturePhoto}
                  className="p-4 bg-blue-600 hover:bg-blue-700 text-white rounded-full"
                  title="Capture Photo"
                >
                  <div className="w-8 h-8 bg-white rounded-full" />
                </button>
              </>
            )}
          </>
        ) : (
          <>
            <button
              onClick={retakePhoto}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg flex items-center space-x-2"
            >
              <X className="w-4 h-4" />
              <span>Retake</span>
            </button>

            <button
              onClick={confirmCapture}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg flex items-center space-x-2"
            >
              <Check className="w-4 h-4" />
              <span>Use Photo</span>
            </button>
          </>
        )}
      </div>
    </div>
  );
};
