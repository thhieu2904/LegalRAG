import React, { useState, useCallback, useEffect } from "react";
import { CameraComponent } from "./CameraComponent";
import { CCCDResultDisplay } from "./CCCDResultDisplay";
import { ocrService } from "../../services/ocrService";
import {
  CreditCard,
  Camera,
  CheckCircle,
  AlertCircle,
  Loader,
  RefreshCcw,
} from "lucide-react";
import type {
  CCCDSide,
  ProcessingStatus,
  CCCDExtractedData,
  ConfidenceScores,
} from "../../types/ocr";

interface OCRInterfaceProps {
  onResult?: (data: CCCDExtractedData) => void;
  onError?: (error: string) => void;
  className?: string;
}

export const OCRInterface: React.FC<OCRInterfaceProps> = ({
  onResult,
  onError,
  className = "",
}) => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<
    "front" | "back" | "processing" | "results"
  >("front");
  const [frontImage, setFrontImage] = useState<string | null>(null);
  const [backImage, setBackImage] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [processingStatus, setProcessingStatus] =
    useState<ProcessingStatus>("pending");
  const [extractedData, setExtractedData] = useState<CCCDExtractedData | null>(
    null
  );
  const [confidenceScores, setConfidenceScores] =
    useState<ConfidenceScores | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processingTime, setProcessingTime] = useState<number | null>(null);

  // Create OCR session
  const createSession = useCallback(async () => {
    try {
      setError(null);
      const response = await ocrService.createSession();
      if (response.success && response.data) {
        setSessionId(response.data.session_id);
        return response.data.session_id;
      }
      throw new Error(response.message || "Failed to create session");
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to create session";
      setError(errorMessage);
      onError?.(errorMessage);
      return null;
    }
  }, [onError]);

  // Upload image to backend
  const uploadImage = useCallback(
    async (imageData: string, side: CCCDSide, sessionId: string) => {
      try {
        setIsUploading(true);
        setError(null);

        const response = await ocrService.uploadImage({
          session_id: sessionId,
          side,
          image_data: imageData,
          image_format: "jpeg",
        });

        if (!response.success) {
          throw new Error(response.message || "Failed to upload image");
        }

        return true;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to upload image";
        setError(errorMessage);
        onError?.(errorMessage);
        return false;
      } finally {
        setIsUploading(false);
      }
    },
    [onError]
  );

  // Process OCR
  const processOCR = useCallback(
    async (sessionId: string) => {
      try {
        setError(null);
        setProcessingStatus("processing");

        // Start processing
        const processResponse = await ocrService.processOCR(sessionId, true);
        if (!processResponse.success) {
          throw new Error(
            processResponse.message || "Failed to start processing"
          );
        }

        // Poll for results
        const pollForResults = async (): Promise<void> => {
          try {
            const resultResponse = await ocrService.getResults(sessionId);

            if (resultResponse.success && resultResponse.data) {
              const {
                processing_status,
                extracted_data,
                confidence_scores,
                processing_time,
                error_message,
              } = resultResponse.data;

              setProcessingStatus(processing_status);

              if (processing_status === "completed") {
                setExtractedData(extracted_data || null);
                setConfidenceScores(confidence_scores || null);
                setProcessingTime(processing_time || null);
                setCurrentStep("results");

                if (extracted_data && onResult) {
                  onResult(extracted_data);
                }
              } else if (processing_status === "failed") {
                throw new Error(error_message || "OCR processing failed");
              } else if (processing_status === "processing") {
                // Continue polling
                setTimeout(pollForResults, 2000);
              }
            } else {
              throw new Error(
                resultResponse.message || "Failed to get results"
              );
            }
          } catch (err) {
            const errorMessage =
              err instanceof Error
                ? err.message
                : "Failed to get processing results";
            setError(errorMessage);
            setProcessingStatus("failed");
            onError?.(errorMessage);
          }
        };

        // Start polling after a short delay
        setTimeout(pollForResults, 1000);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to process OCR";
        setError(errorMessage);
        setProcessingStatus("failed");
        onError?.(errorMessage);
      }
    },
    [onResult, onError]
  );

  // Handle image capture
  const handleImageCapture = useCallback(
    async (imageData: string) => {
      // Ensure session exists
      let currentSessionId = sessionId;
      if (!currentSessionId) {
        currentSessionId = await createSession();
        if (!currentSessionId) return;
      }

      const side = currentStep as CCCDSide;
      const success = await uploadImage(imageData, side, currentSessionId);

      if (success) {
        if (side === "front") {
          setFrontImage(imageData);
          setCurrentStep("back");
        } else {
          setBackImage(imageData);
          setCurrentStep("processing");
          // Auto-start processing
          await processOCR(currentSessionId);
        }
      }
    },
    [sessionId, currentStep, createSession, uploadImage, processOCR]
  );

  // Reset to start over
  const resetOCR = useCallback(async () => {
    if (sessionId) {
      try {
        await ocrService.deleteSession(sessionId);
      } catch (err) {
        console.warn("Failed to delete session:", err);
      }
    }

    setSessionId(null);
    setCurrentStep("front");
    setFrontImage(null);
    setBackImage(null);
    setProcessingStatus("pending");
    setExtractedData(null);
    setConfidenceScores(null);
    setError(null);
    setProcessingTime(null);
  }, [sessionId]);

  // Initialize session on mount
  useEffect(() => {
    createSession();
  }, [createSession]);

  return (
    <div className={`max-w-4xl mx-auto p-6 ${className}`}>
      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex items-center justify-center mb-4">
          <CreditCard className="w-12 h-12 text-blue-600 mr-3" />
          <h1 className="text-3xl font-bold text-gray-800">CCCD OCR Scanner</h1>
        </div>
        <p className="text-gray-600">
          Scan your Citizen Identity Card (Căn Cước Công Dân) to extract
          information automatically
        </p>
      </div>

      {/* Progress Indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-center space-x-8">
          {/* Front Side */}
          <div
            className={`flex items-center space-x-2 ${
              currentStep === "front"
                ? "text-blue-600"
                : frontImage
                ? "text-green-600"
                : "text-gray-400"
            }`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center ${
                currentStep === "front"
                  ? "bg-blue-100 border-2 border-blue-600"
                  : frontImage
                  ? "bg-green-100"
                  : "bg-gray-100"
              }`}
            >
              {frontImage ? <CheckCircle className="w-5 h-5" /> : "1"}
            </div>
            <span className="font-medium">Front Side</span>
          </div>

          <div className="w-8 h-1 bg-gray-300 rounded">
            <div
              className={`h-full rounded transition-all duration-300 ${
                frontImage ? "w-full bg-green-500" : "w-0"
              }`}
            />
          </div>

          {/* Back Side */}
          <div
            className={`flex items-center space-x-2 ${
              currentStep === "back"
                ? "text-blue-600"
                : backImage
                ? "text-green-600"
                : "text-gray-400"
            }`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center ${
                currentStep === "back"
                  ? "bg-blue-100 border-2 border-blue-600"
                  : backImage
                  ? "bg-green-100"
                  : "bg-gray-100"
              }`}
            >
              {backImage ? <CheckCircle className="w-5 h-5" /> : "2"}
            </div>
            <span className="font-medium">Back Side</span>
          </div>

          <div className="w-8 h-1 bg-gray-300 rounded">
            <div
              className={`h-full rounded transition-all duration-300 ${
                backImage ? "w-full bg-green-500" : "w-0"
              }`}
            />
          </div>

          {/* Processing */}
          <div
            className={`flex items-center space-x-2 ${
              currentStep === "processing"
                ? "text-blue-600"
                : currentStep === "results"
                ? "text-green-600"
                : "text-gray-400"
            }`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center ${
                currentStep === "processing"
                  ? "bg-blue-100 border-2 border-blue-600"
                  : currentStep === "results"
                  ? "bg-green-100"
                  : "bg-gray-100"
              }`}
            >
              {currentStep === "processing" ? (
                <Loader className="w-5 h-5 animate-spin" />
              ) : currentStep === "results" ? (
                <CheckCircle className="w-5 h-5" />
              ) : (
                "3"
              )}
            </div>
            <span className="font-medium">Processing</span>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-100 border border-red-300 rounded-lg flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-red-800 font-medium">Error</h3>
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        {(currentStep === "front" || currentStep === "back") && (
          <div>
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <Camera className="w-5 h-5 mr-2" />
              Scan {currentStep === "front" ? "Front" : "Back"} Side of CCCD
            </h2>

            {/* Captured Images Preview */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {frontImage && (
                <div className="space-y-2">
                  <p className="text-sm font-medium text-gray-700">
                    Front Side ✓
                  </p>
                  <img
                    src={frontImage}
                    alt="CCCD Front"
                    className="w-full rounded border-2 border-green-200"
                  />
                </div>
              )}

              {backImage && (
                <div className="space-y-2">
                  <p className="text-sm font-medium text-gray-700">
                    Back Side ✓
                  </p>
                  <img
                    src={backImage}
                    alt="CCCD Back"
                    className="w-full rounded border-2 border-green-200"
                  />
                </div>
              )}
            </div>

            <CameraComponent
              onCapture={handleImageCapture}
              onError={(error) => setError(error)}
            />

            {isUploading && (
              <div className="mt-4 flex items-center justify-center space-x-2 text-blue-600">
                <Loader className="w-4 h-4 animate-spin" />
                <span>Uploading image...</span>
              </div>
            )}
          </div>
        )}

        {currentStep === "processing" && (
          <div className="text-center py-12">
            <Loader className="w-16 h-16 mx-auto mb-4 text-blue-600 animate-spin" />
            <h2 className="text-2xl font-semibold mb-2">
              Processing Your CCCD
            </h2>
            <p className="text-gray-600 mb-4">
              Using advanced OCR technology to extract information from your
              images...
            </p>
            <div className="text-sm text-gray-500">
              Status:{" "}
              <span className="capitalize font-medium">{processingStatus}</span>
            </div>
          </div>
        )}

        {currentStep === "results" && extractedData && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold flex items-center">
                <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
                Extraction Results
              </h2>
              <button
                onClick={resetOCR}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg"
              >
                <RefreshCcw className="w-4 h-4" />
                <span>Scan Another</span>
              </button>
            </div>

            {processingTime && (
              <div className="mb-4 text-sm text-gray-600">
                Processing completed in {processingTime.toFixed(2)} seconds
              </div>
            )}

            <CCCDResultDisplay
              extractedData={extractedData}
              confidenceScores={confidenceScores}
              frontImage={frontImage}
              backImage={backImage}
            />
          </div>
        )}
      </div>
    </div>
  );
};
