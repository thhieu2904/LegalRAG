import React, { useRef, useEffect, useState, useCallback } from "react";
import { Camera, CameraOff, RotateCcw, Check, X } from "lucide-react";

interface CameraComponentProps {
  onCapture: (imageData: string, imageFormat: string) => void;
  onError?: (error: string) => void;
  className?: string;
}

export const CameraComponent: React.FC<CameraComponentProps> = ({
  onCapture,
  onError,
  className = "",
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [isStreaming, setIsStreaming] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [facingMode, setFacingMode] = useState<"user" | "environment">(
    "environment"
  );

  // Start camera stream
  const startCamera = useCallback(async () => {
    // Prevent multiple simultaneous calls
    if (streamRef.current || isStarting) {
      console.log("🔄 Camera already active or starting, skipping...");
      return;
    }

    try {
      setIsStarting(true);
      setError(null);
      console.log("🎥 Requesting camera access...");

      // Check if getUserMedia is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Camera not supported in this browser");
      }

      const constraints: MediaStreamConstraints = {
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: facingMode,
        },
      };

      console.log("📹 Camera constraints:", constraints);

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      console.log("✅ Camera stream obtained");
      console.log("🔍 Video ref exists:", !!videoRef.current);

      if (videoRef.current) {
        console.log("📺 Setting video source...");
        videoRef.current.srcObject = stream;

        try {
          await videoRef.current.play();
          setIsStreaming(true);
          console.log("🎬 Video element started successfully");
        } catch (playError) {
          console.error("❌ Video play failed:", playError);
          throw new Error(`Failed to start video: ${playError}`);
        }
      } else {
        console.error("❌ Video ref is null!");
        throw new Error("Video element not found");
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to access camera";
      setError(errorMessage);
      onError?.(errorMessage);
      console.error("❌ Camera error:", err);
      console.error("❌ Error details:", {
        name: err instanceof Error ? err.name : "Unknown",
        message: errorMessage,
        constraints: {
          video: {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: facingMode,
          },
        },
      });
    } finally {
      setIsStarting(false);
    }
  }, [facingMode, onError, isStarting]);

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
    setIsStarting(false);
    console.log("📴 Camera stopped");
  }, []);

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

  // Manual start camera function (called by button)
  const handleStartCamera = useCallback(() => {
    if (!isStreaming && !isStarting) {
      startCamera();
    }
  }, [isStreaming, isStarting, startCamera]);

  // Manual flip camera function
  const handleFlipCamera = useCallback(async () => {
    if (isStreaming) {
      console.log("🔄 Flipping camera...");
      setFacingMode((prev) => (prev === "user" ? "environment" : "user"));
      // Stop current stream
      stopCamera();
      // Small delay then restart with new facing mode
      setTimeout(() => {
        startCamera();
      }, 300);
    }
  }, [isStreaming, stopCamera, startCamera]);

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
        {/* Debug states */}
        {(() => {
          console.log("🎭 Render states:", {
            isStreaming,
            capturedImage,
            isStarting,
            error,
          });
          return null;
        })()}

        {/* Video element - always rendered but conditionally visible */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`w-full h-full object-cover ${
            isStreaming && !capturedImage ? "block" : "hidden"
          }`}
          onLoadStart={() => console.log("📹 Video loadStart")}
          onCanPlay={() => console.log("📹 Video canPlay")}
          onPlay={() => console.log("📹 Video playing")}
          onError={(e) => console.error("📹 Video error:", e)}
        />

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
                onClick={handleStartCamera}
                className="mt-2 px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* Loading/Starting state */}
        {isStarting && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-800">
            <div className="text-center text-white">
              <Camera className="w-12 h-12 mx-auto mb-2 text-gray-400 animate-pulse" />
              <p className="text-sm">Starting camera...</p>
            </div>
          </div>
        )}

        {/* Idle state - show start button */}
        {!isStreaming && !isStarting && !capturedImage && !error && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-800">
            <div className="text-center text-white">
              <Camera className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <button
                onClick={handleStartCamera}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
              >
                Start Camera
              </button>
              <p className="text-xs mt-2 text-gray-400">
                Click to begin CCCD scanning
              </p>
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
            {/* Start/Stop Camera Button */}
            {!isStreaming && !isStarting ? (
              <button
                onClick={handleStartCamera}
                className="p-3 bg-green-600 hover:bg-green-700 text-white rounded-full"
                title="Start Camera"
              >
                <Camera className="w-6 h-6" />
              </button>
            ) : (
              <button
                onClick={stopCamera}
                className="p-3 bg-red-600 hover:bg-red-700 text-white rounded-full"
                title="Stop Camera"
                disabled={isStarting}
              >
                <CameraOff className="w-6 h-6" />
              </button>
            )}

            {/* Camera Controls - only show when streaming */}
            {isStreaming && (
              <>
                <button
                  onClick={handleFlipCamera}
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
