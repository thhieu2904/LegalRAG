import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../../ui/card";
import { Button } from "../../ui/button";
import { Input } from "../../ui/input";
import { Label } from "../../ui/label";
import { Textarea } from "../../ui/textarea";
import { Badge } from "../../ui/badge";
import { Alert, AlertDescription } from "../../ui/alert";
import {
  X,
  Save,
  Info,
  Upload,
  FileText,
  Settings,
  Loader,
  Eye,
  Download,
  Trash2,
  Edit,
  Plus,
  CheckCircle,
  Clock,
  AlertCircle,
} from "lucide-react";
import type {
  ModalProps,
  LegalCollection,
  LegalDocument,
  ProcessingStep,
} from "../../../types/admin";
import { getModalSizeClass } from "../../../hooks/useModal";

// ============================================================================
// Base Modal Component
// ============================================================================

interface BaseModalProps extends ModalProps {
  children: React.ReactNode;
  showFooter?: boolean;
  footerContent?: React.ReactNode;
}

export function BaseModal({
  isOpen,
  onClose,
  title,
  size = "md",
  children,
  showFooter = true,
  footerContent,
}: BaseModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card
        className={`w-full ${getModalSizeClass(
          size
        )} max-h-[90vh] overflow-hidden`}
      >
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle className="text-lg font-semibold">{title}</CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-8 w-8 p-0"
          >
            <X className="w-4 h-4" />
          </Button>
        </CardHeader>

        <CardContent className="max-h-[calc(90vh-8rem)] overflow-y-auto">
          {children}
        </CardContent>

        {showFooter && footerContent && (
          <div className="px-6 py-4 border-t bg-gray-50">{footerContent}</div>
        )}
      </Card>
    </div>
  );
}

// ============================================================================
// Collection Modals
// ============================================================================

interface CollectionFormData {
  name: string;
  displayName: string;
  description: string;
  category: LegalCollection["category"];
}

interface CollectionModalProps extends ModalProps<LegalCollection> {
  mode: "add" | "edit";
}

export function CollectionModal({
  isOpen,
  onClose,
  onConfirm,
  data,
  mode,
}: CollectionModalProps) {
  const [formData, setFormData] = React.useState<CollectionFormData>({
    name: data?.name || "",
    displayName: data?.displayName || "",
    description: data?.description || "",
    category: data?.category || "other",
  });

  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = "Tên collection là bắt buộc";
    } else if (!/^[a-z0-9_]+$/.test(formData.name)) {
      newErrors.name =
        "Tên collection chỉ được chứa chữ thường, số và dấu gạch dưới";
    }

    if (!formData.displayName.trim()) {
      newErrors.displayName = "Tên hiển thị là bắt buộc";
    }

    if (!formData.description.trim()) {
      newErrors.description = "Mô tả là bắt buộc";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      if (onConfirm) {
        await onConfirm(formData as unknown as LegalCollection);
      }
      onClose();
    } catch (error) {
      console.error("Error submitting collection:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const footerContent = (
    <div className="flex gap-2">
      <Button onClick={handleSubmit} disabled={isSubmitting} className="flex-1">
        {isSubmitting ? (
          <>
            <Loader className="w-4 h-4 mr-2 animate-spin" />
            {mode === "add" ? "Đang tạo..." : "Đang cập nhật..."}
          </>
        ) : (
          <>
            <Save className="w-4 h-4 mr-2" />
            {mode === "add" ? "Tạo Collection" : "Cập nhật"}
          </>
        )}
      </Button>
      <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
        Hủy
      </Button>
    </div>
  );

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={onClose}
      title={mode === "add" ? "Thêm Collection Mới" : "Chỉnh Sửa Collection"}
      size="lg"
      footerContent={footerContent}
    >
      <div className="space-y-6">
        <Alert>
          <Info className="w-4 h-4" />
          <AlertDescription>
            Collection là nhóm các văn bản pháp luật có cùng chủ đề hoặc lĩnh
            vực.
          </AlertDescription>
        </Alert>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="name">Tên Collection (ID) *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, name: e.target.value }))
              }
              placeholder="VD: luat_dan_su"
              className={errors.name ? "border-red-500" : ""}
            />
            {errors.name && (
              <p className="text-sm text-red-500 mt-1">{errors.name}</p>
            )}
            <p className="text-xs text-gray-500 mt-1">
              Chỉ dùng chữ thường, số và dấu gạch dưới
            </p>
          </div>

          <div>
            <Label htmlFor="category">Loại *</Label>
            <select
              id="category"
              value={formData.category}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  category: e.target.value as LegalCollection["category"],
                }))
              }
              className="w-full p-2 border rounded-md"
            >
              <option value="procedure">Thủ tục</option>
              <option value="law">Luật</option>
              <option value="regulation">Quy định</option>
              <option value="guidance">Hướng dẫn</option>
              <option value="form">Biểu mẫu</option>
              <option value="other">Khác</option>
            </select>
          </div>
        </div>

        <div>
          <Label htmlFor="displayName">Tên hiển thị *</Label>
          <Input
            id="displayName"
            value={formData.displayName}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, displayName: e.target.value }))
            }
            placeholder="VD: Luật Dân sự"
            className={errors.displayName ? "border-red-500" : ""}
          />
          {errors.displayName && (
            <p className="text-sm text-red-500 mt-1">{errors.displayName}</p>
          )}
        </div>

        <div>
          <Label htmlFor="description">Mô tả chi tiết *</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, description: e.target.value }))
            }
            placeholder="Mô tả chi tiết về collection này, mục đích sử dụng..."
            rows={4}
            className={errors.description ? "border-red-500" : ""}
          />
          {errors.description && (
            <p className="text-sm text-red-500 mt-1">{errors.description}</p>
          )}
        </div>
      </div>
    </BaseModal>
  );
}

