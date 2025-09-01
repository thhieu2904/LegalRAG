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

  return (
    <div className="clarification-options space-y-3 mt-4">
      {/* Add header for question lists */}
      {clarification.options.some(
        (opt) => opt.action === "proceed_with_question"
      ) && (
        <div className="questions-header">
          <h3>📋 Chọn câu hỏi phù hợp</h3>
          <p>Hoặc chọn "Câu hỏi khác..." để tự nhập câu hỏi</p>
        </div>
      )}

      {clarification.options.map((option) => (
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
              ? "question-card question-type border-indigo-200 bg-indigo-50 hover:bg-indigo-100"
              : option.action === "manual_input" ||
                option.title === "Câu hỏi khác..."
              ? "question-card manual-input-card border-gray-200 bg-gray-50 hover:bg-gray-100"
              : "border-green-200 bg-green-50 hover:bg-green-100"
          }`}
          onClick={() => onOptionSelect(option)}
        >
          <div className="option-header flex items-start gap-3 mb-2">
            {option.action === "proceed_with_question" &&
              option.title !== "Câu hỏi khác..." && (
                <div className="question-number flex-shrink-0 w-7 h-7 bg-indigo-500 text-white text-sm font-bold rounded-full flex items-center justify-center">
                  {option.id}
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
              {option.confidence && (
                <span className="confidence-badge px-2 py-1 text-xs rounded-full bg-gray-200 text-gray-700 mt-1 inline-block">
                  {option.confidence}
                </span>
              )}
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
        </div>
      ))}
    </div>
  );
}
