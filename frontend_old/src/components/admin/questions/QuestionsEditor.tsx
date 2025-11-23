/**
 * 📝 QUESTIONS EDITOR COMPONENT V2
 * Improved UX: Modal confirmation for rebuild với progress tracking
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
  // Editing states
  const [mainQuestion, setMainQuestion] = useState(currentMainQuestion);
  const [variants, setVariants] = useState<string[]>(currentVariants);
  const [newVariant, setNewVariant] = useState("");

  // Save states
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Modal states
  const [showRebuildModal, setShowRebuildModal] = useState(false);
  const [rebuildProgress, setRebuildProgress] = useState<number | null>(null);
  const [rebuildStatus, setRebuildStatus] = useState<string>("");

  // Detect changes
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

  // Step 1: Click "Lưu thay đổi" → Show modal
  const handleSaveClick = () => {
    if (!mainQuestion.trim()) {
      setSaveError("Vui lòng nhập câu hỏi chính");
      return;
    }

    // Show rebuild confirmation modal
    setShowRebuildModal(true);
  };

  // Step 2: Save without rebuild
  const handleSaveOnly = async () => {
    try {
      setIsSaving(true);
      setSaveError(null);

      console.log(
        `💾 Saving questions (no rebuild) for ${collection}/${docId}`
      );

      await updateQuestions(collection, docId, mainQuestion, variants, false);

      console.log("✅ Save successful (no rebuild)");

      // Close modal and notify parent
      setShowRebuildModal(false);
      setTimeout(() => {
        onSaveSuccess();
      }, 500);
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

  // Step 3: Save with rebuild
  const handleSaveAndRebuild = async () => {
    try {
      setIsSaving(true);
      setSaveError(null);
      setRebuildProgress(0);
      setRebuildStatus("Đang lưu thay đổi...");

      console.log(
        `💾 Saving questions with rebuild for ${collection}/${docId}`
      );

      const result = await updateQuestions(
        collection,
        docId,
        mainQuestion,
        variants,
        true
      );

      console.log("✅ Save successful, rebuild triggered:", result);

      if (result.rebuild_status?.triggered) {
        setRebuildStatus("Đang rebuild vector database...");

        // Poll rebuild status
        const pollInterval = setInterval(async () => {
          try {
            const status = await getRebuildStatus();
            setRebuildProgress(status.progress || 0);

            if (status.status === "success") {
              setRebuildStatus("✅ Rebuild hoàn thành!");
              clearInterval(pollInterval);

              // Close modal after 2s
              setTimeout(() => {
                setShowRebuildModal(false);
                setRebuildProgress(null);
                onSaveSuccess();
              }, 2000);
            } else if (status.status === "failed") {
              setRebuildStatus("❌ Rebuild thất bại");
              setRebuildProgress(null);
              clearInterval(pollInterval);
            }
          } catch (err) {
            console.error("Error polling rebuild status:", err);
            clearInterval(pollInterval);
            setRebuildStatus("❌ Lỗi khi kiểm tra tiến trình");
            setRebuildProgress(null);
          }
        }, 2000);

        // Timeout after 2 minutes
        setTimeout(() => {
          clearInterval(pollInterval);
          if (rebuildProgress !== null && rebuildProgress < 100) {
            setRebuildStatus("⏱️ Timeout - Rebuild vẫn đang chạy");
          }
        }, 120000);
      } else {
        // No rebuild triggered
        setShowRebuildModal(false);
        setTimeout(() => {
          onSaveSuccess();
        }, 500);
      }
    } catch (err) {
      console.error("❌ Save & rebuild failed:", err);
      setSaveError(
        err instanceof Error
          ? err.message
          : "Không thể lưu questions. Vui lòng thử lại."
      );
      setRebuildProgress(null);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <>
      {/* Main Editor Card */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl">Chỉnh sửa câu hỏi</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                {documentTitle}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={onCancel}
                variant="outline"
                size="sm"
                disabled={isSaving}
              >
                <X className="w-4 h-4 mr-2" />
                Hủy
              </Button>
              <Button
                onClick={handleSaveClick}
                size="sm"
                disabled={isSaving || !hasChanges}
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

          {/* Change Indicator */}
          {hasChanges && (
            <Card className="border-yellow-200 bg-yellow-50">
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 text-yellow-700">
                  <AlertCircle className="w-4 h-4" />
                  <span className="text-sm font-medium">
                    Có thay đổi chưa được lưu
                  </span>
                </div>
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

          {/* Variants List */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-green-50">
                Biến thể câu hỏi
              </Badge>
              <span className="text-sm text-muted-foreground">
                ({variants.length} variants)
              </span>
            </div>

            {variants.length > 0 ? (
              <div className="space-y-2">
                {variants.map((variant, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-2 p-3 border rounded-lg bg-gray-50"
                  >
                    <span className="text-sm font-medium text-gray-500">
                      {index + 1}.
                    </span>
                    <Input
                      value={variant}
                      onChange={(e) =>
                        handleUpdateVariant(index, e.target.value)
                      }
                      className="flex-1"
                      disabled={isSaving}
                    />
                    <Button
                      onClick={() => handleRemoveVariant(index)}
                      variant="ghost"
                      size="sm"
                      disabled={isSaving}
                    >
                      <Trash2 className="w-4 h-4 text-red-600" />
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground italic">
                Chưa có biến thể nào
              </p>
            )}

            {/* Add New Variant */}
            <div className="flex gap-2">
              <Input
                value={newVariant}
                onChange={(e) => setNewVariant(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleAddVariant()}
                placeholder="Nhập biến thể mới..."
                disabled={isSaving}
              />
              <Button
                onClick={handleAddVariant}
                variant="outline"
                disabled={!newVariant.trim() || isSaving}
              >
                <Plus className="w-4 h-4 mr-2" />
                Thêm
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Rebuild Confirmation Modal */}
      {showRebuildModal && (
        <div
          className="fixed inset-0 flex items-center justify-center z-50 p-4"
          style={{
            backgroundColor: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(4px)",
          }}
        >
          <Card
            className="w-[500px] max-w-[90vw] shadow-2xl border-2"
            style={{ backgroundColor: "white" }}
          >
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <RefreshCw className="w-5 h-5" />
                Xác nhận lưu thay đổi
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {rebuildProgress === null ? (
                <>
                  {/* Question before save */}
                  <div className="space-y-3">
                    <p className="text-sm text-muted-foreground">
                      Bạn có muốn rebuild vector database sau khi lưu?
                    </p>

                    {/* Option 1: Save only */}
                    <div className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                      <div className="flex items-start gap-3">
                        <Save className="w-5 h-5 text-blue-600 mt-0.5" />
                        <div className="flex-1">
                          <h4 className="font-medium text-sm">
                            Chỉ lưu thay đổi
                          </h4>
                          <p className="text-xs text-muted-foreground mt-1">
                            Lưu nhanh, rebuild sau. Thích hợp khi đang chỉnh sửa
                            nhiều documents.
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Option 2: Save & Rebuild */}
                    <div className="p-4 border-2 border-green-200 bg-green-50 rounded-lg">
                      <div className="flex items-start gap-3">
                        <Zap className="w-5 h-5 text-green-600 mt-0.5" />
                        <div className="flex-1">
                          <h4 className="font-medium text-sm text-green-900">
                            Lưu & Rebuild ngay
                          </h4>
                          <p className="text-xs text-green-700 mt-1">
                            Áp dụng thay đổi vào chat ngay lập tức. Khuyến nghị!
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Action buttons */}
                  <div className="flex gap-2 justify-end pt-2">
                    <Button
                      onClick={() => setShowRebuildModal(false)}
                      variant="outline"
                      size="sm"
                      disabled={isSaving}
                    >
                      Hủy
                    </Button>
                    <Button
                      onClick={handleSaveOnly}
                      variant="outline"
                      size="sm"
                      disabled={isSaving}
                    >
                      <Save className="w-4 h-4 mr-2" />
                      Chỉ lưu
                    </Button>
                    <Button
                      onClick={handleSaveAndRebuild}
                      size="sm"
                      disabled={isSaving}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      {isSaving ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Zap className="w-4 h-4 mr-2" />
                      )}
                      Lưu & Rebuild
                    </Button>
                  </div>
                </>
              ) : (
                <>
                  {/* Rebuild in progress */}
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <RefreshCw className="w-5 h-5 animate-spin text-blue-600" />
                      <div className="flex-1">
                        <p className="text-sm font-medium">{rebuildStatus}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Vui lòng đợi...
                        </p>
                      </div>
                    </div>

                    {/* Progress bar */}
                    <div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div
                          className="bg-blue-600 h-3 rounded-full transition-all duration-300 flex items-center justify-center"
                          style={{ width: `${rebuildProgress}%` }}
                        >
                          {rebuildProgress > 10 && (
                            <span className="text-xs text-white font-medium">
                              {rebuildProgress}%
                            </span>
                          )}
                        </div>
                      </div>
                      <p className="text-xs text-center text-muted-foreground mt-2">
                        {rebuildProgress}% hoàn thành
                      </p>
                    </div>

                    {rebuildProgress >= 100 && (
                      <div className="flex items-center gap-2 text-green-600 bg-green-50 p-3 rounded-lg">
                        <CheckCircle className="w-5 h-5" />
                        <span className="text-sm font-medium">
                          Rebuild hoàn thành thành công!
                        </span>
                      </div>
                    )}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </>
  );
}
