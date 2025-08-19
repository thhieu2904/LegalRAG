import type {
  ClarificationData,
  ClarificationOption,
} from "../../services/chatService";

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
      {clarification.options.map((option) => (
        <div
          key={option.id}
          className={`option-card cursor-pointer border rounded-xl p-4 transition-all duration-200 hover:shadow-md ${
            option.action === "proceed_with_collection"
              ? "border-blue-200 bg-blue-50 hover:bg-blue-100"
              : "border-green-200 bg-green-50 hover:bg-green-100"
          }`}
          onClick={() => onOptionSelect(option)}
        >
          <div className="option-header flex items-center justify-between mb-2">
            <h4 className="font-medium text-gray-800">{option.title}</h4>
            {option.confidence && (
              <span className="confidence-badge px-2 py-1 text-xs rounded-full bg-gray-200 text-gray-700">
                {option.confidence}
              </span>
            )}
          </div>
          {option.description && (
            <p className="option-description text-gray-600 text-sm mb-2">
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
