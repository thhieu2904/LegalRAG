/**
 * ❓ QUESTIONS MANAGER - 3-Step Navigation: Collections → Documents → Questions
 * Follow exact same pattern as DatabaseManager with one additional step for questions
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
  Eye,
  HelpCircle,
  MessageSquare,
  BookOpen,
  Calendar,
  Building,
} from "lucide-react";
import {
  fetchCollections,
  fetchCollectionDocuments,
  fetchDocumentQuestions,
  type AdminCollection,
  type AdminDocument,
} from "../../../api/admin-api";
import { formatCollectionName } from "../../../api/collection-mapping";

interface DocumentQuestions {
  collection: string;
  doc_id: string;
  document_title: string;
  questions: Array<{
    id: string;
    text: string;
    type: 'main' | 'variant';
    order: number;
    variant_index?: number;
  }>;
  total: number;
  has_questions: boolean;
}

export default function QuestionsManager() {
  // State management - exactly like DatabaseManager
  const [collections, setCollections] = useState<AdminCollection[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<AdminCollection | null>(null);
  const [documents, setDocuments] = useState<AdminDocument[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<AdminDocument | null>(null);
  const [documentQuestions, setDocumentQuestions] = useState<DocumentQuestions | null>(null);
  
  const [isLoadingCollections, setIsLoadingCollections] = useState(false);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  // Load collections on mount - exactly like DatabaseManager
  useEffect(() => {
    loadCollections();
  }, []);

  const loadCollections = async () => {
    try {
      setIsLoadingCollections(true);
      setError(null);
      console.log("🗃️ Loading collections for questions...");

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

  const loadQuestions = async (document: AdminDocument) => {
    if (!selectedCollection) return;
    
    try {
      setIsLoadingQuestions(true);
      setError(null);
      console.log(`❓ Loading questions for document: ${document.doc_id}`);

      const data = await fetchDocumentQuestions(selectedCollection.name, document.doc_id);
      setDocumentQuestions(data);
      setSelectedDocument(document);

      console.log(`✅ Loaded questions for document ${document.doc_id}`);
    } catch (err) {
      console.error("❌ Error loading questions:", err);
      setError("Không thể tải questions of document. Vui lòng thử lại.");
    } finally {
      setIsLoadingQuestions(false);
    }
  };

  const handleViewDocuments = (collection: AdminCollection) => {
    console.log("📄 View documents for:", collection.name);
    loadDocuments(collection);
  };

  const handleViewQuestions = (document: AdminDocument) => {
    console.log("❓ View questions for:", document.doc_id);
    loadQuestions(document);
  };

  const handleBackToCollections = () => {
    setSelectedCollection(null);
    setSelectedDocument(null);
    setDocuments([]);
    setDocumentQuestions(null);
    setSearchQuery("");
  };

  const handleBackToDocuments = () => {
    setSelectedDocument(null);
    setDocumentQuestions(null);
    setSearchQuery("");
  };

  const handleRefresh = () => {
    if (selectedDocument && selectedCollection) {
      loadQuestions(selectedDocument);
    } else if (selectedCollection) {
      loadDocuments(selectedCollection);
    } else {
      loadCollections();
    }
  };

  // Filter logic - exactly like DatabaseManager
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

  // Error handling - exactly like DatabaseManager
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
      {/* Header - exactly like DatabaseManager */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {selectedDocument && (
            <>
              <Button
                onClick={handleBackToCollections}
                variant="outline"
                size="sm"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Collections
              </Button>
              <Button
                onClick={handleBackToDocuments}
                variant="outline"
                size="sm"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Documents
              </Button>
            </>
          )}
          {selectedCollection && !selectedDocument && (
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
              <HelpCircle className="w-6 h-6" />
              {selectedDocument ? (
                <>Questions - {documentQuestions?.document_title || selectedDocument.title}</>
              ) : selectedCollection ? (
                <>Documents - {formatCollectionName(selectedCollection.name)}</>
              ) : (
                "Quản lý Questions"
              )}
            </h1>
            <p className="text-muted-foreground">
              {selectedDocument && documentQuestions ? (
                `${documentQuestions.total} questions từ document`
              ) : selectedCollection ? (
                `${filteredDocuments.length} documents từ collection`
              ) : (
                `${filteredCollections.length} collections có sẵn`
              )}
            </p>
          </div>
        </div>
        <Button
          onClick={handleRefresh}
          disabled={isLoadingCollections || isLoadingDocuments || isLoadingQuestions}
          variant="outline"
        >
          <RefreshCw
            className={`w-4 h-4 mr-2 ${
              isLoadingCollections || isLoadingDocuments || isLoadingQuestions ? "animate-spin" : ""
            }`}
          />
          Làm mới
        </Button>
      </div>

      {/* Search - exactly like DatabaseManager */}
      {!selectedDocument && (
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
      )}

      {/* Collections View - exactly like DatabaseManager */}
      {!selectedCollection && (
        <div className="space-y-4">
          {isLoadingCollections ? (
            // Loading skeleton
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
                    {searchQuery ? "Không tìm thấy collections" : "Chưa có collections"}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {searchQuery
                      ? "Thử thay đổi từ khóa tìm kiếm"
                      : "Hệ thống chưa có collections nào"
                    }
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
                        {collection.document_count} documents
                      </span>
                      <Button size="sm" variant="outline">
                        <Eye className="w-4 h-4 mr-1" />
                        Xem documents
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Documents View - exactly like DatabaseManager */}
      {selectedCollection && !selectedDocument && (
        <div className="space-y-4">
          {isLoadingDocuments ? (
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
                    {searchQuery ? "Không tìm thấy documents" : "Chưa có documents"}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {searchQuery
                      ? "Thử thay đổi từ khóa tìm kiếm"
                      : "Collection này chưa có documents nào"
                    }
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {filteredDocuments.map((document) => (
                <Card
                  key={document.doc_id}
                  className="hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => handleViewQuestions(document)}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <FileText className="w-5 h-5 text-green-500" />
                          <Badge variant="outline">{document.doc_id}</Badge>
                          <Badge variant="secondary">{document.code}</Badge>
                          {document.has_questions && (
                            <Badge variant="default" className="bg-orange-500">
                              <MessageSquare className="w-3 h-3 mr-1" />
                              {document.question_count} Q&A
                            </Badge>
                          )}
                        </div>
                        <h4 className="font-medium text-base mb-2">
                          {document.title}
                        </h4>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground mb-2">
                          <span className="flex items-center gap-1">
                            <Building className="w-3 h-3" />
                            {document.executing_agency}
                          </span>
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {document.effective_date}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          {document.applicant_type.map((type, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              {type}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <Button size="sm" variant="outline">
                        <MessageSquare className="w-4 h-4 mr-1" />
                        Xem Q&A
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Questions View - NEW STEP */}
      {selectedDocument && (
        <div className="space-y-6">
          {isLoadingQuestions ? (
            // Loading skeleton
            <Card className="animate-pulse">
              <CardContent className="pt-6">
                <div className="space-y-4">
                  <div className="h-6 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                  <div className="space-y-2">
                    {Array.from({ length: 5 }).map((_, index) => (
                      <div key={index} className="h-4 bg-gray-200 rounded w-full"></div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : !documentQuestions ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-muted-foreground mb-2">
                    Chưa có questions
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Document này chưa có questions nào
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Main Question */}
              {documentQuestions.questions.filter(q => q.type === 'main').map((mainQ) => (
                <Card key={mainQ.id} className="border-blue-200 bg-blue-50">
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-3">
                      <MessageSquare className="w-6 h-6 text-blue-600 mt-1" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="default" className="bg-blue-600">
                            Câu hỏi chính
                          </Badge>
                        </div>
                        <h3 className="text-lg font-medium text-blue-900 mb-2">
                          {mainQ.text}
                        </h3>
                        <p className="text-sm text-blue-700">
                          Câu hỏi chính của document này
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {/* Question Variants */}
              {documentQuestions.questions.filter(q => q.type === 'variant').length > 0 && (
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-2 mb-4">
                      <BookOpen className="w-5 h-5 text-green-600" />
                      <h3 className="text-lg font-medium">
                        Biến thể câu hỏi ({documentQuestions.questions.filter(q => q.type === 'variant').length})
                      </h3>
                    </div>
                    
                    <div className="space-y-3">
                      {documentQuestions.questions
                        .filter(q => q.type === 'variant')
                        .sort((a, b) => a.order - b.order)
                        .map((variant, index) => (
                        <div
                          key={variant.id}
                          className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                        >
                          <Badge variant="outline" className="mt-1">
                            {index + 1}
                          </Badge>
                          <p className="text-sm text-gray-700 flex-1">
                            {variant.text}
                          </p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      )}

      {/* Summary - exactly like DatabaseManager */}
      {!isLoadingCollections && !isLoadingDocuments && !isLoadingQuestions && (
        <Card className="bg-muted/50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-4">
                {selectedDocument && documentQuestions ? (
                  <>
                    <span>
                      Document: <strong>{documentQuestions.document_title}</strong>
                    </span>
                    <span>
                      Questions: <strong>{documentQuestions.questions.filter(q => q.type === 'main').length}</strong> main + <strong>{documentQuestions.questions.filter(q => q.type === 'variant').length}</strong> variants
                    </span>
                  </>
                ) : selectedCollection ? (
                  <>
                    <span>
                      Collection: <strong>{formatCollectionName(selectedCollection.name)}</strong>
                    </span>
                    <span>
                      <strong>{filteredDocuments.length}</strong> documents hiển thị
                      {searchQuery && ` (lọc từ ${documents.length})`}
                    </span>
                  </>
                ) : (
                  <>
                    <span>
                      <strong>{filteredCollections.length}</strong> collections hiển thị
                      {searchQuery && ` (lọc từ ${collections.length})`}
                    </span>
                    <span>
                      Chọn collection để xem documents
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