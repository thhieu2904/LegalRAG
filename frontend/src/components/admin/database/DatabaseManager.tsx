/**
 * 📚 DATABASE MANAGER - Integrated Collections & Documents View
 * Combines collections listing with document viewing functionality
 */

import { useState, useEffect } from "react";
import { Card, CardContent } from "../../../components/ui/card";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import { Badge } from "../../../components/ui/badge";
import {
  FolderOpen,
  RefreshCw,
  Search,
  FileText,
  AlertCircle,
  ArrowLeft,
  Database,
  Eye,
  HelpCircle,
  FormInput,
  Calendar,
  Building,
  DollarSign,
  Clock,
} from "lucide-react";
import {
  fetchCollections,
  fetchCollectionDocuments,
  type AdminCollection,
  type AdminDocument,
} from "../../../api/admin-api";
import { formatCollectionName } from "../../../api/collection-mapping";

export default function DatabaseManager() {
  // State management
  const [collections, setCollections] = useState<AdminCollection[]>([]);
  const [selectedCollection, setSelectedCollection] =
    useState<AdminCollection | null>(null);
  const [documents, setDocuments] = useState<AdminDocument[]>([]);
  const [isLoadingCollections, setIsLoadingCollections] = useState(false);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  // Load collections on mount
  useEffect(() => {
    loadCollections();
  }, []);

  const loadCollections = async () => {
    try {
      setIsLoadingCollections(true);
      setError(null);
      console.log("🗃️ Loading collections from admin API...");

      const data = await fetchCollections();
      setCollections(data);

      console.log(`✅ Loaded ${data.length} collections`);
    } catch (err) {
      console.error("❌ Error loading collections:", err);
      setError("Không thể tải danh sách collections. Vui lòng thử lại.");
    } finally {
      setIsLoadingCollections(false);
    }
  };

  const loadDocuments = async (collection: AdminCollection) => {
    try {
      setIsLoadingDocuments(true);
      setError(null);
      console.log(`📄 Loading documents for collection: ${collection.name}`);

      const data = await fetchCollectionDocuments(collection.name);
      setDocuments(data);
      setSelectedCollection(collection);

      console.log(`✅ Loaded ${data.length} documents for ${collection.name}`);
    } catch (err) {
      console.error(`❌ Error loading documents for ${collection.name}:`, err);
      setError("Không thể tải danh sách documents. Vui lòng thử lại.");
    } finally {
      setIsLoadingDocuments(false);
    }
  };

  const handleViewDocuments = (collection: AdminCollection) => {
    console.log("📄 View documents for:", collection.name);
    loadDocuments(collection);
  };

  const handleBackToCollections = () => {
    setSelectedCollection(null);
    setDocuments([]);
    setSearchQuery("");
  };

  const handleRefresh = () => {
    if (selectedCollection) {
      loadDocuments(selectedCollection);
    } else {
      loadCollections();
    }
  };

  // Filter logic
  const filteredCollections = collections.filter(
    (collection) =>
      formatCollectionName(collection.name)
        .toLowerCase()
        .includes(searchQuery.toLowerCase()) ||
      collection.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredDocuments = documents.filter(
    (doc) =>
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.executing_agency.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
        <div className="flex items-center gap-3">
          {selectedCollection && (
            <Button
              onClick={handleBackToCollections}
              variant="outline"
              size="sm"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Quay lại
            </Button>
          )}
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Database className="w-6 h-6" />
              {selectedCollection ? (
                <>Documents - {formatCollectionName(selectedCollection.name)}</>
              ) : (
                "Quản lý Collections"
              )}
            </h1>
            <p className="text-muted-foreground">
              {selectedCollection
                ? `${filteredDocuments.length} documents từ collection`
                : `${filteredCollections.length} collections có sẵn`}
            </p>
          </div>
        </div>
        <Button
          onClick={handleRefresh}
          disabled={isLoadingCollections || isLoadingDocuments}
          variant="outline"
        >
          <RefreshCw
            className={`w-4 h-4 mr-2 ${
              isLoadingCollections || isLoadingDocuments ? "animate-spin" : ""
            }`}
          />
          Làm mới
        </Button>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder={
                selectedCollection
                  ? "Tìm kiếm documents..."
                  : "Tìm kiếm collections..."
              }
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Collections View */}
      {!selectedCollection && (
        <div className="space-y-4">
          {isLoadingCollections ? (
            // Loading skeleton for collections
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, index) => (
                <Card key={index} className="animate-pulse">
                  <CardContent className="pt-6">
                    <div className="space-y-3">
                      <div className="h-6 bg-gray-200 rounded w-3/4"></div>
                      <div className="h-4 bg-gray-200 rounded w-full"></div>
                      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                      <div className="flex justify-between items-center">
                        <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                        <div className="h-8 bg-gray-200 rounded w-20"></div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : filteredCollections.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <FolderOpen className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-muted-foreground mb-2">
                    {searchQuery
                      ? "Không tìm thấy collections"
                      : "Chưa có collections"}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {searchQuery
                      ? "Thử thay đổi từ khóa tìm kiếm"
                      : "Hệ thống chưa có collections nào"}
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredCollections.map((collection) => (
                <Card
                  key={collection.name}
                  className="hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => handleViewDocuments(collection)}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-3">
                      <FolderOpen className="w-8 h-8 text-blue-500" />
                      <Badge variant="secondary">
                        {collection.document_count} docs
                      </Badge>
                    </div>
                    <h3 className="font-semibold text-lg mb-2">
                      {formatCollectionName(collection.name)}
                    </h3>
                    <p className="text-sm text-muted-foreground mb-4 line-clamp-2 min-h-[2.5rem]">
                      {collection.description}
                    </p>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-muted-foreground">
                        {collection.metadata_exists
                          ? "✅ Metadata"
                          : "❌ No metadata"}
                      </span>
                      <Button size="sm" variant="outline">
                        <Eye className="w-4 h-4 mr-1" />
                        Xem
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Documents View */}
      {selectedCollection && (
        <div className="space-y-4">
          {isLoadingDocuments ? (
            // Loading skeleton for documents
            <div className="space-y-4">
              {Array.from({ length: 5 }).map((_, index) => (
                <Card key={index} className="animate-pulse">
                  <CardContent className="pt-6">
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <div className="h-6 bg-gray-200 rounded w-1/2"></div>
                        <div className="h-6 bg-gray-200 rounded w-16"></div>
                      </div>
                      <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                      <div className="h-4 bg-gray-200 rounded w-full"></div>
                      <div className="flex justify-between">
                        <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                        <div className="h-8 bg-gray-200 rounded w-20"></div>
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
                      ? "Thử thay đổi từ khóa tìm kiếm"
                      : "Collection này chưa có documents nào"}
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {filteredDocuments.map((doc) => (
                <Card
                  key={doc.doc_id}
                  className="hover:shadow-md transition-shadow"
                >
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <FileText className="w-5 h-5 text-blue-500" />
                          <Badge variant="outline">{doc.code}</Badge>
                          <Badge
                            variant={
                              doc.has_original_doc ? "default" : "secondary"
                            }
                          >
                            {doc.has_original_doc ? "✅ DOC" : "❌ NO DOC"}
                          </Badge>
                          <Badge
                            variant={
                              doc.has_processed_json ? "default" : "secondary"
                            }
                          >
                            {doc.has_processed_json ? "✅ JSON" : "❌ NO JSON"}
                          </Badge>
                        </div>
                        <h3 className="font-semibold text-lg mb-2">
                          {doc.title}
                        </h3>
                        <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground mb-3">
                          <div className="flex items-center gap-2">
                            <Building className="w-4 h-4" />
                            <span className="line-clamp-1">
                              {doc.executing_agency}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Calendar className="w-4 h-4" />
                            <span>{doc.effective_date}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <HelpCircle className="w-4 h-4" />
                            <span>{doc.question_count} câu hỏi</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <FormInput className="w-4 h-4" />
                            <span>
                              {doc.has_forms
                                ? `${doc.form_count} form`
                                : "Không có form"}
                            </span>
                          </div>
                        </div>
                        {doc.processing_time_text && (
                          <div className="flex items-start gap-2 text-sm text-muted-foreground mb-2">
                            <Clock className="w-4 h-4 mt-0.5" />
                            <span className="line-clamp-2">
                              {doc.processing_time_text}
                            </span>
                          </div>
                        )}
                        {doc.fee_text && (
                          <div className="flex items-start gap-2 text-sm text-muted-foreground">
                            <DollarSign className="w-4 h-4 mt-0.5" />
                            <span className="line-clamp-2">{doc.fee_text}</span>
                          </div>
                        )}
                      </div>
                      <div className="flex gap-2 ml-4">
                        <Button size="sm" variant="outline">
                          <Eye className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Summary */}
      {!isLoadingCollections && !isLoadingDocuments && (
        <Card className="bg-muted/50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-4">
                {selectedCollection ? (
                  <>
                    <span>
                      <strong>{filteredDocuments.length}</strong> documents hiển
                      thị
                      {searchQuery && ` (lọc từ ${documents.length})`}
                    </span>
                    <span>
                      Collection:{" "}
                      <strong>
                        {formatCollectionName(selectedCollection.name)}
                      </strong>
                    </span>
                  </>
                ) : (
                  <>
                    <span>
                      <strong>{filteredCollections.length}</strong> collections
                      hiển thị
                      {searchQuery && ` (lọc từ ${collections.length})`}
                    </span>
                    <span>
                      Tổng{" "}
                      <strong>
                        {collections.reduce(
                          (acc, col) => acc + col.document_count,
                          0
                        )}
                      </strong>{" "}
                      documents
                    </span>
                  </>
                )}
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
