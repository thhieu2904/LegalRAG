import { useState } from "react";
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
} from "lucide-react";

interface QuestionCollection {
  id: string;
  name: string;
  displayName: string;
  questionCount: number;
  lastUpdated: string;
  description: string;
}

interface SampleQuestion {
  id: string;
  question: string;
  category: string;
  keywords: string[];
  expectedCollection: string;
  confidence: number;
  lastUpdated: string;
}

export default function AdminQuestions() {
  const [selectedCollection, setSelectedCollection] =
    useState<QuestionCollection | null>(null);
  const [showAddQuestion, setShowAddQuestion] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  // Mock data based on router_examples_smart_v3 structure
  const [collections] = useState<QuestionCollection[]>([
    {
      id: "quy_trinh_cap_ho_tich_cap_xa",
      name: "quy_trinh_cap_ho_tich_cap_xa",
      displayName: "Hộ tịch cấp xã",
      questionCount: 45,
      lastUpdated: "2024-01-15",
      description: "Câu hỏi về khai sinh, kết hôn, khai tử...",
    },
    {
      id: "quy_trinh_chung_thuc",
      name: "quy_trinh_chung_thuc",
      displayName: "Chứng thực",
      questionCount: 28,
      lastUpdated: "2024-01-12",
      description: "Câu hỏi về chứng thực hợp đồng, chữ ký...",
    },
    {
      id: "quy_trinh_nuoi_con_nuoi",
      name: "quy_trinh_nuoi_con_nuoi",
      displayName: "Nuôi con nuôi",
      questionCount: 15,
      lastUpdated: "2024-01-10",
      description: "Câu hỏi về thủ tục nhận con nuôi...",
    },
  ]);

  // Mock questions for selected collection
  const [questions] = useState<SampleQuestion[]>([
    {
      id: "q1",
      question: "Làm thủ tục khai sinh cho em bé cần giấy tờ gì?",
      category: "khai_sinh",
      keywords: ["khai sinh", "em bé", "giấy tờ", "thủ tục"],
      expectedCollection: "quy_trinh_cap_ho_tich_cap_xa",
      confidence: 0.95,
      lastUpdated: "2024-01-15",
    },
    {
      id: "q2",
      question: "Thời gian làm giấy khai sinh mất bao lâu?",
      category: "khai_sinh",
      keywords: ["thời gian", "giấy khai sinh", "bao lâu"],
      expectedCollection: "quy_trinh_cap_ho_tich_cap_xa",
      confidence: 0.92,
      lastUpdated: "2024-01-14",
    },
    {
      id: "q3",
      question: "Có thể làm khai sinh ở xã khác không?",
      category: "khai_sinh",
      keywords: ["khai sinh", "xã khác", "nơi khác"],
      expectedCollection: "quy_trinh_cap_ho_tich_cap_xa",
      confidence: 0.88,
      lastUpdated: "2024-01-13",
    },
    {
      id: "q4",
      question: "Đăng ký kết hôn cần chuẩn bị gì?",
      category: "ket_hon",
      keywords: ["đăng ký kết hôn", "chuẩn bị", "giấy tờ"],
      expectedCollection: "quy_trinh_cap_ho_tich_cap_xa",
      confidence: 0.94,
      lastUpdated: "2024-01-12",
    },
    {
      id: "q5",
      question: "Người nước ngoài kết hôn với người Việt Nam cần làm gì?",
      category: "ket_hon",
      keywords: ["nước ngoài", "kết hôn", "Việt Nam", "thủ tục"],
      expectedCollection: "quy_trinh_cap_ho_tich_cap_xa",
      confidence: 0.91,
      lastUpdated: "2024-01-11",
    },
  ]);

  const [newQuestion, setNewQuestion] = useState({
    question: "",
    category: "",
    keywords: "",
    expectedCollection: "",
    confidence: 0.8,
  });

  const filteredQuestions = questions.filter(
    (q) =>
      q.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.keywords.some((k) => k.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleSaveQuestion = () => {
    // TODO: Implement save question
    console.log("Save question:", newQuestion);
    alert("Câu hỏi mẫu sẽ được lưu vào router examples");
    setShowAddQuestion(false);
    setNewQuestion({
      question: "",
      category: "",
      keywords: "",
      expectedCollection: "",
      confidence: 0.8,
    });
  };

  const handleDeleteQuestion = (questionId: string) => {
    // TODO: Implement delete question
    if (confirm("Bạn có chắc muốn xóa câu hỏi này?")) {
      console.log("Delete question:", questionId);
    }
  };

  const handleImportFromFiles = () => {
    // TODO: Implement import from existing JSON files
    console.log("Import from router_examples_smart_v3");
    alert("Sẽ import câu hỏi từ các file JSON có sẵn");
  };

  const handleExportQuestions = () => {
    // TODO: Implement export to JSON
    console.log("Export questions to JSON");
    alert("Sẽ export câu hỏi ra file JSON cho router system");
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

  const QuestionCard = ({ question }: { question: SampleQuestion }) => (
    <Card className="border-2">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-base leading-tight">
              {question.question}
            </CardTitle>
            <div className="flex items-center space-x-2 mt-2">
              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                {question.category}
              </span>
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                {Math.round(question.confidence * 100)}% tin cậy
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

        {/* Expected Collection */}
        <div>
          <p className="text-xs font-medium text-gray-600 mb-1">
            Collection dự kiến:
          </p>
          <p className="text-sm text-gray-800">{question.expectedCollection}</p>
        </div>

        <div className="text-xs text-gray-500">
          Cập nhật: {question.lastUpdated}
        </div>

        {/* Actions */}
        <div className="flex space-x-2">
          <Button variant="outline" size="sm">
            <Eye className="h-3 w-3 mr-1" />
            Xem
          </Button>
          <Button variant="outline" size="sm">
            <Edit className="h-3 w-3 mr-1" />
            Sửa
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDeleteQuestion(question.id)}
            className="text-red-600"
          >
            <Trash2 className="h-3 w-3 mr-1" />
            Xóa
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
              value={newQuestion.question}
              onChange={(e) =>
                setNewQuestion((prev) => ({
                  ...prev,
                  question: e.target.value,
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
              <Label>Collection dự kiến</Label>
              <select
                className="w-full p-2 border border-gray-300 rounded-md"
                value={newQuestion.expectedCollection}
                onChange={(e) =>
                  setNewQuestion((prev) => ({
                    ...prev,
                    expectedCollection: e.target.value,
                  }))
                }
              >
                <option value="">Chọn collection</option>
                {collections.map((col) => (
                  <option key={col.id} value={col.name}>
                    {col.displayName}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <Label>Từ khóa (phân cách bằng dấu phẩy)</Label>
            <Input
              value={newQuestion.keywords}
              onChange={(e) =>
                setNewQuestion((prev) => ({
                  ...prev,
                  keywords: e.target.value,
                }))
              }
              placeholder="khai sinh, giấy tờ, thủ tục, em bé"
            />
          </div>

          <div>
            <Label>
              Độ tin cậy: {Math.round(newQuestion.confidence * 100)}%
            </Label>
            <input
              type="range"
              min="0.5"
              max="1.0"
              step="0.05"
              value={newQuestion.confidence}
              onChange={(e) =>
                setNewQuestion((prev) => ({
                  ...prev,
                  confidence: parseFloat(e.target.value),
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
              disabled={
                !newQuestion.question ||
                !newQuestion.category ||
                !newQuestion.expectedCollection
              }
            >
              <Save className="h-4 w-4 mr-2" />
              Lưu câu hỏi
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  if (selectedCollection) {
    return (
      <div className="space-y-6">
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
            Tìm thấy <strong>{filteredQuestions.length}</strong> câu hỏi. Đường
            dẫn file:{" "}
            <code>
              backend/data/router_examples_smart_v3/{selectedCollection.name}/
            </code>
          </AlertDescription>
        </Alert>

        {/* Questions Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredQuestions.map((question) => (
            <QuestionCard key={question.id} question={question} />
          ))}
        </div>

        {showAddQuestion && <AddQuestionModal />}
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
          >
            <FileText className="w-4 h-4" />
            Import từ file JSON
          </Button>
        </div>
      </div>

      <div className="admin-content-section">
        <Alert className="questions-alert">
          <Info className="w-4 h-4" />
          <AlertDescription>
            <strong>Hướng dẫn:</strong> Câu hỏi mẫu giúp hệ thống học cách phân
            loại và định tuyến câu hỏi mới. Dữ liệu được lưu trong{" "}
            <code className="questions-code">
              backend/data/router_examples_smart_v3/
            </code>
          </AlertDescription>
        </Alert>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {collections.map((collection) => (
            <CollectionCard key={collection.id} collection={collection} />
          ))}
        </div>

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
