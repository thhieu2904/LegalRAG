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
        return "vector-status-active";
      case "building":
        return "vector-status-building";
      case "error":
        return "vector-status-error";
      default:
        return "vector-status-default";
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
    <Card className="vector-collection-card">
      <CardHeader className="vector-card-header">
        <div className="vector-card-header-content">
          <div className="vector-card-icon-title">
            <Database className="vector-card-icon" />
            <div>
              <CardTitle className="vector-card-title">
                {collection.displayName}
              </CardTitle>
              <p className="vector-card-subtitle">{collection.name}</p>
            </div>
          </div>
          <div className={`vector-status ${getStatusColor(collection.status)}`}>
            {getStatusIcon(collection.status)}
            <span>{getStatusText(collection.status)}</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="vector-card-content">
        {/* Stats */}
        <div className="vector-card-stats">
          <div className="vector-card-stat vector-card-stat-blue">
            <p className="vector-card-stat-value">{collection.documentCount}</p>
            <p className="vector-card-stat-label">Tài liệu</p>
          </div>
          <div className="vector-card-stat vector-card-stat-green">
            <p className="vector-card-stat-value">
              {collection.embeddings.toLocaleString()}
            </p>
            <p className="vector-card-stat-label">Embeddings</p>
          </div>
          <div className="vector-card-stat vector-card-stat-orange">
            <p className="vector-card-stat-value">{collection.size}</p>
            <p className="vector-card-stat-label">Dung lượng</p>
          </div>
        </div>

        {/* Last Updated */}
        <div className="vector-card-updated">
          Cập nhật cuối: {collection.lastUpdated}
        </div>

        {/* Actions */}
        <div className="vector-card-actions">
          <Button
            variant="outline"
            size="sm"
            className="shared-button shared-button-small"
          >
            <Eye className="w-4 h-4" />
            Xem
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleRebuildCollection(collection.id)}
            className="shared-button shared-button-small"
          >
            <RefreshCw className="w-4 h-4" />
            Rebuild
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDeleteCollection(collection.id)}
            className="shared-button shared-button-small shared-button-danger"
          >
            <Trash2 className="w-4 h-4" />
            Xóa
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
    <div className="admin-page-container admin-vector-page">
      <div className="admin-page-header-section">
        <div className="admin-page-header-content">
          <h1 className="admin-page-title-main">
            Quản lý Cơ sở dữ liệu Vector
          </h1>
          <p className="admin-page-subtitle-main">
            Quản lý các collection văn bản đã được embedding hóa
          </p>
        </div>
        <div className="admin-page-actions-main">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="shared-button"
          >
            <RefreshCw
              className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`}
            />
            Làm mới
          </Button>
          <Button
            onClick={handleCreateNewCollection}
            className="shared-button shared-button-primary"
          >
            <Plus className="w-4 h-4" />
            Tạo Collection
          </Button>
        </div>
      </div>

      <div className="admin-content-section">
        <Alert className="vector-alert">
          <Info className="w-4 h-4" />
          <AlertDescription>
            <strong>Lưu ý:</strong> Các collection này chứa dữ liệu đã được
            embedding hóa để tìm kiếm. Rebuild sẽ tạo lại tất cả embeddings từ
            tài liệu gốc.
          </AlertDescription>
        </Alert>
      </div>

      {/* Summary Stats */}
      <div className="admin-content-section">
        <div className="admin-vector-stats-grid">
          <Card className="vector-stat-card">
            <CardContent className="vector-stat-content">
              <div className="vector-stat-details">
                <p className="vector-stat-label">Tổng Collections</p>
                <p className="vector-stat-value">{collections.length}</p>
                <p className="vector-stat-note vector-stat-success">
                  {activeCollections} đang hoạt động
                </p>
              </div>
              <div className="vector-stat-icon vector-stat-icon-blue">
                <Database className="w-6 h-6" />
              </div>
            </CardContent>
          </Card>

          <Card className="vector-stat-card">
            <CardContent className="vector-stat-content">
              <div className="vector-stat-details">
                <p className="vector-stat-label">Tổng Tài liệu</p>
                <p className="vector-stat-value">{totalDocuments}</p>
                <p className="vector-stat-note">Đã được xử lý</p>
              </div>
              <div className="vector-stat-icon vector-stat-icon-green">
                <HardDrive className="w-6 h-6" />
              </div>
            </CardContent>
          </Card>

          <Card className="vector-stat-card">
            <CardContent className="vector-stat-content">
              <div className="vector-stat-details">
                <p className="vector-stat-label">Tổng Embeddings</p>
                <p className="vector-stat-value">
                  {totalEmbeddings.toLocaleString()}
                </p>
                <p className="vector-stat-note">Vector chunks</p>
              </div>
              <div className="vector-stat-icon vector-stat-icon-orange">
                <RefreshCw className="w-6 h-6" />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Collections Grid */}
      <div className="admin-content-section">
        <div className="admin-vector-collections-grid">
          {collections.map((collection) => (
            <CollectionCard key={collection.id} collection={collection} />
          ))}
        </div>
      </div>

      {/* Build Tools */}
      <div className="admin-content-section">
        <Card className="vector-build-tools">
          <CardHeader>
            <CardTitle className="admin-card-title">
              Công cụ xây dựng Vector Database
            </CardTitle>
          </CardHeader>
          <CardContent className="vector-build-content">
            <div className="vector-build-steps">
              <h4 className="vector-build-steps-title">Các bước xây dựng:</h4>
              <ol className="vector-build-steps-list">
                <li>
                  Chuẩn bị tài liệu trong thư mục{" "}
                  <code className="vector-code">backend/data/documents/</code>
                </li>
                <li>
                  Chạy tool{" "}
                  <code className="vector-code">
                    python tools/2_build_vectordb.py
                  </code>
                </li>
                <li>Chọn collection và cấu hình embedding</li>
                <li>Hệ thống sẽ tự động tạo embeddings</li>
              </ol>
            </div>

            <div className="vector-build-actions">
              <Button variant="outline" className="shared-button">
                <RefreshCw className="w-4 h-4" />
                Rebuild All Collections
              </Button>
              <Button variant="outline" className="shared-button">
                <Database className="w-4 h-4" />
                Backup Database
              </Button>
              <Button variant="outline" className="shared-button">
                <Eye className="w-4 h-4" />
                Xem Log Build
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
