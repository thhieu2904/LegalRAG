/**
 * 📝 QUESTIONS EDITOR COMPONENT
 * Component để edit/update questions và variants với rebuild trigger
 */

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../../ui/card";
import { Button } from "../../ui/button";
import { Input } from "../../ui/input";
import { Badge } from "../../ui/badge";
import { Textarea } from "../../ui/textarea";
import {
  Save,
  X,
  Plus,
  Trash2,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Loader2,
  Zap,
} from "lucide-react";
import { updateQuestions, getRebuildStatus } from "../../../api/admin-api";

interface QuestionsEditorProps {
  collection: string;
  docId: string;
  documentTitle: string;
  currentMainQuestion: string;
  currentVariants: string[];
  onSaveSuccess: () => void;
  onCancel: () => void;
}

export default function QuestionsEditor({
  collection,
  docId,
  documentTitle,
  currentMainQuestion,
  currentVariants,
  onSaveSuccess,
  onCancel,
}: QuestionsEditorProps) {
  const [mainQuestion, setMainQuestion] = useState(currentMainQuestion);
  const [variants, setVariants] = useState<string[]>(currentVariants);
  const [newVariant, setNewVariant] = useState("");

  // Modal states
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [saveMode, setSaveMode] = useState<"save-only" | "save-and-rebuild">(
    "save-only"
  );

  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [rebuildStatus, setRebuildStatus] = useState<{
    triggered: boolean;
    pid?: number;
    progress?: number;
  } | null>(null);

  const hasChanges =
    mainQuestion !== currentMainQuestion ||
    JSON.stringify(variants) !== JSON.stringify(currentVariants);

  const handleAddVariant = () => {
    if (newVariant.trim()) {
      setVariants([...variants, newVariant.trim()]);
      setNewVariant("");
    }
  };

  const handleRemoveVariant = (index: number) => {
    setVariants(variants.filter((_, i) => i !== index));
  };

  const handleUpdateVariant = (index: number, value: string) => {
    const updated = [...variants];
    updated[index] = value;
    setVariants(updated);
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setSaveError(null);
      setSaveSuccess(false);
      setRebuildStatus(null);

      console.log(`💾 Saving questions for ${collection}/${docId}`);

      const result = await updateQuestions(
        collection,
        docId,
        mainQuestion,
        variants,
        triggerRebuild
      );

      console.log("✅ Save successful:", result);
      setSaveSuccess(true);

      if (result.rebuild_status?.triggered) {
        setRebuildStatus({
          triggered: true,
          pid: result.rebuild_status.pid,
          progress: 0,
        });

        // Poll rebuild status
        const pollInterval = setInterval(async () => {
          try {
            const status = await getRebuildStatus();
            setRebuildStatus({
              triggered: true,
              progress: status.progress,
            });

            if (status.status === "success" || status.status === "failed") {
              clearInterval(pollInterval);
            }
          } catch (err) {
            console.error("Error polling rebuild status:", err);
            clearInterval(pollInterval);
          }
        }, 2000);

        // Auto-stop polling after 2 minutes
        setTimeout(() => clearInterval(pollInterval), 120000);
      }

      // Notify parent after 1.5s
      setTimeout(() => {
        onSaveSuccess();
      }, 1500);
    } catch (err) {
      console.error("❌ Save failed:", err);
      setSaveError(
        err instanceof Error
          ? err.message
          : "Không thể lưu questions. Vui lòng thử lại."
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    if (hasChanges) {
      if (window.confirm("Bạn có thay đổi chưa lưu. Bạn có chắc muốn hủy?")) {
        onCancel();
      }
    } else {
      onCancel();
    }
  };

  return (
    <Card className="border-blue-200">
      <CardHeader className="bg-blue-50 border-b">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">✏️ Chỉnh sửa Questions</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              {documentTitle} ({collection}/{docId})
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={handleCancel}
              variant="outline"
              size="sm"
              disabled={isSaving}
            >
              <X className="w-4 h-4 mr-2" />
              Hủy
            </Button>
            <Button
              onClick={handleSave}
              size="sm"
              disabled={!hasChanges || isSaving}
            >
              {isSaving ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Save className="w-4 h-4 mr-2" />
              )}
              Lưu thay đổi
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-6 space-y-6">
        {/* Save Success Message */}
        {saveSuccess && (
          <Card className="border-green-200 bg-green-50">
            <CardContent className="pt-4">
              <div className="flex items-center gap-2 text-green-600">
                <CheckCircle className="w-5 h-5" />
                <span className="font-medium">Lưu thành công!</span>
              </div>
              {rebuildStatus?.triggered && (
                <div className="mt-2 text-sm text-green-700">
                  🚀 Rebuild đã được kích hoạt (PID: {rebuildStatus.pid})
                  {rebuildStatus.progress !== undefined && (
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full transition-all"
                          style={{ width: `${rebuildStatus.progress}%` }}
                        ></div>
                      </div>
                      <p className="text-xs mt-1">
                        {rebuildStatus.progress}% hoàn thành
                      </p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Save Error Message */}
        {saveError && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-4">
              <div className="flex items-center gap-2 text-red-600">
                <AlertCircle className="w-5 h-5" />
                <span className="font-medium">Lỗi khi lưu</span>
              </div>
              <p className="text-sm text-red-700 mt-1">{saveError}</p>
            </CardContent>
          </Card>
        )}

        {/* Main Question */}
        <div className="space-y-2">
          <label className="text-sm font-medium flex items-center gap-2">
            <Badge variant="default" className="bg-blue-600">
              Câu hỏi chính
            </Badge>
          </label>
          <Textarea
            value={mainQuestion}
            onChange={(e) => setMainQuestion(e.target.value)}
            placeholder="Nhập câu hỏi chính..."
            rows={3}
            className="resize-none"
            disabled={isSaving}
          />
          <p className="text-xs text-muted-foreground">
            Câu hỏi chính đại diện cho nội dung document
          </p>
        </div>

        {/* Question Variants */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium flex items-center gap-2">
              <Badge variant="outline">Biến thể câu hỏi</Badge>
              <span className="text-muted-foreground">({variants.length})</span>
            </label>
          </div>

          {/* Existing Variants */}
          <div className="space-y-2">
            {variants.map((variant, index) => (
              <div key={index} className="flex items-center gap-2">
                <Badge variant="outline" className="w-8 text-center">
                  {index + 1}
                </Badge>
                <Input
                  value={variant}
                  onChange={(e) => handleUpdateVariant(index, e.target.value)}
                  placeholder={`Biến thể ${index + 1}...`}
                  disabled={isSaving}
                  className="flex-1"
                />
                <Button
                  onClick={() => handleRemoveVariant(index)}
                  variant="outline"
                  size="sm"
                  disabled={isSaving}
                >
                  <Trash2 className="w-4 h-4 text-red-500" />
                </Button>
              </div>
            ))}
          </div>

          {/* Add New Variant */}
          <div className="flex items-center gap-2">
            <Input
              value={newVariant}
              onChange={(e) => setNewVariant(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleAddVariant();
                }
              }}
              placeholder="Thêm biến thể mới..."
              disabled={isSaving}
              className="flex-1"
            />
            <Button
              onClick={handleAddVariant}
              variant="outline"
              size="sm"
              disabled={!newVariant.trim() || isSaving}
            >
              <Plus className="w-4 h-4 mr-2" />
              Thêm
            </Button>
          </div>
        </div>

        {/* Rebuild Trigger Option */}
        <div className="flex items-center gap-3 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <input
            type="checkbox"
            id="trigger-rebuild"
            checked={triggerRebuild}
            onChange={(e) => setTriggerRebuild(e.target.checked)}
            disabled={isSaving}
            className="w-4 h-4"
          />
          <label
            htmlFor="trigger-rebuild"
            className="text-sm text-yellow-900 cursor-pointer flex-1"
          >
            <div className="flex items-center gap-2">
              <RefreshCw className="w-4 h-4" />
              <span className="font-medium">Rebuild VectorDB sau khi lưu</span>
            </div>
            <p className="text-xs text-yellow-700 mt-1">
              Cập nhật cache để các thay đổi có hiệu lực ngay lập tức (khuyến
              nghị)
            </p>
          </label>
        </div>

        {/* Changes Summary */}
        {hasChanges && (
          <div className="text-sm text-muted-foreground bg-blue-50 p-3 rounded-lg">
            📝 Bạn có thay đổi chưa lưu:
            <ul className="list-disc list-inside mt-1 space-y-1">
              {mainQuestion !== currentMainQuestion && (
                <li>Câu hỏi chính đã thay đổi</li>
              )}
              {JSON.stringify(variants) !== JSON.stringify(currentVariants) && (
                <li>Biến thể đã thay đổi ({variants.length} biến thể)</li>
              )}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