// ============================================================================
// Document Modals
// ============================================================================

interface DocumentFormData {
  name: string;
  title: string;
  version: string;
  tags: string[];
  documentType: LegalDocument["documentType"];
  documentNumber?: string;
  issuedBy?: string;
  issuedDate?: string;
  effectiveDate?: string;
  autoProcess: boolean;
  autoIndex: boolean;
  notifyOnComplete: boolean;
}

interface DocumentModalProps extends ModalProps<LegalDocument> {
  mode: "add" | "edit" | "view";
  collectionId?: string;
}

export function DocumentModal({
  isOpen,
  onClose,
  onConfirm,
  data,
  mode,
  collectionId,
}: DocumentModalProps) {
  const [formData, setFormData] = React.useState<DocumentFormData>({
    name: data?.name || "",
    title: data?.title || "",
    version: data?.version || "1.0",
    tags: data?.tags || [],
    documentType: data?.documentType || "other",
    documentNumber: data?.documentNumber || "",
    issuedBy: data?.issuedBy || "",
    issuedDate: data?.issuedDate || "",
    effectiveDate: data?.effectiveDate || "",
    autoProcess: true,
    autoIndex: true,
    notifyOnComplete: false,
  });

  const [files, setFiles] = React.useState<{
    source?: File;
    processed?: File;
    form?: File;
  }>({});

  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = "Tên văn bản là bắt buộc";
    }

    if (!formData.title.trim()) {
      newErrors.title = "Tiêu đề là bắt buộc";
    }

    if (mode === "add" && !files.source) {
      newErrors.source = "File nguồn là bắt buộc";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleTagAdd = (tag: string) => {
    if (tag.trim() && !formData.tags.includes(tag.trim())) {
      setFormData((prev) => ({
        ...prev,
        tags: [...prev.tags, tag.trim()],
      }));
    }
  };

  const handleTagRemove = (tagToRemove: string) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags.filter((tag) => tag !== tagToRemove),
    }));
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      const submitData = {
        ...formData,
        collectionId: collectionId || data?.collectionId,
        files,
      };

      if (onConfirm) {
        await onConfirm(submitData as unknown as LegalDocument);
      }
      onClose();
    } catch (error) {
      console.error("Error submitting document:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (mode === "view") {
    return <DocumentViewModal isOpen={isOpen} onClose={onClose} data={data} />;
  }

  const footerContent = (
    <div className="flex gap-2">
      <Button onClick={handleSubmit} disabled={isSubmitting} className="flex-1">
        {isSubmitting ? (
          <>
            <Loader className="w-4 h-4 mr-2 animate-spin" />
            {mode === "add" ? "Đang tải lên..." : "Đang cập nhật..."}
          </>
        ) : (
          <>
            <Upload className="w-4 h-4 mr-2" />
            {mode === "add" ? "Tải lên & Xử lý" : "Cập nhật"}
          </>
        )}
      </Button>
      <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
        Hủy
      </Button>
    </div>
  );

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={onClose}
      title={mode === "add" ? "Tải Lên Văn Bản Mới" : "Chỉnh Sửa Văn Bản"}
      size="xl"
      footerContent={footerContent}
    >
      <div className="space-y-6">
        {/* Document Info Section */}
        <div className="space-y-4">
          <h4 className="font-medium flex items-center gap-2">
            <Info className="w-4 h-4" />
            Thông tin văn bản
          </h4>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">Tên văn bản *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, name: e.target.value }))
                }
                placeholder="VD: Thông tư 01/2023/TT-BNV"
                className={errors.name ? "border-red-500" : ""}
              />
              {errors.name && (
                <p className="text-sm text-red-500 mt-1">{errors.name}</p>
              )}
            </div>

            <div>
              <Label htmlFor="version">Phiên bản</Label>
              <Input
                id="version"
                value={formData.version}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, version: e.target.value }))
                }
                placeholder="VD: 1.0"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="title">Tiêu đề đầy đủ *</Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, title: e.target.value }))
              }
              placeholder="VD: Thông tư về việc hướng dẫn..."
              className={errors.title ? "border-red-500" : ""}
            />
            {errors.title && (
              <p className="text-sm text-red-500 mt-1">{errors.title}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="documentType">Loại văn bản</Label>
              <select
                id="documentType"
                value={formData.documentType}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    documentType: e.target
                      .value as LegalDocument["documentType"],
                  }))
                }
                className="w-full p-2 border rounded-md"
              >
                <option value="law">Luật</option>
                <option value="regulation">Quy định</option>
                <option value="procedure">Thủ tục</option>
                <option value="form">Biểu mẫu</option>
                <option value="guide">Hướng dẫn</option>
                <option value="other">Khác</option>
              </select>
            </div>

            <div>
              <Label htmlFor="documentNumber">Số văn bản</Label>
              <Input
                id="documentNumber"
                value={formData.documentNumber}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    documentNumber: e.target.value,
                  }))
                }
                placeholder="VD: 01/2023/TT-BNV"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label htmlFor="issuedBy">Cơ quan ban hành</Label>
              <Input
                id="issuedBy"
                value={formData.issuedBy}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, issuedBy: e.target.value }))
                }
                placeholder="VD: Bộ Nội vụ"
              />
            </div>

            <div>
              <Label htmlFor="issuedDate">Ngày ban hành</Label>
              <Input
                id="issuedDate"
                type="date"
                value={formData.issuedDate}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    issuedDate: e.target.value,
                  }))
                }
              />
            </div>

            <div>
              <Label htmlFor="effectiveDate">Ngày hiệu lực</Label>
              <Input
                id="effectiveDate"
                type="date"
                value={formData.effectiveDate}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    effectiveDate: e.target.value,
                  }))
                }
              />
            </div>
          </div>

          {/* Tags */}
          <div>
            <Label htmlFor="tags">Tags</Label>
            <div className="flex flex-wrap gap-2 mb-2">
              {formData.tags.map((tag, index) => (
                <Badge
                  key={index}
                  variant="outline"
                  className="flex items-center gap-1"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => handleTagRemove(tag)}
                    className="text-gray-500 hover:text-red-500"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
            </div>
            <Input
              id="tags"
              placeholder="Nhập tag và nhấn Enter"
              onKeyPress={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleTagAdd(e.currentTarget.value);
                  e.currentTarget.value = "";
                }
              }}
            />
          </div>
        </div>

        {/* File Upload Section */}
        {mode === "add" && (
          <div className="space-y-4">
            <h4 className="font-medium flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Tải lên files
            </h4>

            <div className="grid gap-4">
              <div className="p-4 border-2 border-dashed border-gray-300 rounded-lg">
                <Label
                  htmlFor="source-file"
                  className="font-medium text-blue-600"
                >
                  File DOC/DOCX/PDF * (Bắt buộc)
                </Label>
                <Input
                  id="source-file"
                  type="file"
                  accept=".doc,.docx,.pdf"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      setFiles((prev) => ({ ...prev, source: file }));
                    }
                  }}
                  className="mt-2"
                />
                {errors.source && (
                  <p className="text-sm text-red-500 mt-1">{errors.source}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  File gốc sẽ được phân tích và chuyển đổi thành JSON
                </p>
              </div>

              <div className="p-4 border-2 border-dashed border-gray-300 rounded-lg">
                <Label
                  htmlFor="processed-file"
                  className="font-medium text-green-600"
                >
                  File JSON (Tùy chọn)
                </Label>
                <Input
                  id="processed-file"
                  type="file"
                  accept=".json"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      setFiles((prev) => ({ ...prev, processed: file }));
                    }
                  }}
                  className="mt-2"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Nếu không có, hệ thống sẽ tự động tạo từ file gốc
                </p>
              </div>

              <div className="p-4 border-2 border-dashed border-gray-300 rounded-lg">
                <Label
                  htmlFor="form-file"
                  className="font-medium text-purple-600"
                >
                  File Form/Biểu mẫu (Tùy chọn)
                </Label>
                <Input
                  id="form-file"
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      setFiles((prev) => ({ ...prev, form: file }));
                    }
                  }}
                  className="mt-2"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Biểu mẫu, form liên quan đến văn bản
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Processing Options */}
        <div className="space-y-4">
          <h4 className="font-medium flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Tùy chọn xử lý
          </h4>

          <div className="space-y-3">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.autoProcess}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    autoProcess: e.target.checked,
                  }))
                }
              />
              <span className="text-sm">Tự động phân tích và tạo JSON</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.autoIndex}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    autoIndex: e.target.checked,
                  }))
                }
              />
              <span className="text-sm">Đánh index vào vector database</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.notifyOnComplete}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    notifyOnComplete: e.target.checked,
                  }))
                }
              />
              <span className="text-sm">Gửi thông báo khi hoàn thành</span>
            </label>
          </div>
        </div>
      </div>
    </BaseModal>
  );
}

