import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Alert, AlertDescription } from "../../components/ui/alert";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui/textarea";
import {
  MessageSquare,
  Plus,
  Eye,
  Edit,
  Trash2,
  FolderOpen,
  FileText,
  Search,
  Info,
  Save,
  X,
  ChevronLeft,
  Loader,
} from "lucide-react";
import { questionsService } from "../../services/questionsService";
import type { Question, QuestionCreate } from "../../services/questionsService";

interface QuestionCollection {
  id: string;
  name: string;
  displayName: string;
  questionCount: number;
  lastUpdated: string;
  description: string;
}

export default function AdminQuestions() {
  const [selectedCollection, setSelectedCollection] =
    useState<QuestionCollection | null>(null);
  const [showAddQuestion, setShowAddQuestion] = useState(false);
  const [showEditQuestion, setShowEditQuestion] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // State for real data from API
  const [collections, setCollections] = useState<QuestionCollection[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);

  // Load collections from API
  useEffect(() => {
    loadCollections();
  }, []);

  const loadCollections = async () => {
    try {
      setLoading(true);
      setError(null);
      const apiCollections = await questionsService.getCollections();

      // Transform API data to local format
      const transformedCollections: QuestionCollection[] = apiCollections.map(
        (col) => ({
          id: col.name,
          name: col.name,
          displayName: col.display_name,
          questionCount: col.total_questions,
          lastUpdated: new Date().toISOString().split("T")[0], // Mock last updated
          description: `Quản lý câu hỏi cho ${col.display_name}`, // Mock description
        })
      );

      setCollections(transformedCollections);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load collections"
      );
    } finally {
      setLoading(false);
    }
  };

  const loadQuestions = async (collectionName: string) => {
    try {
      setLoading(true);
      setError(null);
      const apiQuestions = await questionsService.getCollectionQuestions(
        collectionName
      );
      setQuestions(apiQuestions);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load questions");
    } finally {
      setLoading(false);
    }
  };

  // Load questions when collection is selected
  useEffect(() => {
    if (selectedCollection) {
      loadQuestions(selectedCollection.name);
    }
  }, [selectedCollection]);

  const [newQuestion, setNewQuestion] = useState({
    text: "",
    category: "",
    keywords: [] as string[],
    keywordsText: "", // For the input field
    type: "variant",
    priority_score: 0.8,
  });

  const filteredQuestions = questions.filter(
    (q) =>
      q.text.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.keywords.some((k) => k.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleSaveQuestion = async () => {
    if (!selectedCollection) return;

    try {
      setLoading(true);
      setError(null);

      // Convert keywords text to array
      const keywordsArray = newQuestion.keywordsText
        .split(",")
        .map((k) => k.trim())
        .filter((k) => k.length > 0);

      const questionData: QuestionCreate = {
        text: newQuestion.text,
        category: newQuestion.category,
        keywords: keywordsArray,
        type: newQuestion.type,
        priority_score: newQuestion.priority_score,
      };

      await questionsService.createQuestion(
        selectedCollection.name,
        questionData
      );

      // Reload questions
      await loadQuestions(selectedCollection.name);

      // Reset form
      setNewQuestion({
        text: "",
        category: "",
        keywords: [],
        keywordsText: "",
        type: "variant",
        priority_score: 0.8,
      });

      setShowAddQuestion(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save question");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteQuestion = async (questionId: string) => {
    if (!selectedCollection) return;

    if (confirm("Bạn có chắc muốn xóa câu hỏi này?")) {
      try {
        setLoading(true);
        setError(null);

        await questionsService.deleteQuestion(
          selectedCollection.name,
          questionId
        );

        // Reload questions
        await loadQuestions(selectedCollection.name);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to delete question"
        );
      } finally {
        setLoading(false);
      }
    }
  };

  const handleEditQuestion = (question: Question) => {
    setEditingQuestion(question);
    setNewQuestion({
      text: question.text,
      category: question.category || "",
      keywords: question.keywords || [],
      keywordsText: question.keywords?.join(", ") || "",
      type: question.type || "variant",
      priority_score: question.priority_score || 0.5,
    });
    setShowEditQuestion(true);
  };

  const handleUpdateQuestion = async () => {
    if (!selectedCollection || !editingQuestion) return;

    try {
      setLoading(true);
      setError(null);

      // Convert keywords text to array
      const keywordsArray = newQuestion.keywordsText
        .split(",")
        .map((k) => k.trim())
        .filter((k) => k.length > 0);

      const updates = {
        text: newQuestion.text,
        category: newQuestion.category,
        keywords: keywordsArray,
        priority_score: newQuestion.priority_score,
      };

      await questionsService.updateQuestion(
        selectedCollection.name,
        editingQuestion.id,
        updates
      );

      // Reload questions
      await loadQuestions(selectedCollection.name);

      // Reset form
      setEditingQuestion(null);
      setShowEditQuestion(false);
      setNewQuestion({
        text: "",
        category: "",
        keywords: [],
        keywordsText: "",
        type: "variant",
        priority_score: 0.8,
      });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update question"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleImportFromFiles = async () => {
    // TODO: Implement import from existing JSON files
    alert("Tính năng import sẽ được triển khai sau");
  };

  const handleExportQuestions = async () => {
    if (!selectedCollection) return;

    try {
      setLoading(true);
      setError(null);

      await questionsService.saveCollectionToFile(selectedCollection.name);
      alert("Đã lưu questions vào file JSON thành công!");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to export questions"
      );
    } finally {
      setLoading(false);
    }
  };

  const CollectionCard = ({
    collection,
  }: {
    collection: QuestionCollection;
  }) => (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow border-2 hover:border-blue-200"
      onClick={() => setSelectedCollection(collection)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <MessageSquare className="h-6 w-6 text-green-600" />
            <div>
              <CardTitle className="text-lg">
                {collection.displayName}
              </CardTitle>
              <p className="text-sm text-gray-500 mt-1">{collection.name}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-green-900">
              {collection.questionCount}
            </p>
            <p className="text-xs text-green-700">câu hỏi</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-sm text-gray-600 mb-3">{collection.description}</p>
        <div className="text-sm text-gray-500">
          Cập nhật: {collection.lastUpdated}
        </div>
      </CardContent>
    </Card>
  );

  const QuestionCard = ({ question }: { question: Question }) => (
    <Card className="border-2">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-base leading-tight">
              {question.text}
            </CardTitle>
            <div className="flex items-center space-x-2 mt-2">
              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                {question.category || "Không phân loại"}
              </span>
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                {Math.round(question.priority_score * 100)}% ưu tiên
              </span>
              <span
                className={`px-2 py-1 text-xs rounded-full ${
                  question.status === "active"
                    ? "bg-green-100 text-green-800"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {question.status}
              </span>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Keywords */}
        <div>
          <p className="text-xs font-medium text-gray-600 mb-1">Từ khóa:</p>
          <div className="flex flex-wrap gap-1">
            {question.keywords.map((keyword, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>

        {/* Type and Source */}
        <div className="grid grid-cols-2 gap-2">
          <div>
            <p className="text-xs font-medium text-gray-600 mb-1">Loại:</p>
            <p className="text-sm text-gray-800">{question.type}</p>
          </div>
          {question.source && (
            <div>
              <p className="text-xs font-medium text-gray-600 mb-1">Nguồn:</p>
              <p className="text-sm text-gray-800 truncate">
                {question.source}
              </p>
            </div>
          )}
        </div>

        <div className="text-xs text-gray-500">
          {question.updated_at &&
            `Cập nhật: ${new Date(question.updated_at).toLocaleDateString(
              "vi-VN"
            )}`}
          {question.created_at &&
            !question.updated_at &&
            `Tạo: ${new Date(question.created_at).toLocaleDateString("vi-VN")}`}
        </div>

        {/* Actions */}
        <div className="flex space-x-2">
          <Button variant="outline" size="sm">
            <Eye className="h-3 w-3 mr-1" />
            Xem
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleEditQuestion(question)}
          >
            <Edit className="h-3 w-3 mr-1" />
            Sửa
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDeleteQuestion(question.id)}
            className="text-red-600"
            disabled={loading}
          >
            <Trash2 className="h-3 w-3 mr-1" />
            {loading ? "..." : "Xóa"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  // Add Question Modal
  const AddQuestionModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-2xl mx-4">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Thêm câu hỏi mẫu</CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAddQuestion(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Câu hỏi</Label>
            <Textarea
              value={newQuestion.text}
              onChange={(e) =>
                setNewQuestion((prev) => ({
                  ...prev,
                  text: e.target.value,
                }))
              }
              placeholder="Nhập câu hỏi mẫu..."
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Danh mục</Label>
              <Input
                value={newQuestion.category}
                onChange={(e) =>
                  setNewQuestion((prev) => ({
                    ...prev,
                    category: e.target.value,
                  }))
                }
                placeholder="vd: khai_sinh, ket_hon"
              />
            </div>
            <div>
              <Label>Collection</Label>
              <select
                className="w-full p-2 border border-gray-300 rounded-md"
                value={selectedCollection?.name || ""}
                disabled
              >
                <option value="">
                  {selectedCollection?.displayName || "Chọn collection"}
                </option>
              </select>
            </div>
          </div>

          <div>
            <Label>Từ khóa (phân cách bằng dấu phẩy)</Label>
            <Input
              value={newQuestion.keywordsText}
              onChange={(e) =>
                setNewQuestion((prev) => ({
                  ...prev,
                  keywordsText: e.target.value,
                }))
              }
              placeholder="khai sinh, giấy tờ, thủ tục, em bé"
            />
          </div>

          <div>
            <Label>
              Độ ưu tiên: {Math.round(newQuestion.priority_score * 100)}%
            </Label>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={newQuestion.priority_score}
              onChange={(e) =>
                setNewQuestion((prev) => ({
                  ...prev,
                  priority_score: parseFloat(e.target.value),
                }))
              }
              className="w-full"
            />
          </div>

          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              Câu hỏi mẫu sẽ được lưu vào router examples để huấn luyện hệ thống
              phân loại.
            </AlertDescription>
          </Alert>

          <div className="flex justify-end space-x-3">
            <Button variant="outline" onClick={() => setShowAddQuestion(false)}>
              Hủy
            </Button>
            <Button
              onClick={handleSaveQuestion}
              disabled={loading || !newQuestion.text || !newQuestion.category}
            >
              <Save className="h-4 w-4 mr-2" />
              {loading ? "Đang lưu..." : "Lưu câu hỏi"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  // Edit Question Modal
  const EditQuestionModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-2xl mx-4">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Chỉnh sửa câu hỏi</CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setShowEditQuestion(false);
                setEditingQuestion(null);
              }}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Câu hỏi</Label>
            <Textarea
              value={newQuestion.text}
              onChange={(e) =>
                setNewQuestion((prev) => ({
                  ...prev,
                  text: e.target.value,
                }))
              }
              placeholder="Nhập câu hỏi mẫu..."
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Danh mục</Label>
              <Input
                value={newQuestion.category}
                onChange={(e) =>
                  setNewQuestion((prev) => ({
                    ...prev,
                    category: e.target.value,
                  }))
                }
                placeholder="vd: khai_sinh, ket_hon"
              />
            </div>
            <div>
              <Label>Loại câu hỏi</Label>
              <select
                className="w-full p-2 border border-gray-300 rounded-md"
                value={newQuestion.type}
                onChange={(e) =>
                  setNewQuestion((prev) => ({
                    ...prev,
                    type: e.target.value,
                  }))
                }
              >
                <option value="main">Câu hỏi chính</option>
                <option value="variant">Câu hỏi phụ</option>
                <option value="user_generated">Người dùng tạo</option>
              </select>
            </div>
          </div>

          <div>
            <Label>Từ khóa (phân cách bằng dấu phẩy)</Label>
            <Input
              value={newQuestion.keywordsText}
              onChange={(e) =>
                setNewQuestion((prev) => ({
                  ...prev,
                  keywordsText: e.target.value,
                }))
              }
              placeholder="khai sinh, giấy tờ, thủ tục, em bé"
            />
          </div>

          <div>
            <Label>
              Độ ưu tiên: {Math.round(newQuestion.priority_score * 100)}%
            </Label>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={newQuestion.priority_score}
              onChange={(e) =>
                setNewQuestion((prev) => ({
                  ...prev,
                  priority_score: parseFloat(e.target.value),
                }))
              }
              className="w-full"
            />
          </div>

          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              Thay đổi sẽ được lưu vào database và cập nhật router cache.
            </AlertDescription>
          </Alert>

          <div className="flex justify-end space-x-3">
            <Button
              variant="outline"
              onClick={() => {
                setShowEditQuestion(false);
                setEditingQuestion(null);
              }}
            >
              Hủy
            </Button>
            <Button
              onClick={handleUpdateQuestion}
              disabled={loading || !newQuestion.text || !newQuestion.category}
            >
              <Save className="h-4 w-4 mr-2" />
              {loading ? "Đang cập nhật..." : "Cập nhật câu hỏi"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  if (selectedCollection) {
    return (
      <div className="space-y-6">
        {error && (
          <Alert className="border-red-200 bg-red-50">
            <Info className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              {error}
            </AlertDescription>
          </Alert>
        )}

        <div className="flex items-center justify-between">
          <div>
            <Button
              variant="outline"
              onClick={() => setSelectedCollection(null)}
              className="mb-4 flex items-center space-x-1 px-3 py-2 text-gray-700 bg-white border border-gray-300 hover:bg-gray-50"
              aria-label="Quay lại"
            >
              <ChevronLeft className="h-4 w-4" />
              <span>Quay lại</span>
            </Button>
            <h1 className="text-3xl font-bold text-gray-900">
              Câu hỏi mẫu: {selectedCollection.displayName}
            </h1>
            <p className="text-gray-600 mt-2">
              {selectedCollection.description}
            </p>
          </div>
          <Button
            onClick={() => setShowAddQuestion(true)}
            className="flex items-center space-x-2"
            disabled={loading}
          >
            <Plus className="h-4 w-4" />
            <span>Thêm câu hỏi</span>
          </Button>
        </div>

        {/* Search */}
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
              <Input
                placeholder="Tìm kiếm câu hỏi, danh mục, từ khóa..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <Button variant="outline" onClick={handleImportFromFiles}>
            <FileText className="h-4 w-4 mr-2" />
            Import từ JSON
          </Button>
          <Button variant="outline" onClick={handleExportQuestions}>
            <Save className="h-4 w-4 mr-2" />
            Export JSON
          </Button>
        </div>

        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            Tìm thấy <strong>{filteredQuestions.length}</strong> câu hỏi trong
            collection <strong>{selectedCollection.displayName}</strong>
          </AlertDescription>
        </Alert>

        {/* Questions Grid */}
        {loading && questions.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <Loader className="w-6 h-6 animate-spin mr-2" />
            <span>Đang tải câu hỏi...</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredQuestions.map((question, index) => (
              <QuestionCard
                key={question.id || `question-${index}`}
                question={question}
              />
            ))}
            {filteredQuestions.length === 0 && !loading && (
              <div className="col-span-full text-center py-12 text-gray-500">
                {searchTerm
                  ? "Không tìm thấy câu hỏi nào"
                  : "Chưa có câu hỏi nào"}
              </div>
            )}
          </div>
        )}

        {showAddQuestion && <AddQuestionModal />}
        {showEditQuestion && <EditQuestionModal />}
      </div>
    );
  }

  return (
    <div className="admin-page-container admin-questions-page">
      <div className="admin-page-header-section">
        <div className="admin-page-header-content">
          <h1 className="admin-page-title-main">Quản lý câu hỏi mẫu</h1>
          <p className="admin-page-subtitle-main">
            Quản lý câu hỏi mẫu để huấn luyện hệ thống phân loại và định tuyến
          </p>
        </div>
        <div className="admin-page-actions-main">
          <Button
            onClick={handleImportFromFiles}
            className="shared-button shared-button-primary"
            disabled={loading}
          >
            <FileText className="w-4 h-4" />
            {loading ? "Đang xử lý..." : "Import từ file JSON"}
          </Button>
        </div>
      </div>

      <div className="admin-content-section">
        {error && (
          <Alert className="questions-alert border-red-200 bg-red-50 mb-6">
            <Info className="w-4 h-4 text-red-600" />
            <AlertDescription className="text-red-800">
              {error}
            </AlertDescription>
          </Alert>
        )}

        <Alert className="questions-alert">
          <Info className="w-4 h-4" />
          <AlertDescription>
            <strong>Hướng dẫn:</strong> Câu hỏi mẫu giúp hệ thống học cách phân
            loại và định tuyến câu hỏi mới. Dữ liệu được lưu trong{" "}
            <code className="questions-code">
              backend/data/storage/collections/
            </code>
          </AlertDescription>
        </Alert>

        {loading && collections.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <Loader className="w-6 h-6 animate-spin mr-2" />
            <span>Đang tải collections...</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {collections.map((collection) => (
              <CollectionCard key={collection.id} collection={collection} />
            ))}
          </div>
        )}

        {/* Summary Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <MessageSquare className="h-5 w-5" />
              <span>Thống kê câu hỏi mẫu</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="flex items-center space-x-3">
                  <FolderOpen className="h-8 w-8 text-green-600" />
                  <div>
                    <p className="text-2xl font-bold text-green-900">
                      {collections.length}
                    </p>
                    <p className="text-green-700">Collections</p>
                  </div>
                </div>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex items-center space-x-3">
                  <MessageSquare className="h-8 w-8 text-blue-600" />
                  <div>
                    <p className="text-2xl font-bold text-blue-900">
                      {collections.reduce(
                        (total, col) => total + col.questionCount,
                        0
                      )}
                    </p>
                    <p className="text-blue-700">Câu hỏi</p>
                  </div>
                </div>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg">
                <div className="flex items-center space-x-3">
                  <FileText className="h-8 w-8 text-orange-600" />
                  <div>
                    <p className="text-2xl font-bold text-orange-900">
                      {collections.reduce(
                        (total, col) => total + col.questionCount,
                        0
                      )}
                    </p>
                    <p className="text-orange-700">Training samples</p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
