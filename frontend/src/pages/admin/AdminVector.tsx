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
  Database,
  RefreshCw,
  Trash2,
  Eye,
  Plus,
  CheckCircle,
  Clock,
  AlertTriangle,
  Info,
  HardDrive,
} from "lucide-react";

interface VectorCollection {
  id: string;
  name: string;
  displayName: string;
  documentCount: number;
  lastUpdated: string;
  status: "active" | "building" | "error";
  size: string;
  embeddings: number;
}

export default function AdminVector() {
  // Mock data - tĩnh không cần connect backend
  const [collections] = useState<VectorCollection[]>([
    {
      id: "legal_documents",
      name: "legal_documents",
      displayName: "Tài liệu pháp luật",
      documentCount: 105,
      lastUpdated: "2024-01-15",
      status: "active",
      size: "450 MB",
      embeddings: 2847,
    },
    {
      id: "regulations",
      name: "regulations",
      displayName: "Quy định và thông tư",
      documentCount: 67,
      lastUpdated: "2024-01-12",
      status: "active",
      size: "320 MB",
      embeddings: 1923,
    },
    {
      id: "sample_questions",
      name: "sample_questions",
      displayName: "Câu hỏi mẫu",
      documentCount: 0,
      lastUpdated: "2024-01-10",
      status: "building",
      size: "0 MB",
      embeddings: 0,
    },
  ]);

  const [isRefreshing, setIsRefreshing] = useState(false);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "text-green-600 bg-green-50 border-green-200";
      case "building":
        return "text-blue-600 bg-blue-50 border-blue-200";
      case "error":
        return "text-red-600 bg-red-50 border-red-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <CheckCircle className="h-4 w-4" />;
      case "building":
        return <Clock className="h-4 w-4" />;
      case "error":
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return <Database className="h-4 w-4" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "active":
        return "Hoạt động";
      case "building":
        return "Đang xây dựng";
      case "error":
        return "Lỗi";
      default:
        return "Không xác định";
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    // TODO: Implement actual refresh from backend
    setTimeout(() => {
      setIsRefreshing(false);
    }, 2000);
  };

  const handleRebuildCollection = (collectionId: string) => {
    // TODO: Implement rebuild collection
    console.log("Rebuild collection:", collectionId);
    alert(`Sẽ rebuild collection: ${collectionId}`);
  };

  const handleDeleteCollection = (collectionId: string) => {
    // TODO: Implement delete collection
    if (confirm("Bạn có chắc muốn xóa collection này?")) {
      console.log("Delete collection:", collectionId);
    }
  };

  const handleCreateNewCollection = () => {
    // TODO: Implement create new collection
    console.log("Create new collection");
    alert("Tính năng tạo collection mới sẽ được phát triển");
  };

  const CollectionCard = ({ collection }: { collection: VectorCollection }) => (
    <Card className="border-2">
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <Database className="h-6 w-6 text-blue-600 mt-1" />
            <div>
              <CardTitle className="text-lg">
                {collection.displayName}
              </CardTitle>
              <p className="text-sm text-gray-500 mt-1">{collection.name}</p>
            </div>
          </div>
          <div
            className={`flex items-center space-x-1 px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(
              collection.status
            )}`}
          >
            {getStatusIcon(collection.status)}
            <span>{getStatusText(collection.status)}</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="bg-blue-50 p-3 rounded-lg">
            <p className="text-xl font-bold text-blue-900">
              {collection.documentCount}
            </p>
            <p className="text-xs text-blue-700">Tài liệu</p>
          </div>
          <div className="bg-green-50 p-3 rounded-lg">
            <p className="text-xl font-bold text-green-900">
              {collection.embeddings.toLocaleString()}
            </p>
            <p className="text-xs text-green-700">Embeddings</p>
          </div>
          <div className="bg-orange-50 p-3 rounded-lg">
            <p className="text-xl font-bold text-orange-900">
              {collection.size}
            </p>
            <p className="text-xs text-orange-700">Dung lượng</p>
          </div>
        </div>

        {/* Last Updated */}
        <div className="text-sm text-gray-500">
          Cập nhật cuối: {collection.lastUpdated}
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            className="flex items-center space-x-1"
          >
            <Eye className="h-4 w-4" />
            <span>Xem</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleRebuildCollection(collection.id)}
            className="flex items-center space-x-1"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Rebuild</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDeleteCollection(collection.id)}
            className="flex items-center space-x-1 text-red-600 hover:text-red-700"
          >
            <Trash2 className="h-4 w-4" />
            <span>Xóa</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const totalEmbeddings = collections.reduce(
    (sum, col) => sum + col.embeddings,
    0
  );
  const totalDocuments = collections.reduce(
    (sum, col) => sum + col.documentCount,
    0
  );
  const activeCollections = collections.filter(
    (col) => col.status === "active"
  ).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Quản lý Cơ sở dữ liệu Vector
          </h1>
          <p className="text-gray-600 mt-2">
            Quản lý các collection văn bản đã được embedding hóa
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-2"
          >
            <RefreshCw
              className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`}
            />
            <span>Làm mới</span>
          </Button>
          <Button
            onClick={handleCreateNewCollection}
            className="flex items-center space-x-2"
          >
            <Plus className="h-4 w-4" />
            <span>Tạo Collection</span>
          </Button>
        </div>
      </div>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          <strong>Lưu ý:</strong> Các collection này chứa dữ liệu đã được
          embedding hóa để tìm kiếm. Rebuild sẽ tạo lại tất cả embeddings từ tài
          liệu gốc.
        </AlertDescription>
      </Alert>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Tổng Collections
                </p>
                <p className="text-2xl font-bold text-blue-900">
                  {collections.length}
                </p>
                <p className="text-sm text-green-600">
                  {activeCollections} đang hoạt động
                </p>
              </div>
              <div className="p-3 rounded-full bg-blue-100">
                <Database className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Tổng Tài liệu
                </p>
                <p className="text-2xl font-bold text-green-900">
                  {totalDocuments}
                </p>
                <p className="text-sm text-gray-600">Đã được xử lý</p>
              </div>
              <div className="p-3 rounded-full bg-green-100">
                <HardDrive className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Tổng Embeddings
                </p>
                <p className="text-2xl font-bold text-orange-900">
                  {totalEmbeddings.toLocaleString()}
                </p>
                <p className="text-sm text-gray-600">Vector chunks</p>
              </div>
              <div className="p-3 rounded-full bg-orange-100">
                <RefreshCw className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Collections Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {collections.map((collection) => (
          <CollectionCard key={collection.id} collection={collection} />
        ))}
      </div>

      {/* Build Tools */}
      <Card>
        <CardHeader>
          <CardTitle>Công cụ xây dựng Vector Database</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">
              Các bước xây dựng:
            </h4>
            <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
              <li>
                Chuẩn bị tài liệu trong thư mục{" "}
                <code className="bg-gray-200 px-1 rounded">
                  backend/data/documents/
                </code>
              </li>
              <li>
                Chạy tool{" "}
                <code className="bg-gray-200 px-1 rounded">
                  python tools/2_build_vectordb.py
                </code>
              </li>
              <li>Chọn collection và cấu hình embedding</li>
              <li>Hệ thống sẽ tự động tạo embeddings</li>
            </ol>
          </div>

          <div className="flex space-x-3">
            <Button variant="outline" className="flex items-center space-x-2">
              <RefreshCw className="h-4 w-4" />
              <span>Rebuild All Collections</span>
            </Button>
            <Button variant="outline" className="flex items-center space-x-2">
              <Database className="h-4 w-4" />
              <span>Backup Database</span>
            </Button>
            <Button variant="outline" className="flex items-center space-x-2">
              <Eye className="h-4 w-4" />
              <span>Xem Log Build</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