// ============================================================================
// Document View Modal
// ============================================================================

interface DocumentViewModalProps extends ModalProps<LegalDocument> {
  data?: LegalDocument;
}

export function DocumentViewModal({
  isOpen,
  onClose,
  data,
}: DocumentViewModalProps) {
  if (!data) return null;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "processed":
      case "published":
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case "processing":
        return <Loader className="w-4 h-4 text-yellow-600 animate-spin" />;
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Clock className="w-4 h-4 text-gray-600" />;
    }
  };

  const renderProcessingSteps = (steps?: ProcessingStep[]) => {
    if (!steps || steps.length === 0) return null;

    return (
      <div className="space-y-3">
        <h5 className="font-medium text-gray-900">Tiến trình xử lý:</h5>
        {steps.map((step) => (
          <div
            key={step.id}
            className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg"
          >
            {getStatusIcon(step.status)}
            <div className="flex-1">
              <div className="text-sm font-medium">{step.name}</div>
              {step.errorMessage && (
                <div className="text-xs text-red-600 mt-1">
                  {step.errorMessage}
                </div>
              )}
            </div>
            <div className="text-sm text-gray-500">{step.progress}%</div>
          </div>
        ))}
      </div>
    );
  };

  const footerContent = (
    <div className="flex gap-2">
      <Button variant="outline" className="flex-1">
        <Edit className="w-4 h-4 mr-2" />
        Chỉnh sửa
      </Button>
      <Button variant="outline">
        <Download className="w-4 h-4 mr-2" />
        Tải xuống
      </Button>
      <Button variant="outline" className="text-red-600">
        <Trash2 className="w-4 h-4 mr-2" />
        Xóa
      </Button>
    </div>
  );

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={onClose}
      title={`Chi Tiết: ${data.name}`}
      size="xl"
      footerContent={footerContent}
    >
      <div className="space-y-6">
        {/* Basic Info */}
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <Label className="text-sm font-medium text-gray-600">
                Tên văn bản
              </Label>
              <p className="text-sm">{data.name}</p>
            </div>
            <div>
              <Label className="text-sm font-medium text-gray-600">
                Tiêu đề
              </Label>
              <p className="text-sm">{data.title}</p>
            </div>
            <div>
              <Label className="text-sm font-medium text-gray-600">
                Phiên bản
              </Label>
              <p className="text-sm">v{data.version}</p>
            </div>
            <div>
              <Label className="text-sm font-medium text-gray-600">
                Loại văn bản
              </Label>
              <Badge variant="outline">{data.documentType}</Badge>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <Label className="text-sm font-medium text-gray-600">
                Trạng thái
              </Label>
              <div className="flex items-center gap-2">
                {getStatusIcon(data.status)}
                <span className="text-sm">{data.status}</span>
              </div>
            </div>
            <div>
              <Label className="text-sm font-medium text-gray-600">
                Số văn bản
              </Label>
              <p className="text-sm">{data.documentNumber || "Không có"}</p>
            </div>
            <div>
              <Label className="text-sm font-medium text-gray-600">
                Cơ quan ban hành
              </Label>
              <p className="text-sm">{data.issuedBy || "Không có"}</p>
            </div>
            <div>
              <Label className="text-sm font-medium text-gray-600">
                Ngày hiệu lực
              </Label>
              <p className="text-sm">{data.effectiveDate || "Không có"}</p>
            </div>
          </div>
        </div>

        {/* Tags */}
        <div>
          <Label className="text-sm font-medium text-gray-600">Tags</Label>
          <div className="flex flex-wrap gap-2 mt-2">
            {data.tags.map((tag, index) => (
              <Badge key={index} variant="outline">
                {tag}
              </Badge>
            ))}
          </div>
        </div>

        {/* Files */}
        <div>
          <Label className="text-sm font-medium text-gray-600">Files</Label>
          <div className="grid grid-cols-3 gap-4 mt-2">
            <div className="p-3 bg-blue-50 rounded-lg">
              <div className="flex items-center gap-2 text-blue-600 mb-1">
                <FileText className="w-4 h-4" />
                <span className="font-medium">Source</span>
              </div>
              <p className="text-xs text-blue-600">
                {data.sourceFile.filename}
              </p>
            </div>

            {data.processedFile && (
              <div className="p-3 bg-green-50 rounded-lg">
                <div className="flex items-center gap-2 text-green-600 mb-1">
                  <CheckCircle className="w-4 h-4" />
                  <span className="font-medium">JSON</span>
                </div>
                <p className="text-xs text-green-600">
                  {data.processedFile.filename}
                </p>
              </div>
            )}

            {data.formFile && (
              <div className="p-3 bg-purple-50 rounded-lg">
                <div className="flex items-center gap-2 text-purple-600 mb-1">
                  <Plus className="w-4 h-4" />
                  <span className="font-medium">Form</span>
                </div>
                <p className="text-xs text-purple-600">
                  {data.formFile.filename}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Processing Steps */}
        {data.processingSteps && data.processingSteps.length > 0 && (
          <div>{renderProcessingSteps(data.processingSteps)}</div>
        )}

        {/* Statistics */}
        <div className="grid grid-cols-3 gap-4 pt-4 border-t">
          <div className="text-center">
            <div className="text-lg font-semibold text-blue-600">
              {data.viewCount || 0}
            </div>
            <div className="text-xs text-gray-600">Lượt xem</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-green-600">
              {data.downloadCount || 0}
            </div>
            <div className="text-xs text-gray-600">Lượt tải</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-purple-600">
              {data.queryCount || 0}
            </div>
            <div className="text-xs text-gray-600">Lượt truy vấn</div>
          </div>
        </div>
      </div>
    </BaseModal>
  );
}

