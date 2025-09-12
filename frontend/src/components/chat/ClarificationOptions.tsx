import type {
  ClarificationData,
  ClarificationOption,
} from "../../services/chatService";
import "../../styles/components/question-list.css";

interface ClarificationOptionsProps {
  clarification: ClarificationData;
  onOptionSelect: (option: ClarificationOption) => void;
}

export function ClarificationOptions({
  clarification,
  onOptionSelect,
}: ClarificationOptionsProps) {
  if (!clarification?.options || clarification.options.length === 0) {
    return null;
  }

  // 🔥 NEW: Check if this is an enhanced clarification with similarity scores
  const hasSimilarityScores = clarification.options.some(
    (opt) => opt.similarity_percent !== undefined && opt.similarity_percent > 0
  );

  // 🔥 NEW: Check clarification style for enhanced features
  const isEnhancedStyle =
    clarification.style?.includes("similarity") ||
    clarification.style?.includes("enhanced") ||
    hasSimilarityScores;

  // 🔥 NEW: Sort options by similarity if available
  const sortedOptions = hasSimilarityScores
    ? [...clarification.options].sort((a, b) => {
        const aScore = a.similarity_percent || 0;
        const bScore = b.similarity_percent || 0;
        return bScore - aScore; // Descending order
      })
    : clarification.options;

  return (
    <div className="clarification-options space-y-3 mt-4">
      {/* 🔥 ENHANCED: Smart header based on clarification type */}
      {clarification.options.some(
        (opt) => opt.action === "proceed_with_question"
      ) && (
        <div className="questions-header">
          <h3>
            📋{" "}
            {hasSimilarityScores
              ? "Câu hỏi được sắp xếp theo độ phù hợp"
              : "Chọn câu hỏi phù hợp"}
          </h3>
          <p>
            {hasSimilarityScores
              ? "Câu hỏi có % cao hơn phù hợp với câu hỏi của bạn hơn"
              : 'Hoặc chọn "Câu hỏi khác..." để tự nhập câu hỏi'}
          </p>
          {/* 🔥 NEW: Show sorting info */}
          {clarification.sorting_note && (
            <p className="text-xs text-gray-500 mt-1">
              ℹ️ {clarification.sorting_note}
            </p>
          )}
        </div>
      )}

      {/* 🔥 ENHANCED: Render sorted options with similarity indicators */}
      {sortedOptions.map((option, index) => (
        <div
          key={option.id}
          className={`option-card cursor-pointer border rounded-xl p-4 transition-all duration-200 hover:shadow-md ${
            option.action === "proceed_with_collection"
              ? "border-blue-200 bg-blue-50 hover:bg-blue-100"
              : option.action === "show_document_questions"
              ? "border-purple-200 bg-purple-50 hover:bg-purple-100"
              : option.action === "proceed_with_document"
              ? "border-orange-200 bg-orange-50 hover:bg-orange-100"
              : option.action === "proceed_with_question"
              ? `question-card question-type border-indigo-200 bg-indigo-50 hover:bg-indigo-100 ${
                  hasSimilarityScores && index === 0
                    ? "ring-2 ring-indigo-300"
                    : ""
                }`
              : option.action === "manual_input" ||
                option.title === "Câu hỏi khác..."
              ? "question-card manual-input-card border-gray-200 bg-gray-50 hover:bg-gray-100"
              : "border-green-200 bg-green-50 hover:bg-green-100"
          }`}
          onClick={() => onOptionSelect(option)}
        >
          <div className="option-header flex items-start gap-3 mb-2">
            {/* 🔥 ENHANCED: Question number with similarity ranking indicator */}
            {option.action === "proceed_with_question" &&
              option.title !== "Câu hỏi khác..." && (
                <div
                  className={`question-number flex-shrink-0 w-7 h-7 text-white text-sm font-bold rounded-full flex items-center justify-center ${
                    hasSimilarityScores && index === 0
                      ? "bg-gradient-to-r from-indigo-500 to-purple-600 ring-2 ring-purple-300"
                      : "bg-indigo-500"
                  }`}
                >
                  {hasSimilarityScores && index === 0 ? "⭐" : option.id}
                </div>
              )}
            {(option.action === "manual_input" ||
              option.title === "Câu hỏi khác...") && (
              <div className="manual-icon flex-shrink-0 w-7 h-7 bg-gray-400 text-white text-sm rounded-full flex items-center justify-center">
                ✏️
              </div>
            )}
            <div className="flex-1">
              <h4
                className={`question-title font-medium text-gray-800 ${
                  option.action === "proceed_with_question"
                    ? "text-base leading-relaxed"
                    : ""
                }`}
              >
                {option.title}
              </h4>

              {/* 🔥 ENHANCED: Display multiple confidence/similarity metrics */}
              <div className="confidence-metrics flex flex-wrap gap-2 mt-1">
                {/* Original confidence badge */}
                {option.confidence && (
                  <span className="confidence-badge px-2 py-1 text-xs rounded-full bg-gray-200 text-gray-700">
                    {option.confidence}
                  </span>
                )}

                {/* 🔥 NEW: Confidence percentage from new schema */}
                {option.confidence_percent !== undefined &&
                  option.confidence_percent !== null &&
                  option.confidence_percent > 0 && (
                    <span
                      className={`confidence-badge px-2 py-1 text-xs rounded-full font-medium ${
                        option.confidence_percent >= 90
                          ? "bg-green-100 text-green-800"
                          : option.confidence_percent >= 70
                          ? "bg-blue-100 text-blue-800"
                          : option.confidence_percent >= 50
                          ? "bg-yellow-100 text-yellow-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      📊 {option.confidence_percent}%
                    </span>
                  )}

                {/* 🔥 LEGACY: Similarity percentage badge for backward compatibility */}
                {option.similarity_percent !== undefined &&
                  option.similarity_percent > 0 && (
                    <span
                      className={`similarity-badge px-2 py-1 text-xs rounded-full font-medium ${
                        option.similarity_percent >= 90
                          ? "bg-green-100 text-green-800"
                          : option.similarity_percent >= 70
                          ? "bg-blue-100 text-blue-800"
                          : option.similarity_percent >= 50
                          ? "bg-yellow-100 text-yellow-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      🎯 {option.similarity_percent}% phù hợp
                    </span>
                  )}

                {/* 🔥 NEW: Relevance percentage for categories */}
                {option.relevance_percent !== undefined &&
                  option.relevance_percent > 0 && (
                    <span className="relevance-badge px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800">
                      📊 {option.relevance_percent}% liên quan
                    </span>
                  )}

                {/* 🔥 NEW: Router confidence for multiple choice */}
                {option.router_confidence !== undefined &&
                  option.router_confidence > 0 && (
                    <span className="router-badge px-2 py-1 text-xs rounded-full bg-indigo-100 text-indigo-800">
                      🤖 {option.router_confidence}%
                    </span>
                  )}

                {/* 🔥 NEW: Best match indicator */}
                {hasSimilarityScores &&
                  index === 0 &&
                  option.similarity_percent &&
                  option.similarity_percent > 80 && (
                    <span className="best-match-badge px-2 py-1 text-xs rounded-full bg-gradient-to-r from-purple-100 to-pink-100 text-purple-800 font-medium">
                      ⭐ Khuyến nghị
                    </span>
                  )}
              </div>
            </div>
          </div>

          {option.description && (
            <p
              className={`question-description text-gray-600 text-sm mb-2 ${
                option.action === "proceed_with_question" ? "ml-10" : ""
              }`}
            >
              {option.description}
            </p>
          )}

          {option.examples && option.examples.length > 0 && (
            <div className="option-examples text-xs text-gray-500">
              <span className="font-medium">Ví dụ:</span>{" "}
              {option.examples.join(", ")}
            </div>
          )}

          {/* 🔥 NEW: Enhanced info display for debugging/advanced users */}
          {(option.procedure || option.document) && (
            <div className="enhanced-info text-xs text-gray-500 mt-2 border-t pt-2">
              {option.procedure && (
                <span className="procedure-info">
                  📋 Thủ tục: {option.procedure}
                </span>
              )}
              {option.document && (
                <span className="document-info ml-3">
                  📄 Tài liệu: {option.document}
                </span>
              )}
            </div>
          )}
        </div>
      ))}

      {/* 🔥 NEW: Enhanced clarification footer with additional info */}
      {isEnhancedStyle && (
        <div className="enhanced-footer text-xs text-gray-500 text-center py-2 border-t">
          <span className="enhanced-indicator">
            🚀 Được tối ưu bằng AI với embedding similarity
          </span>
        </div>
      )}

      {/* 🔥 NEW: Additional help from backend */}
      {clarification.additional_help && (
        <div className="additional-help bg-blue-50 border border-blue-200 rounded-lg p-3 mt-4">
          <div className="flex items-start gap-2">
            <span className="text-blue-500 text-sm">💡</span>
            <p className="text-blue-700 text-sm">
              {clarification.additional_help}
            </p>
          </div>
        </div>
      )}

      {/* 🔥 NEW: Manual input area if required */}
      {clarification.show_manual_input && (
        <div className="manual-input-area bg-gray-50 border border-gray-200 rounded-lg p-4 mt-4">
          <label
            htmlFor="manual-input"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Hoặc mô tả chi tiết câu hỏi của bạn:
          </label>
          <textarea
            id="manual-input"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows={3}
            placeholder={
              clarification.manual_input_placeholder ||
              "Mô tả chi tiết câu hỏi của bạn..."
            }
          />
          <button
            className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            onClick={() => {
              const textarea = document.getElementById(
                "manual-input"
              ) as HTMLTextAreaElement;
              if (textarea && textarea.value.trim()) {
                onOptionSelect({
                  id: "manual_input",
                  title: "Câu hỏi tự nhập",
                  description: textarea.value,
                  action: "manual_input",
                  question_text: textarea.value,
                });
              }
            }}
          >
            Gửi câu hỏi
          </button>
        </div>
      )}
    </div>
  );
}
