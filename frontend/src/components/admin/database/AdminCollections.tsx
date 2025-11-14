/**
 * 🗃️ ADMIN COLLECTIONS COMPONENT - Mới hoàn toàn
 * Hiển thị danh sách collections từ admin API backend
 */

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import { Badge } from "../../../components/ui/badge";
import {
  FolderOpen,
  RefreshCw,
  Search,
  FileText,
  AlertCircle,
  Database,
  Eye,
} from "lucide-react";
import { fetchCollections, type AdminCollection } from "../../../api/admin-api";
import { formatCollectionName } from "../../../api/collection-mapping";

export default function AdminCollectionsManager() {
  // State management
  const [collections, setCollections] = useState<AdminCollection[]>([]);
  const [filteredCollections, setFilteredCollections] = useState<
    AdminCollection[]
  >([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  // Load collections on mount
  useEffect(() => {
    loadCollections();
  }, []);

  // Filter collections when search changes
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredCollections(collections);
    } else {
      const query = searchQuery.toLowerCase();
      const filtered = collections.filter(
        (collection) =>
          formatCollectionName(collection.name).toLowerCase().includes(query) ||
          collection.description.toLowerCase().includes(query) ||
          collection.name.toLowerCase().includes(query)
      );
      setFilteredCollections(filtered);
    }
  }, [collections, searchQuery]);

  const loadCollections = async () => {
    try {
      setIsLoading(true);
      setError(null);
      console.log("🗃️ Loading collections from admin API...");

      const data = await fetchCollections();
      setCollections(data);

      console.log(`✅ Loaded ${data.length} collections`);
    } catch (err) {
      console.error("❌ Error loading collections:", err);
      setError("Không thể tải danh sách collections. Vui lòng thử lại.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = () => {
    loadCollections();
  };

  const handleViewDocuments = (collection: AdminCollection) => {
    console.log("📄 View documents for:", collection.name);
    // Navigate to documents view - implement later
  };

  if (error) {
    return (
      <div className="p-6">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-600 mb-4">
              <AlertCircle className="w-5 h-5" />
              <span className="font-medium">Lỗi tải dữ liệu</span>
            </div>
            <p className="text-red-700 mb-4">{error}</p>
            <Button onClick={handleRefresh} variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              Thử lại
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Database className="w-6 h-6" />
            Quản lý Collections
          </h1>
          <p className="text-muted-foreground">
            Danh sách {collections.length} collections pháp luật
          </p>
        </div>
        <Button onClick={handleRefresh} disabled={isLoading} variant="outline">
          <RefreshCw
            className={`w-4 h-4 mr-2 ${isLoading ? "animate-spin" : ""}`}
          />
          Làm mới
        </Button>
      </div>

      {/* Search */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Tìm kiếm Collections</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Tìm kiếm theo tên collection hoặc mô tả..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Collections Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading ? (
          // Loading skeleton
          Array.from({ length: 6 }).map((_, index) => (
            <Card key={index} className="animate-pulse">
              <CardHeader>
                <div className="h-6 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="h-4 bg-gray-200 rounded"></div>
                  <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                  <div className="h-8 bg-gray-200 rounded w-1/3"></div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : filteredCollections.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <FolderOpen className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-muted-foreground mb-2">
              {searchQuery
                ? "Không tìm thấy collections"
                : "Chưa có collections"}
            </h3>
            <p className="text-sm text-muted-foreground">
              {searchQuery
                ? `Không có collection nào khớp với "${searchQuery}"`
                : "Hệ thống chưa có collections nào"}
            </p>
          </div>
        ) : (
          // Collections list
          filteredCollections.map((collection) => (
            <Card
              key={collection.name}
              className="hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => handleViewDocuments(collection)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg mb-2 flex items-center gap-2">
                      <FolderOpen className="w-5 h-5 text-blue-600" />
                      {formatCollectionName(collection.name)}
                    </CardTitle>
                    <p className="text-sm text-muted-foreground">
                      {collection.name}
                    </p>
                  </div>
                  <Badge variant="secondary" className="ml-2">
                    {collection.document_count} docs
                  </Badge>
                </div>
              </CardHeader>

              <CardContent>
                <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                  {collection.description}
                </p>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">
                      {collection.document_count} văn bản
                    </span>
                  </div>

                  <div className="flex items-center gap-1">
                    {collection.metadata_exists ? (
                      <Badge variant="default" className="text-xs">
                        Có metadata
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-xs">
                        Chưa có metadata
                      </Badge>
                    )}
                  </div>
                </div>

                <Button
                  className="w-full mt-4"
                  variant="outline"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleViewDocuments(collection);
                  }}
                >
                  <Eye className="w-4 h-4 mr-2" />
                  Xem Documents
                </Button>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Summary */}
      {!isLoading && collections.length > 0 && (
        <Card className="bg-muted/50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-4">
                <span>
                  <strong>{filteredCollections.length}</strong> collections
                  {searchQuery && ` (lọc từ ${collections.length})`}
                </span>
                <span>
                  <strong>
                    {filteredCollections.reduce(
                      (sum, col) => sum + col.document_count,
                      0
                    )}
                  </strong>{" "}
                  văn bản tổng cộng
                </span>
              </div>
              <span className="text-muted-foreground">
                Dữ liệu từ Admin API
              </span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
