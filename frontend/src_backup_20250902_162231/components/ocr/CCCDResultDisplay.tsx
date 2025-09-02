import React from "react";
import {
  User,
  Calendar,
  MapPin,
  Globe,
  Award,
  AlertTriangle,
} from "lucide-react";
import type { CCCDExtractedData, ConfidenceScores } from "../../types/ocr";

interface CCCDResultDisplayProps {
  extractedData: CCCDExtractedData;
  confidenceScores?: ConfidenceScores | null;
  frontImage?: string | null;
  backImage?: string | null;
}

export const CCCDResultDisplay: React.FC<CCCDResultDisplayProps> = ({
  extractedData,
  confidenceScores,
  frontImage,
  backImage,
}) => {
  const getConfidenceColor = (score?: number) => {
    if (!score) return "text-gray-400";
    if (score >= 0.8) return "text-green-600";
    if (score >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  const getConfidenceLabel = (score?: number) => {
    if (!score) return "Unknown";
    if (score >= 0.8) return "High";
    if (score >= 0.6) return "Medium";
    return "Low";
  };

  const formatConfidence = (score?: number) => {
    return score ? `${(score * 100).toFixed(1)}%` : "N/A";
  };

  const fields = [
    {
      key: "id_number" as keyof CCCDExtractedData,
      label: "ID Number / Số CCCD",
      icon: Award,
      description: "12-digit citizen identity card number",
    },
    {
      key: "full_name" as keyof CCCDExtractedData,
      label: "Full Name / Họ và tên",
      icon: User,
      description: "Full name as shown on the ID card",
    },
    {
      key: "date_of_birth" as keyof CCCDExtractedData,
      label: "Date of Birth / Ngày sinh",
      icon: Calendar,
      description: "Date of birth in DD/MM/YYYY format",
    },
    {
      key: "gender" as keyof CCCDExtractedData,
      label: "Gender / Giới tính",
      icon: User,
      description: "Gender (Nam/Nữ)",
    },
    {
      key: "nationality" as keyof CCCDExtractedData,
      label: "Nationality / Quốc tịch",
      icon: Globe,
      description: "Nationality",
    },
    {
      key: "hometown" as keyof CCCDExtractedData,
      label: "Hometown / Quê quán",
      icon: MapPin,
      description: "Place of origin",
    },
    {
      key: "residence" as keyof CCCDExtractedData,
      label: "Residence / Nơi thường trú",
      icon: MapPin,
      description: "Place of residence",
    },
    {
      key: "issue_date" as keyof CCCDExtractedData,
      label: "Issue Date / Ngày cấp",
      icon: Calendar,
      description: "Date when the ID was issued",
    },
    {
      key: "expiry_date" as keyof CCCDExtractedData,
      label: "Expiry Date / Có giá trị đến",
      icon: Calendar,
      description: "Expiry date of the ID card",
    },
  ];

  const overallConfidence = confidenceScores?.overall_confidence;

  return (
    <div className="space-y-6">
      {/* Overall Confidence */}
      {overallConfidence && (
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-800">
              Overall Confidence
            </h3>
            <div
              className={`text-lg font-bold ${getConfidenceColor(
                overallConfidence
              )}`}
            >
              {formatConfidence(overallConfidence)} (
              {getConfidenceLabel(overallConfidence)})
            </div>
          </div>
          <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                overallConfidence >= 0.8
                  ? "bg-green-500"
                  : overallConfidence >= 0.6
                  ? "bg-yellow-500"
                  : "bg-red-500"
              }`}
              style={{ width: `${overallConfidence * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Extracted Data */}
      <div className="grid gap-4">
        {fields.map(({ key, label, icon: Icon, description }) => {
          const value = extractedData[key];
          const confidence =
            confidenceScores && key in confidenceScores
              ? confidenceScores[key as keyof ConfidenceScores]
              : undefined;

          if (!value) return null;

          return (
            <div
              key={key}
              className="border rounded-lg p-4 bg-white hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-grow">
                  <Icon className="w-5 h-5 text-gray-500 mt-1 flex-shrink-0" />
                  <div className="flex-grow">
                    <h4 className="font-semibold text-gray-800">{label}</h4>
                    <p className="text-sm text-gray-600 mb-2">{description}</p>
                    <div className="text-lg text-gray-900 font-mono bg-gray-100 px-3 py-2 rounded border">
                      {value}
                    </div>
                  </div>
                </div>

                {/* Confidence Score */}
                {confidence !== undefined && (
                  <div className="ml-4 text-right flex-shrink-0">
                    <div className="text-xs text-gray-500 mb-1">Confidence</div>
                    <div
                      className={`text-sm font-semibold ${getConfidenceColor(
                        confidence
                      )}`}
                    >
                      {formatConfidence(confidence)}
                    </div>
                    <div className="text-xs text-gray-400">
                      {getConfidenceLabel(confidence)}
                    </div>
                  </div>
                )}
              </div>

              {/* Low confidence warning */}
              {confidence !== undefined && confidence < 0.6 && (
                <div className="mt-3 flex items-center space-x-2 text-orange-600 bg-orange-50 px-3 py-2 rounded">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  <span className="text-sm">
                    Low confidence - please verify this information manually
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Captured Images */}
      {(frontImage || backImage) && (
        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Captured Images
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {frontImage && (
              <div className="space-y-2">
                <h4 className="font-medium text-gray-700">Front Side</h4>
                <img
                  src={frontImage}
                  alt="CCCD Front"
                  className="w-full rounded border border-gray-300 hover:border-gray-400 transition-colors"
                />
              </div>
            )}

            {backImage && (
              <div className="space-y-2">
                <h4 className="font-medium text-gray-700">Back Side</h4>
                <img
                  src={backImage}
                  alt="CCCD Back"
                  className="w-full rounded border border-gray-300 hover:border-gray-400 transition-colors"
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* JSON Export (for development/debugging) */}
      <details className="border-t pt-6">
        <summary className="cursor-pointer text-gray-600 hover:text-gray-800 font-medium">
          Raw Data (for developers)
        </summary>
        <div className="mt-4 space-y-4">
          <div>
            <h4 className="font-medium text-gray-700 mb-2">Extracted Data</h4>
            <pre className="text-xs bg-gray-100 p-3 rounded border overflow-auto">
              {JSON.stringify(extractedData, null, 2)}
            </pre>
          </div>

          {confidenceScores && (
            <div>
              <h4 className="font-medium text-gray-700 mb-2">
                Confidence Scores
              </h4>
              <pre className="text-xs bg-gray-100 p-3 rounded border overflow-auto">
                {JSON.stringify(confidenceScores, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </details>
    </div>
  );
};
