import React, { useState, useEffect } from "react";
import { Button } from "../../ui/button";
import { Input } from "../../ui/input";
import { Label } from "../../ui/label";
import { Textarea } from "../../ui/textarea";
import { X } from "lucide-react";

interface SimpleQuestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  mode: "add" | "edit";
  questionType: "main" | "variant";
  initialData?: {
    text: string;
  };
  onConfirm: (data: {
    text: string;
    type: "main" | "variant";
  }) => Promise<void>;
}

export const SimpleQuestionModal: React.FC<SimpleQuestionModalProps> = ({
  isOpen,
  onClose,
  mode,
  questionType,
  initialData,
  onConfirm,
}) => {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setText(initialData?.text || "");
    }
  }, [isOpen, initialData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!text.trim()) {
      alert("Vui lòng nhập nội dung câu hỏi");
      return;
    }

    try {
      setLoading(true);
      await onConfirm({
        text: text.trim(),
        type: questionType,
      });
      onClose();
    } catch (error) {
      console.error("Error saving question:", error);
      alert("Có lỗi xảy ra khi lưu câu hỏi");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">
            {mode === "add" ? "Thêm" : "Chỉnh sửa"} câu hỏi{" "}
            {questionType === "main" ? "chính" : "phụ"}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <Label htmlFor="question-text">
                Nội dung câu hỏi {questionType === "main" ? "chính" : "phụ"}
              </Label>
              <Textarea
                id="question-text"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder={`Nhập câu hỏi ${
                  questionType === "main" ? "chính" : "phụ"
                }...`}
                rows={4}
                className="mt-1"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 mt-6">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={loading}
            >
              Hủy
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Đang lưu..." : "Lưu"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