// ============================================================================
// Delete Confirmation Modal
// ============================================================================

interface DeleteModalProps extends ModalProps {
  itemName: string;
  itemType: "collection" | "document";
}

export function DeleteModal({
  isOpen,
  onClose,
  onConfirm,
  itemName,
  itemType,
}: DeleteModalProps) {
  const [isDeleting, setIsDeleting] = React.useState(false);

  const handleConfirm = async () => {
    setIsDeleting(true);
    try {
      if (onConfirm) {
        await onConfirm(true);
      }
      onClose();
    } catch (error) {
      console.error("Error deleting item:", error);
    } finally {
      setIsDeleting(false);
    }
  };

  const footerContent = (
    <div className="flex gap-2">
      <Button
        variant="destructive"
        onClick={handleConfirm}
        disabled={isDeleting}
        className="flex-1"
      >
        {isDeleting ? (
          <>
            <Loader className="w-4 h-4 mr-2 animate-spin" />
            Đang xóa...
          </>
        ) : (
          <>
            <Trash2 className="w-4 h-4 mr-2" />
            Xác nhận xóa
          </>
        )}
      </Button>
      <Button variant="outline" onClick={onClose} disabled={isDeleting}>
        Hủy
      </Button>
    </div>
  );

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={onClose}
      title={`Xóa ${itemType === "collection" ? "Collection" : "Văn bản"}`}
      size="sm"
      footerContent={footerContent}
    >
      <div className="space-y-4">
        <Alert>
          <AlertCircle className="w-4 h-4" />
          <AlertDescription>
            <strong>Cảnh báo:</strong> Hành động này không thể hoàn tác!
          </AlertDescription>
        </Alert>

        <p className="text-gray-700">
          Bạn có chắc chắn muốn xóa{" "}
          {itemType === "collection" ? "collection" : "văn bản"}{" "}
          <strong>"{itemName}"</strong>?
        </p>

        {itemType === "collection" && (
          <p className="text-sm text-red-600">
            Tất cả văn bản trong collection này cũng sẽ bị xóa.
          </p>
        )}
      </div>
    </BaseModal>
  );
}
