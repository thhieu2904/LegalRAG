import React, { useState, useEffect } from "react";
import { Button } from "../../ui/button";
import { Input } from "../../ui/input";
import { Label } from "../../ui/label";
import { Textarea } from "../../ui/textarea";
import { Badge } from "../../ui/badge";
import { X, Plus, Trash2 } from "lucide-react";
import type {
  Question,
  Collection,
  Document,
  QuestionCreate,
} from "../../../services/questionsService";

interface AddEditQuestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  mode: "add" | "edit";
  data?: {
    question?: Question;
    collection?: Collection;
    document?: Document;
  };
  onConfirm: (questionData: {
    text: string;
    keywords: string[];
    type: string;
    category: string;
    priority_score: number;
  }) => Promise<void>;
}

export const AddEditQuestionModal: React.FC<AddEditQuestionModalProps> = ({
  isOpen,
  onClose,
  mode,
  data,
  onConfirm,
}) => {
  const [formData, setFormData] = useState({
    text: "",
    keywords: [] as string[],
    type: "variant",
    category: "",
    priority_score: 0.5,
  });
  const [newKeyword, setNewKeyword] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      if (mode === "edit" && data?.question) {
        setFormData({
          text: data.question.text,
          keywords: [...data.question.keywords],
          type: data.question.type,
          category: data.question.category,
          priority_score: data.question.priority_score,
        });
      } else {
        setFormData({
          text: "",
          keywords: [],
          type: "variant",
          category: data?.document?.id || "",
          priority_score: 0.5,
        });
      }
    }
  }, [isOpen, mode, data]);

  const handleAddKeyword = () => {
    if (newKeyword.trim() && !formData.keywords.includes(newKeyword.trim())) {
      setFormData((prev) => ({
        ...prev,
        keywords: [...prev.keywords, newKeyword.trim()],
      }));
      setNewKeyword("");
    }
  };

  const handleRemoveKeyword = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      keywords: prev.keywords.filter((_, i) => i !== index),
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.text.trim()) {
      alert("Vui lòng nhập nội dung câu hỏi");
      return;
    }

    try {
      setLoading(true);
      await onConfirm(formData);
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
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold">
            {mode === "add" ? "Thêm câu hỏi mới" : "Chỉnh sửa câu hỏi"}
          </h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Collection and Document Info */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex gap-4 text-sm">
              <div>
                <span className="font-medium">Collection:</span>
                <span className="ml-2">{data?.collection?.display_name}</span>
              </div>
              <div>
                <span className="font-medium">Document:</span>
                <span className="ml-2">{data?.document?.title}</span>
              </div>
            </div>
          </div>

          {/* Question Text */}
          <div>
            <Label htmlFor="text">Nội dung câu hỏi *</Label>
            <Textarea
              id="text"
              value={formData.text}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, text: e.target.value }))
              }
              placeholder="Nhập nội dung câu hỏi..."
              rows={3}
              required
            />
          </div>

          {/* Type */}
          <div>
            <Label htmlFor="type">Loại câu hỏi</Label>
            <select
              id="type"
              value={formData.type}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, type: e.target.value }))
              }
              className="w-full p-2 border border-gray-300 rounded-md"
            >
              <option value="main">Câu hỏi chính</option>
              <option value="variant">Câu hỏi phụ</option>
              <option value="user_generated">Do người dùng tạo</option>
            </select>
          </div>

          {/* Category */}
          <div>
            <Label htmlFor="category">Danh mục</Label>
            <Input
              id="category"
              value={formData.category}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, category: e.target.value }))
              }
              placeholder="Nhập danh mục..."
            />
          </div>

          {/* Priority Score */}
          <div>
            <Label htmlFor="priority">
              Điểm ưu tiên ({formData.priority_score})
            </Label>
            <input
              type="range"
              id="priority"
              min="0"
              max="1"
              step="0.1"
              value={formData.priority_score}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  priority_score: parseFloat(e.target.value),
                }))
              }
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Thấp (0.0)</span>
              <span>Trung bình (0.5)</span>
              <span>Cao (1.0)</span>
            </div>
          </div>

          {/* Keywords */}
          <div>
            <Label>Từ khóa</Label>
            <div className="flex gap-2 mb-2">
              <Input
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                placeholder="Nhập từ khóa..."
                onKeyPress={(e) =>
                  e.key === "Enter" && (e.preventDefault(), handleAddKeyword())
                }
              />
              <Button type="button" onClick={handleAddKeyword} size="sm">
                <Plus className="w-4 h-4" />
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.keywords.map((keyword, index) => (
                <Badge
                  key={index}
                  variant="secondary"
                  className="flex items-center gap-1"
                >
                  {keyword}
                  <button
                    type="button"
                    onClick={() => handleRemoveKeyword(index)}
                    className="text-gray-500 hover:text-red-600"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button type="button" variant="outline" onClick={onClose}>
              Hủy
            </Button>
            <Button type="submit" disabled={loading}>
              {loading
                ? "Đang lưu..."
                : mode === "add"
                ? "Thêm câu hỏi"
                : "Cập nhật"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

interface QuestionViewModalProps {
  isOpen: boolean;
  onClose: () => void;
  data?: Question;
}

export const QuestionViewModal: React.FC<QuestionViewModalProps> = ({
  isOpen,
  onClose,
  data,
}) => {
  if (!isOpen || !data) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold">Chi tiết câu hỏi</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Status and Type */}
          <div className="flex gap-2">
            <Badge
              className={`${
                data.status === "active"
                  ? "bg-green-100 text-green-800"
                  : data.status === "inactive"
                  ? "bg-yellow-100 text-yellow-800"
                  : "bg-red-100 text-red-800"
              }`}
            >
              {data.status}
            </Badge>
            <Badge
              className={`${
                data.type === "main"
                  ? "bg-blue-100 text-blue-800"
                  : data.type === "variant"
                  ? "bg-purple-100 text-purple-800"
                  : "bg-orange-100 text-orange-800"
              }`}
            >
              {data.type}
            </Badge>
          </div>

          {/* Question Text */}
          <div>
            <Label>Nội dung câu hỏi</Label>
            <div className="p-3 bg-gray-50 rounded-md mt-1">{data.text}</div>
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Collection</Label>
              <div className="text-sm text-gray-600 mt-1">
                {data.collection}
              </div>
            </div>
            <div>
              <Label>Category</Label>
              <div className="text-sm text-gray-600 mt-1">{data.category}</div>
            </div>
            <div>
              <Label>Điểm ưu tiên</Label>
              <div className="text-sm text-gray-600 mt-1">
                {data.priority_score}
              </div>
            </div>
            <div>
              <Label>Source</Label>
              <div className="text-sm text-gray-600 mt-1">{data.source}</div>
            </div>
          </div>

          {/* Keywords */}
          {data.keywords && data.keywords.length > 0 && (
            <div>
              <Label>Từ khóa</Label>
              <div className="flex flex-wrap gap-2 mt-1">
                {data.keywords.map((keyword, index) => (
                  <Badge key={index} variant="outline">
                    {keyword}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Timestamps */}
          {(data.created_at || data.updated_at) && (
            <div className="grid grid-cols-2 gap-4">
              {data.created_at && (
                <div>
                  <Label>Ngày tạo</Label>
                  <div className="text-sm text-gray-600 mt-1">
                    {new Date(data.created_at).toLocaleString("vi-VN")}
                  </div>
                </div>
              )}
              {data.updated_at && (
                <div>
                  <Label>Ngày cập nhật</Label>
                  <div className="text-sm text-gray-600 mt-1">
                    {new Date(data.updated_at).toLocaleString("vi-VN")}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 p-6 border-t">
          <Button onClick={onClose}>Đóng</Button>
        </div>
      </div>
    </div>
  );
};

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  confirmVariant?: "default" | "destructive";
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = "Xác nhận",
  confirmVariant = "default",
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-lg font-semibold">{title}</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-gray-600">{message}</p>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 p-6 border-t">
          <Button variant="outline" onClick={onClose}>
            Hủy
          </Button>
          <Button
            onClick={onConfirm}
            className={
              confirmVariant === "destructive"
                ? "bg-red-600 text-white hover:bg-red-700"
                : ""
            }
          >
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  );
};

export interface QuestionModalsProps {
  questionModal: any;
  viewModal: any;
  deleteModal: any;
  onSaved: () => void;
  onDeleted: () => void;
}

export const QuestionModals: React.FC<QuestionModalsProps> = ({
  questionModal,
  viewModal,
  deleteModal,
  onSaved,
  onDeleted,
}) => {
  return (
    <>
      <AddEditQuestionModal
        isOpen={questionModal.isOpen}
        onClose={questionModal.closeModal}
        mode={questionModal.modalState.type?.includes("add") ? "add" : "edit"}
        data={questionModal.modalState.data}
        onConfirm={async (questionData) => {
          // Handle save logic here
          questionModal.closeModal();
          onSaved();
        }}
      />

      <QuestionViewModal
        isOpen={viewModal.isOpen}
        onClose={viewModal.closeModal}
        data={viewModal.modalState.data}
      />

      <ConfirmModal
        isOpen={deleteModal.isOpen}
        onClose={deleteModal.closeModal}
        onConfirm={async () => {
          // Handle delete logic here
          deleteModal.closeModal();
          onDeleted();
        }}
        title="Xóa câu hỏi"
        message="Bạn có chắc chắn muốn xóa câu hỏi này không?"
        confirmText="Xóa"
        confirmVariant="destructive"
      />
    </>
  );
};
