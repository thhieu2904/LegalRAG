import React from "react";
import type { ContextSummary } from "../services/chatService";

interface ContextStatusBarProps {
  contextSummary: ContextSummary | null;
  isLoading?: boolean;
  onResetContext: () => void;
}

export const ContextStatusBar: React.FC<ContextStatusBarProps> = ({
  contextSummary,
  isLoading = false,
  onResetContext,
}) => {
  // Không hiển thị gì nếu không có context summary hoặc đang loading
  if (!contextSummary || isLoading) {
    return null;
  }

  const {
    has_active_context,
    current_collection_display,
    preserved_document,
    context_age_minutes,
  } = contextSummary;

  // Không hiển thị nếu không có active context
  if (!has_active_context) {
    return null;
  }

  const getContextStatusColor = () => {
    if (context_age_minutes <= 2)
      return "bg-green-50 border-green-200 text-green-800";
    if (context_age_minutes <= 5)
      return "bg-yellow-50 border-yellow-200 text-yellow-800";
    return "bg-orange-50 border-orange-200 text-orange-800";
  };

  const getContextStatusText = () => {
    if (preserved_document) {
      return `Đang tập trung vào: ${current_collection_display} - ${preserved_document}`;
    }
    return `Đang tập trung vào: ${current_collection_display}`;
  };

  const getAgeText = () => {
    if (context_age_minutes === 0) return "vừa xong";
    if (context_age_minutes === 1) return "1 phút trước";
    return `${context_age_minutes} phút trước`;
  };

  return (
    <div
      className={`flex items-center justify-between p-3 mb-4 border rounded-lg ${getContextStatusColor()}`}
    >
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <svg
            className="w-5 h-5 text-current"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span className="font-medium text-sm">{getContextStatusText()}</span>
        </div>
        <span className="text-xs opacity-75">({getAgeText()})</span>
      </div>

      <button
        onClick={onResetContext}
        className="px-3 py-1 text-xs font-medium text-current border border-current rounded-md hover:bg-current hover:text-white transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-current focus:ring-opacity-50"
        title="Xóa ngữ cảnh và bắt đầu lại"
      >
        Bắt đầu lại
      </button>
    </div>
  );
};

export default ContextStatusBar;
