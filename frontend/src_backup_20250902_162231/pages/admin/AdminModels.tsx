import { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Alert, AlertDescription } from "../../components/ui/alert";
import {
  Cpu,
  Play,
  Pause,
  Download,
  Trash2,
  Settings,
  CheckCircle,
  AlertTriangle,
  Clock,
  Info,
  RefreshCw,
  Terminal,
  HardDrive,
} from "lucide-react";

interface ModelInfo {
  id: string;
  name: string;
  displayName: string;
  description: string;
  type: "llm" | "embedding" | "reranker";
  status: "active" | "inactive" | "downloading" | "error" | "not_found";
  version: string;
  size: string;
  location: "gpu" | "cpu";
  path: string;
  url?: string;
  requirements: {
    minVRAM: string;
    recommendedVRAM: string;
    diskSpace: string;
  };
  lastUsed?: string;
}

export default function AdminModels() {
  const [models] = useState<ModelInfo[]>([
    {
      id: "phogpt",
      name: "PhoGPT-4B-Chat-Q4_K_M",
      displayName: "PhoGPT (Mô hình ngôn ngữ)",
      description: "Mô hình AI tạo câu trả lời bằng tiếng Việt từ VinAI",
      type: "llm",
      status: "active",
      version: "4B-Chat-Q4_K_M",
      size: "2.4 GB",
      location: "gpu",
      path: "data/models/llm_dir/PhoGPT-4B-Chat-Q4_K_M.gguf",
      url: "https://huggingface.co/vinai/PhoGPT-4B-Chat-gguf/resolve/main/PhoGPT-4B-Chat-Q4_K_M.gguf",
      requirements: {
        minVRAM: "4 GB",
        recommendedVRAM: "6 GB",
        diskSpace: "3 GB",
      },
      lastUsed: "2024-01-15 14:30",
    },
    {
      id: "embedding",
      name: "Vietnamese_Embedding_v2",
      displayName: "VinAI Embedding (Tìm kiếm)",
      description: "Mô hình tạo embedding để tìm kiếm tài liệu tương đồng",
      type: "embedding",
      status: "active",
      version: "v2",
      size: "1.2 GB",
      location: "cpu",
      path: "data/models/hf_cache/AITeamVN/Vietnamese_Embedding_v2",
      requirements: {
        minVRAM: "0 GB (CPU)",
        recommendedVRAM: "2 GB",
        diskSpace: "2 GB",
      },
      lastUsed: "2024-01-15 14:35",
    },
    {
      id: "reranker",
      name: "Vietnamese_Reranker",
      displayName: "VinAI Reranker (Sắp xếp)",
      description: "Mô hình sắp xếp và chọn lọc kết quả tìm kiếm tốt nhất",
      type: "reranker",
      status: "inactive",
      version: "v1",
      size: "800 MB",
      location: "gpu",
      path: "data/models/hf_cache/AITeamVN/Vietnamese_Reranker",
      requirements: {
        minVRAM: "2 GB",
        recommendedVRAM: "4 GB",
        diskSpace: "1 GB",
      },
    },
  ]);

  const [isRefreshing, setIsRefreshing] = useState(false);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "text-green-600 bg-green-50 border-green-200";
      case "inactive":
        return "text-gray-600 bg-gray-50 border-gray-200";
      case "downloading":
        return "text-blue-600 bg-blue-50 border-blue-200";
      case "error":
      case "not_found":
        return "text-red-600 bg-red-50 border-red-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <CheckCircle className="h-4 w-4" />;
      case "inactive":
        return <Pause className="h-4 w-4" />;
      case "downloading":
        return <Clock className="h-4 w-4" />;
      case "error":
      case "not_found":
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return <Cpu className="h-4 w-4" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "active":
        return "Đang hoạt động";
      case "inactive":
        return "Không hoạt động";
      case "downloading":
        return "Đang tải xuống";
      case "error":
        return "Lỗi";
      case "not_found":
        return "Không tìm thấy";
      default:
        return "Không xác định";
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "llm":
        return "text-blue-600 bg-blue-50";
      case "embedding":
        return "text-green-600 bg-green-50";
      case "reranker":
        return "text-orange-600 bg-orange-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const getTypeText = (type: string) => {
    switch (type) {
      case "llm":
        return "Ngôn ngữ";
      case "embedding":
        return "Tìm kiếm";
      case "reranker":
        return "Sắp xếp";
      default:
        return "Khác";
    }
  };

  const handleRefreshModels = async () => {
    setIsRefreshing(true);
    // TODO: Check model status from backend
    setTimeout(() => {
      setIsRefreshing(false);
    }, 2000);
  };

  const handleSetupAllModels = () => {
    // TODO: Run setup models script
    console.log("Run: python tools/1_setup_models.py");
    alert("Sẽ chạy script setup models:\npython tools/1_setup_models.py");
  };

  const handleStartModel = (modelId: string) => {
    // TODO: Start specific model
    console.log("Start model:", modelId);
    alert(`Sẽ khởi động model: ${modelId}`);
  };

  const handleStopModel = (modelId: string) => {
    // TODO: Stop specific model
    console.log("Stop model:", modelId);
    alert(`Sẽ dừng model: ${modelId}`);
  };

  const handleDownloadModel = (modelId: string) => {
    // TODO: Download model
    console.log("Download model:", modelId);
    alert(`Sẽ tải xuống model: ${modelId}`);
  };

  const handleDeleteModel = (modelId: string) => {
    // TODO: Delete model
    if (confirm("Bạn có chắc muốn xóa model này?")) {
      console.log("Delete model:", modelId);
    }
  };

  const ModelCard = ({ model }: { model: ModelInfo }) => (
    <Card className="border-2">
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <Cpu className="h-6 w-6 text-blue-600 mt-1" />
            <div className="flex-1">
              <CardTitle className="text-lg">{model.displayName}</CardTitle>
              <div className="flex items-center space-x-2 mt-1">
                <span
                  className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(
                    model.type
                  )}`}
                >
                  {getTypeText(model.type)}
                </span>
                <span className="text-sm text-gray-500">v{model.version}</span>
                <span
                  className={`px-1 py-0.5 rounded text-xs ${
                    model.location === "gpu"
                      ? "bg-yellow-100 text-yellow-800"
                      : "bg-blue-100 text-blue-800"
                  }`}
                >
                  {model.location.toUpperCase()}
                </span>
              </div>
            </div>
          </div>
          <div
            className={`flex items-center space-x-1 px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(
              model.status
            )}`}
          >
            {getStatusIcon(model.status)}
            <span>{getStatusText(model.status)}</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <p className="text-sm text-gray-600">{model.description}</p>

        {/* Model Info */}
        <div className="bg-gray-50 p-3 rounded-lg space-y-2">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Kích thước:</span>
              <p>{model.size}</p>
            </div>
            <div>
              <span className="font-medium text-gray-700">VRAM cần:</span>
              <p>{model.requirements.recommendedVRAM}</p>
            </div>
          </div>
          <div>
            <span className="font-medium text-gray-700 text-sm">
              Đường dẫn:
            </span>
            <p className="text-xs font-mono bg-gray-100 p-1 rounded mt-1">
              {model.path}
            </p>
          </div>
        </div>

        {/* Last Used */}
        {model.lastUsed && (
          <div className="text-xs text-gray-500">
            Sử dụng lần cuối: {model.lastUsed}
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-2">
          {model.status === "active" ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleStopModel(model.id)}
              className="flex items-center space-x-1"
            >
              <Pause className="h-4 w-4" />
              <span>Dừng</span>
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={() => handleStartModel(model.id)}
              className="flex items-center space-x-1"
              disabled={
                model.status === "downloading" || model.status === "not_found"
              }
            >
              <Play className="h-4 w-4" />
              <span>Khởi động</span>
            </Button>
          )}

          {(model.status === "not_found" || model.status === "error") &&
            model.url && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDownloadModel(model.id)}
                className="flex items-center space-x-1"
              >
                <Download className="h-4 w-4" />
                <span>Tải xuống</span>
              </Button>
            )}

          <Button
            variant="outline"
            size="sm"
            className="flex items-center space-x-1"
          >
            <Settings className="h-4 w-4" />
            <span>Cài đặt</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDeleteModel(model.id)}
            className="flex items-center space-x-1 text-red-600 hover:text-red-700"
          >
            <Trash2 className="h-4 w-4" />
            <span>Xóa</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const activeModels = models.filter((m) => m.status === "active").length;
  const totalVRAM = models
    .filter((m) => m.status === "active" && m.location === "gpu")
    .reduce(
      (total, m) => total + parseFloat(m.requirements.recommendedVRAM),
      0
    );

  return (
    <div className="admin-page-container admin-models-page">
      <div className="admin-page-header-section">
        <div className="admin-page-header-content">
          <h1 className="admin-page-title-main">Quản lý mô hình AI</h1>
          <p className="admin-page-subtitle-main">
            Quản lý các mô hình trí tuệ nhân tạo của hệ thống
          </p>
        </div>
        <div className="admin-page-actions-main">
          <Button
            variant="outline"
            onClick={handleRefreshModels}
            disabled={isRefreshing}
            className="shared-button"
          >
            <RefreshCw
              className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`}
            />
            Làm mới
          </Button>
          <Button
            onClick={handleSetupAllModels}
            className="flex items-center space-x-2"
          >
            <Terminal className="h-4 w-4" />
            <span>Setup Models</span>
          </Button>
        </div>
      </div>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          <strong>Công cụ setup:</strong> Sử dụng script{" "}
          <code>python tools/1_setup_models.py</code>
          để tự động tải và cấu hình tất cả models cần thiết.
        </AlertDescription>
      </Alert>

      {/* System Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Models đang chạy
                </p>
                <p className="text-2xl font-bold text-green-900">
                  {activeModels}
                </p>
                <p className="text-sm text-gray-600">
                  / {models.length} tổng cộng
                </p>
              </div>
              <div className="p-3 rounded-full bg-green-100">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  VRAM đang dùng
                </p>
                <p className="text-2xl font-bold text-blue-900">
                  {totalVRAM.toFixed(1)} GB
                </p>
                <p className="text-sm text-gray-600">GPU memory</p>
              </div>
              <div className="p-3 rounded-full bg-blue-100">
                <HardDrive className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Tổng dung lượng
                </p>
                <p className="text-2xl font-bold text-orange-900">
                  {models
                    .reduce((total, m) => total + parseFloat(m.size), 0)
                    .toFixed(1)}{" "}
                  GB
                </p>
                <p className="text-sm text-gray-600">Disk space</p>
              </div>
              <div className="p-3 rounded-full bg-orange-100">
                <Cpu className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Models Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {models.map((model) => (
          <ModelCard key={model.id} model={model} />
        ))}
      </div>

      {/* Setup Tools */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Terminal className="h-5 w-5" />
            <span>Công cụ quản lý</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">
              Các lệnh hữu ích:
            </h4>
            <div className="space-y-2 text-sm">
              <div className="flex items-center space-x-2">
                <code className="bg-gray-200 px-2 py-1 rounded">
                  python tools/1_setup_models.py
                </code>
                <span className="text-gray-600">
                  - Setup và kiểm tra tất cả models
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <code className="bg-gray-200 px-2 py-1 rounded">
                  python tools/1_setup_models.py --verify-only
                </code>
                <span className="text-gray-600">
                  - Chỉ kiểm tra không tải xuống
                </span>
              </div>
            </div>
          </div>

          <div className="flex space-x-3">
            <Button variant="outline" onClick={handleSetupAllModels}>
              <Terminal className="h-4 w-4 mr-2" />
              Chạy Setup Script
            </Button>
            <Button variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Kiểm tra Models
            </Button>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Tải xuống tất cả
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
