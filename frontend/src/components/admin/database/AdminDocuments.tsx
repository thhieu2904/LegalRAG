/**
 * 📄 ADMIN DOCUMENTS COMPONENT - Mới hoàn toàn
 * Hiển thị danh sách documents từ admin API backend
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
  FileText,
  RefreshCw,
  Search,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  HelpCircle,
  FormInput,
  Calendar,
  Building,
  DollarSign,
  Clock,
  Eye,
} from "lucide-react";
import {
  fetchCollectionDocuments,
  fetchCollections,
  type AdminDocument,
  type AdminCollection,
} from "../../../api/admin-api";
import { formatCollectionName } from "../../../api/collection-mapping";

interface AdminDocumentsManagerProps {
  collectionName?: string;
  onBack?: () => void;
}

export default function AdminDocumentsManager({
  collectionName,
  onBack,
}: AdminDocumentsManagerProps) {
  // State management
  const [documents, setDocuments] = useState<AdminDocument[]>([]);
  const [filteredDocuments, setFilteredDocuments] = useState<AdminDocument[]>(
    []
  );
  const [collections, setCollections] = useState<AdminCollection[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<string>(
    collectionName || ""
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  // Load collections on mount
  useEffect(() => {
    loadCollections();
  }, []);

  // Load documents when collection changes
  useEffect(() => {
    if (selectedCollection) {
      loadDocuments(selectedCollection);
    } else {
      setDocuments([]);
      setFilteredDocuments([]);
    }
  }, [selectedCollection]);

  // Filter documents when search changes
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredDocuments(documents);
    } else {
      const query = searchQuery.toLowerCase();
      const filtered = documents.filter(
        (doc) =>
          doc.title.toLowerCase().includes(query) ||
          doc.code.toLowerCase().includes(query) ||
          doc.executing_agency.toLowerCase().includes(query)
      );
      setFilteredDocuments(filtered);
    }
  }, [documents, searchQuery]);

  const loadCollections = async () => {
    try {
      const data = await fetchCollections();
      setCollections(data);
    } catch (err) {
      console.error("❌ Error loading collections:", err);
    }
  };

  const loadDocuments = async (collection: string) => {
    try {
      setIsLoading(true);
      setError(null);
      console.log(`📄 Loading documents for collection: ${collection}`);

      const data = await fetchCollectionDocuments(collection);
      setDocuments(data);

      console.log(`✅ Loaded ${data.length} documents`);
    } catch (err) {
      console.error(`❌ Error loading documents for ${collection}:`, err);
      setError(`Không thể tải documents cho collection ${collection}`);
      setDocuments([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = () => {
    if (selectedCollection) {
      loadDocuments(selectedCollection);
    }
  };

  const formatFee = (feeVnd: number, feeText: string) => {
    if (feeVnd > 0) {
      return `${feeVnd.toLocaleString("vi-VN")} VNĐ`;
    }
    if (feeText.toLowerCase().includes("miễn")) {
      return "Miễn phí";
    }
    return "Xem chi tiết";
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
            <div className="flex gap-2">
              <Button onClick={handleRefresh} variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                Thử lại
              </Button>
              {onBack && (
                <Button onClick={onBack} variant="ghost">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Quay lại
                </Button>
              )}
            </div>
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
          <div className="flex items-center gap-2 mb-2">
            {onBack && (
              <Button onClick={onBack} variant="ghost" size="sm">
                <ArrowLeft className="w-4 h-4" />
              </Button>
            )}
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <FileText className="w-6 h-6" />
              Quản lý Documents
            </h1>
          </div>
          <p className="text-muted-foreground">
            {selectedCollection
              ? `${documents.length} documents trong ${formatCollectionName(
                  selectedCollection
                )}`
              : "Chọn collection để xem documents"}
          </p>
        </div>
        <Button
          onClick={handleRefresh}
          disabled={isLoading || !selectedCollection}
          variant="outline"
        >
          <RefreshCw
            className={`w-4 h-4 mr-2 ${isLoading ? "animate-spin" : ""}`}
          />
          Làm mới
        </Button>
      </div>

      {/* Collection Selector */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Chọn Collection</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <select
            className="w-full px-3 py-2 border border-input bg-background rounded-md text-sm"
            value={selectedCollection}
            onChange={(e) => setSelectedCollection(e.target.value)}
          >
            <option value="">-- Chọn collection --</option>
            {collections.map((collection) => (
              <option key={collection.name} value={collection.name}>
                {formatCollectionName(collection.name)} (
                {collection.document_count})
              </option>
            ))}
          </select>

          {selectedCollection && (
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Tìm kiếm documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Documents List */}
      {selectedCollection && (
        <div className="space-y-4">
          {isLoading ? (
            // Loading skeleton
            <div className="space-y-4">
              {Array.from({ length: 5 }).map((_, index) => (
                <Card key={index} className="animate-pulse">
                  <CardContent className="pt-6">
                    <div className="space-y-3">
                      <div className="h-6 bg-gray-200 rounded w-3/4"></div>
                      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                      <div className="flex gap-2">
                        <div className="h-6 bg-gray-200 rounded w-16"></div>
                        <div className="h-6 bg-gray-200 rounded w-20"></div>
                        <div className="h-6 bg-gray-200 rounded w-24"></div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : filteredDocuments.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-muted-foreground mb-2">
                    {searchQuery
                      ? "Không tìm thấy documents"
                      : "Chưa có documents"}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {searchQuery
                      ? `Không có document nào khớp với "${searchQuery}"`
                      : "Collection này chưa có documents"}
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            // Documents list
            <div className="space-y-4">
              {filteredDocuments.map((document) => (
                <Card
                  key={document.doc_id}
                  className="hover:shadow-md transition-shadow"
                >
                  <CardContent className="pt-6">
                    <div className="space-y-4">
                      {/* Header */}
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold mb-2">
                            {document.title}
                          </h3>
                          <div className="flex items-center gap-2 mb-2">
                            <Badge variant="outline">{document.code}</Badge>
                            <Badge variant="secondary">{document.doc_id}</Badge>
                            <Badge
                              variant={
                                document.status === "active"
                                  ? "default"
                                  : "destructive"
                              }
                            >
                              {document.status}
                            </Badge>
                          </div>
                        </div>
                        <Button variant="outline" size="sm">
                          <Eye className="w-4 h-4 mr-2" />
                          Chi tiết
                        </Button>
                      </div>

                      {/* Info Grid */}
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                        <div className="flex items-center gap-2">
                          <Building className="w-4 h-4 text-muted-foreground" />
                          <div>
                            <p className="text-muted-foreground">
                              Cơ quan thực hiện
                            </p>
                            <p className="font-medium line-clamp-2">
                              {document.executing_agency}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4 text-muted-foreground" />
                          <div>
                            <p className="text-muted-foreground">
                              Ngày hiệu lực
                            </p>
                            <p className="font-medium">
                              {document.effective_date}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <DollarSign className="w-4 h-4 text-muted-foreground" />
                          <div>
                            <p className="text-muted-foreground">Lệ phí</p>
                            <p className="font-medium">
                              {formatFee(document.fee_vnd, document.fee_text)}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4 text-muted-foreground" />
                          <div>
                            <p className="text-muted-foreground">Đối tượng</p>
                            <p className="font-medium">
                              {document.applicant_type.join(", ")}
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Features */}
                      <div className="flex flex-wrap gap-2">
                        {document.has_questions && (
                          <div className="flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">
                            <HelpCircle className="w-3 h-3" />
                            {document.question_count} câu hỏi
                          </div>
                        )}
                        {document.has_forms && (
                          <div className="flex items-center gap-1 px-2 py-1 bg-green-50 text-green-700 rounded text-xs">
                            <FormInput className="w-3 h-3" />
                            {document.form_count} biểu mẫu
                          </div>
                        )}
                        {document.has_original_doc && (
                          <div className="flex items-center gap-1 px-2 py-1 bg-purple-50 text-purple-700 rounded text-xs">
                            <CheckCircle className="w-3 h-3" />
                            Có file gốc
                          </div>
                        )}
                        {document.has_processed_json && (
                          <div className="flex items-center gap-1 px-2 py-1 bg-orange-50 text-orange-700 rounded text-xs">
                            <CheckCircle className="w-3 h-3" />
                            Đã xử lý
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Summary */}
          {!isLoading && documents.length > 0 && (
            <Card className="bg-muted/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-4">
                    <span>
                      <strong>{filteredDocuments.length}</strong> documents
                      {searchQuery && ` (lọc từ ${documents.length})`}
                    </span>
                    <span>
                      Tổng{" "}
                      <strong>
                        {filteredDocuments.reduce(
                          (sum, doc) => sum + doc.question_count,
                          0
                        )}
                      </strong>{" "}
                      câu hỏi
                    </span>
                    <span>
                      Tổng{" "}
                      <strong>
                        {filteredDocuments.reduce(
                          (sum, doc) => sum + doc.form_count,
                          0
                        )}
                      </strong>{" "}
                      biểu mẫu
                    </span>
                  </div>
                  <span className="text-muted-foreground">
                    Collection: {formatCollectionName(selectedCollection)}
                  </span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
