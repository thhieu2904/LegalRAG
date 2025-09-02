import { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Badge } from "../../components/ui/badge";
import {
  FolderOpen,
  FileText,
  Plus,
  Edit,
  Trash2,
  Upload,
  Search,
  File,
  FilePlus,
  Download,
  Eye,
  CheckCircle,
  Clock,
  AlertCircle,
  Settings,
  Filter,
  RefreshCw,
  Database,
  FileCheck,
  FileX,
  Loader,
  ArrowUpDown,
  ChevronDown,
} from "lucide-react";
import type {
  LegalCollection,
  LegalDocument,
  ProcessingStep,
} from "../../types/admin";
import { useModal } from "../../hooks/useModal";
import {
  CollectionModal,
  DocumentModal,
  DocumentViewModal,
  DeleteModal,
} from "../../components/admin/modals/DatabaseModals";

export default function AdminDatabase() {
  const [selectedCollection, setSelectedCollection] =
    useState<LegalCollection | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus] = useState<string>("all");
  const [filterCategory] = useState<string>("all");

  // Modal management
  const collectionModal = useModal();
  const documentModal = useModal();
  const viewModal = useModal();
  const deleteModal = useModal();

  // Enhanced mock collections data
  const [collections] = useState<LegalCollection[]>([
    {
      id: "quy_trinh_cap_ho_tich_cap_xa",
      name: "quy_trinh_cap_ho_tich_cap_xa",
      displayName: "Quy trình cấp hộ tịch cấp xã",
      documentCount: 15,
      updatedAt: "2024-03-15",
      description:
        "Các văn bản pháp luật về quy trình cấp giấy tờ hộ tịch tại cấp xã",
      status: "active",
      totalSize: 45200000, // 45.2 MB in bytes
      category: "procedure",
      createdAt: "2024-01-15",
    },
    {
      id: "thu_tuc_hanh_chinh",
      name: "thu_tuc_hanh_chinh",
      displayName: "Thủ tục hành chính",
      documentCount: 23,
      updatedAt: "2024-03-12",
      description: "Văn bản hướng dẫn các thủ tục hành chính công",
      status: "active",
      totalSize: 78600000, // 78.6 MB in bytes
      category: "procedure",
      createdAt: "2024-01-10",
    },
    {
      id: "luat_dan_su",
      name: "luat_dan_su",
      displayName: "Luật Dân sự",
      documentCount: 8,
      updatedAt: "2024-03-10",
      description: "Các điều khoản và quy định trong Bộ luật Dân sự",
      status: "active",
      totalSize: 32100000, // 32.1 MB in bytes
      category: "law",
      createdAt: "2024-01-05",
    },
  ]);

  // Enhanced mock documents for selected collection
  const [documents] = useState<LegalDocument[]>([
    {
      id: "doc_001",
      collectionId: "quy_trinh_cap_ho_tich_cap_xa",
      name: "Thông tư 01/2023/TT-BNV",
      fileName: "thong_tu_01_2023_tt_bnv",
      title: "Thông tư hướng dẫn thủ tục cấp hộ tịch",
      version: "1.0",
      status: "processed",
      documentType: "regulation",
      language: "vi",
      tags: ["thông tư", "hộ tịch", "2023"],
      documentNumber: "01/2023/TT-BNV",
      issuedBy: "Bộ Nội vụ",
      issuedDate: "2023-01-15",
      effectiveDate: "2023-02-15",
      createdAt: "2024-03-15",
      updatedAt: "2024-03-15",
      sourceFile: {
        id: "file_001_doc",
        filename: "thong_tu_01_2023_tt_bnv.docx",
        originalName: "Thông tư 01-2023-TT-BNV.docx",
        path: "/docs/thong_tu_01_2023_tt_bnv.docx",
        size: 2500000,
        mimeType:
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        uploadedAt: "2024-03-15",
        status: "processed",
      },
      processedFile: {
        id: "file_001_json",
        filename: "thong_tu_01_2023_tt_bnv.json",
        originalName: "thong_tu_01_2023_tt_bnv.json",
        path: "/docs/thong_tu_01_2023_tt_bnv.json",
        size: 500000,
        mimeType: "application/json",
        uploadedAt: "2024-03-15",
        status: "processed",
      },
      formFile: {
        id: "file_001_form",
        filename: "form_thong_tu_01.pdf",
        originalName: "Form thông tư 01.pdf",
        path: "/forms/form_thong_tu_01.pdf",
        size: 1000000,
        mimeType: "application/pdf",
        uploadedAt: "2024-03-15",
        status: "processed",
      },
      isIndexed: true,
      indexedAt: "2024-03-15",
      viewCount: 25,
      downloadCount: 8,
      processingSteps: [
        { id: "1", name: "Tải lên file", status: "completed", progress: 100 },
        {
          id: "2",
          name: "Phân tích văn bản",
          status: "completed",
          progress: 100,
        },
        { id: "3", name: "Tạo JSON", status: "completed", progress: 100 },
        { id: "4", name: "Đánh index", status: "completed", progress: 100 },
      ],
    },
    {
      id: "doc_002",
      collectionId: "quy_trinh_cap_ho_tich_cap_xa",
      name: "Quyết định 15/2023/QĐ-UBND",
      fileName: "quyet_dinh_15_2023_qd_ubnd",
      title: "Quyết định về thủ tục cấp giấy tờ",
      version: "1.2",
      status: "processed",
      documentType: "law",
      language: "vi",
      tags: ["quyết định", "UBND", "2023"],
      documentNumber: "15/2023/QĐ-UBND",
      issuedBy: "UBND Tỉnh",
      issuedDate: "2023-02-10",
      effectiveDate: "2023-03-01",
      createdAt: "2024-03-14",
      updatedAt: "2024-03-14",
      sourceFile: {
        id: "file_002_doc",
        filename: "quyet_dinh_15_2023_qd_ubnd.docx",
        originalName: "Quyết định 15-2023-QĐ-UBND.docx",
        path: "/docs/quyet_dinh_15_2023_qd_ubnd.docx",
        size: 1800000,
        mimeType:
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        uploadedAt: "2024-03-14",
        status: "processed",
      },
      processedFile: {
        id: "file_002_json",
        filename: "quyet_dinh_15_2023_qd_ubnd.json",
        originalName: "quyet_dinh_15_2023_qd_ubnd.json",
        path: "/docs/quyet_dinh_15_2023_qd_ubnd.json",
        size: 400000,
        mimeType: "application/json",
        uploadedAt: "2024-03-14",
        status: "processed",
      },
      isIndexed: true,
      indexedAt: "2024-03-14",
      viewCount: 18,
      downloadCount: 5,
    },
    {
      id: "doc_003",
      collectionId: "quy_trinh_cap_ho_tich_cap_xa",
      name: "Hướng dẫn thực hiện 2024",
      fileName: "huong_dan_thuc_hien_2024",
      title: "Hướng dẫn thực hiện thủ tục cấp hộ tịch năm 2024",
      version: "1.0",
      status: "processing",
      documentType: "guide",
      language: "vi",
      tags: ["hướng dẫn", "2024"],
      issuedBy: "Bộ Tư pháp",
      issuedDate: "2024-01-01",
      effectiveDate: "2024-02-01",
      createdAt: "2024-03-13",
      updatedAt: "2024-03-13",
      sourceFile: {
        id: "file_003_doc",
        filename: "huong_dan_thuc_hien_2024.docx",
        originalName: "Hướng dẫn thực hiện 2024.docx",
        path: "/docs/huong_dan_thuc_hien_2024.docx",
        size: 3200000,
        mimeType:
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        uploadedAt: "2024-03-13",
        status: "processing",
      },
      isIndexed: false,
      viewCount: 3,
      processingSteps: [
        { id: "1", name: "Tải lên file", status: "completed", progress: 100 },
        {
          id: "2",
          name: "Phân tích văn bản",
          status: "processing",
          progress: 65,
        },
        { id: "3", name: "Tạo JSON", status: "pending", progress: 0 },
        { id: "4", name: "Đánh index", status: "pending", progress: 0 },
      ],
    },
  ]);

  const filteredCollections = collections.filter((collection) => {
    const matchesSearch =
      collection.displayName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      collection.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory =
      filterCategory === "all" || collection.category === filterCategory;
    const matchesStatus =
      filterStatus === "all" || collection.status === filterStatus;
    return matchesSearch && matchesCategory && matchesStatus;
  });

  const filteredDocuments = documents.filter((doc) => {
    if (!selectedCollection || doc.collectionId !== selectedCollection.id)
      return false;
    const matchesSearch =
      doc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.fileName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.tags.some((tag) =>
        tag.toLowerCase().includes(searchTerm.toLowerCase())
      );
    const matchesStatus = filterStatus === "all" || doc.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "processed":
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case "processing":
        return <Loader className="w-4 h-4 text-yellow-600 animate-spin" />;
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      case "pending":
        return <Clock className="w-4 h-4 text-gray-600" />;
      default:
        return <Clock className="w-4 h-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "processed":
        return "bg-green-100 text-green-800";
      case "processing":
        return "bg-yellow-100 text-yellow-800";
      case "error":
        return "bg-red-100 text-red-800";
      case "pending":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "procedure":
        return "bg-blue-100 text-blue-800";
      case "law":
        return "bg-purple-100 text-purple-800";
      case "regulation":
        return "bg-orange-100 text-orange-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const renderProcessingSteps = (steps?: ProcessingStep[]) => {
    if (!steps) return null;

    return (
      <div className="space-y-2 mt-3">
        <h5 className="text-sm font-medium text-gray-700">Tiến trình xử lý:</h5>
        {steps.map((step) => (
          <div key={step.id} className="flex items-center space-x-3">
            {getStatusIcon(step.status)}
            <span className="text-sm text-gray-600 flex-1">{step.name}</span>
            <span className="text-xs text-gray-500">{step.progress}%</span>
          </div>
        ))}
      </div>
    );
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString("vi-VN");
  };

  const handleUploadDocument = () => {
    if (!selectedCollection) {
      alert("Vui lòng chọn collection trước khi tải lên văn bản mới");
      return;
    }
    documentModal.openModal("add-document");
  };

  const handleAddCollection = () => {
    collectionModal.openModal("add-collection");
  };

  const handleViewDocument = (document: LegalDocument) => {
    viewModal.openModal("view-document", document);
  };

  const handleDeleteDocument = (document: LegalDocument) => {
    deleteModal.openModal("delete-document", document);
  };

  return (
    <div className="admin-page-container admin-database-page">
      {/* Enhanced Header */}
      <div className="admin-page-header-section">
        <div className="admin-page-header-content">
          <div className="flex items-center gap-3">
            <Database className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="admin-page-title-main">Cơ sở dữ liệu pháp luật</h1>
              <p className="admin-page-subtitle-main">
                Quản lý collections và documents trong hệ thống RAG
              </p>
            </div>
          </div>

          {/* Statistics */}
          <div className="flex gap-4 mt-4">
            <div className="bg-blue-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {collections.length}
              </div>
              <div className="text-sm text-blue-600">Collections</div>
            </div>
            <div className="bg-green-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {collections.reduce((acc, col) => acc + col.documentCount, 0)}
              </div>
              <div className="text-sm text-green-600">Documents</div>
            </div>
            <div className="bg-purple-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {formatFileSize(
                  collections.reduce((acc, col) => acc + col.totalSize, 0)
                )}
              </div>
              <div className="text-sm text-purple-600">Total Size</div>
            </div>
          </div>
        </div>

        <div className="admin-page-actions-main">
          {selectedCollection && (
            <Button
              onClick={handleUploadDocument}
              className="shared-button shared-button-primary"
            >
              <Upload className="w-4 h-4" />
              Tải lên văn bản
            </Button>
          )}
          <Button
            onClick={handleAddCollection}
            variant="outline"
            className="flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Thêm Collection
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <RefreshCw className="w-4 h-4" />
            Đồng bộ
          </Button>
        </div>
      </div>

      {/* Enhanced Filters */}
      <div className="flex flex-col lg:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder={
              selectedCollection
                ? "Tìm kiếm văn bản, tags..."
                : "Tìm kiếm collection..."
            }
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="flex items-center gap-2"
          >
            <Filter className="w-4 h-4" />
            Trạng thái
            <ChevronDown className="w-4 h-4" />
          </Button>

          <Button
            variant="outline"
            size="sm"
            className="flex items-center gap-2"
          >
            <ArrowUpDown className="w-4 h-4" />
            Sắp xếp
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Enhanced Collections Panel */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FolderOpen className="w-5 h-5" />
                  Collections ({filteredCollections.length})
                </div>
                <Button variant="ghost" size="sm">
                  <Settings className="w-4 h-4" />
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 max-h-96 overflow-y-auto">
              {filteredCollections.map((collection) => (
                <div
                  key={collection.id}
                  className={`p-4 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
                    selectedCollection?.id === collection.id
                      ? "bg-blue-50 border-blue-200 shadow-sm"
                      : "bg-white border-gray-200 hover:bg-gray-50"
                  }`}
                  onClick={() => setSelectedCollection(collection)}
                >
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="font-medium text-gray-900 text-sm">
                      {collection.displayName}
                    </h3>
                    <div className="flex gap-1">
                      <Badge
                        variant="outline"
                        className={getCategoryColor(collection.category)}
                      >
                        {collection.category}
                      </Badge>
                    </div>
                  </div>

                  <p className="text-xs text-gray-600 mb-3 line-clamp-2">
                    {collection.description}
                  </p>

                  <div className="flex justify-between items-center text-xs text-gray-500">
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1">
                        <FileText className="w-3 h-3" />
                        {collection.documentCount}
                      </span>
                      <span>{formatFileSize(collection.totalSize)}</span>
                    </div>
                    <Badge className={getStatusColor(collection.status)}>
                      {collection.status}
                    </Badge>
                  </div>

                  <div className="text-xs text-gray-400 mt-2">
                    Cập nhật: {formatDate(collection.updatedAt)}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Enhanced Documents Panel */}
        <div className="lg:col-span-2">
          {selectedCollection ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5" />
                    Văn bản trong "{selectedCollection.displayName}" (
                    {filteredDocuments.length})
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Download className="w-4 h-4" />
                      Export
                    </Button>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {filteredDocuments.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      Không có văn bản nào
                    </h3>
                    <p className="text-gray-600 mb-4">
                      Chưa có văn bản nào trong collection này. Hãy tải lên văn
                      bản đầu tiên.
                    </p>
                    <Button
                      onClick={handleUploadDocument}
                      className="flex items-center gap-2"
                    >
                      <Upload className="w-4 h-4" />
                      Tải lên văn bản đầu tiên
                    </Button>
                  </div>
                ) : (
                  filteredDocuments.map((doc) => (
                    <div
                      key={doc.id}
                      className="p-4 border rounded-lg bg-white hover:shadow-md transition-all"
                    >
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <div className="flex items-start gap-3 mb-2">
                            {getStatusIcon(doc.status)}
                            <div className="flex-1">
                              <h4 className="font-medium text-gray-900 mb-1">
                                {doc.name}
                              </h4>
                              <p className="text-sm text-gray-600 mb-2">
                                {doc.fileName} • v{doc.version}
                              </p>
                            </div>
                            <Badge className={getStatusColor(doc.status)}>
                              {doc.status}
                            </Badge>
                          </div>

                          {/* Tags */}
                          <div className="flex gap-1 mb-3">
                            {doc.tags.map((tag, index) => (
                              <Badge
                                key={index}
                                variant="outline"
                                className="text-xs"
                              >
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* File Types with better layout */}
                      <div className="grid grid-cols-3 gap-4 mb-4 p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-2 text-sm">
                          <File className="w-4 h-4 text-blue-600" />
                          <div>
                            <div className="font-medium">DOC/DOCX</div>
                            <div className="text-xs text-gray-500">
                              {formatFileSize(doc.sourceFile.size)}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <FileCheck className="w-4 h-4 text-green-600" />
                          <div>
                            <div className="font-medium">JSON</div>
                            <div className="text-xs text-gray-500">
                              Đã xử lý
                            </div>
                          </div>
                        </div>
                        {doc.formFile ? (
                          <div className="flex items-center gap-2 text-sm">
                            <FilePlus className="w-4 h-4 text-purple-600" />
                            <div>
                              <div className="font-medium">FORM</div>
                              <div className="text-xs text-gray-500">
                                Có sẵn
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2 text-sm text-gray-400">
                            <FileX className="w-4 h-4" />
                            <div>
                              <div>Không có form</div>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Processing Steps for processing documents */}
                      {doc.status === "processing" &&
                        renderProcessingSteps(doc.processingSteps)}

                      {/* Enhanced Actions */}
                      <div className="flex justify-between items-center pt-3 border-t">
                        <div className="text-xs text-gray-500">
                          Tải lên: {formatDate(doc.createdAt)} • Sửa đổi:{" "}
                          {formatDate(doc.updatedAt)}
                        </div>

                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleViewDocument(doc)}
                          >
                            <Eye className="w-3 h-3 mr-1" />
                            Xem
                          </Button>
                          <Button size="sm" variant="outline">
                            <Edit className="w-3 h-3 mr-1" />
                            Sửa
                          </Button>
                          <Button size="sm" variant="outline">
                            <Download className="w-3 h-3 mr-1" />
                            Tải
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-red-600"
                            onClick={() => handleDeleteDocument(doc)}
                          >
                            <Trash2 className="w-3 h-3 mr-1" />
                            Xóa
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="text-center py-16">
                <FolderOpen className="w-20 h-20 mx-auto mb-6 text-gray-300" />
                <h3 className="text-xl font-medium text-gray-900 mb-3">
                  Chọn một Collection
                </h3>
                <p className="text-gray-600 mb-6 max-w-md mx-auto">
                  Chọn một collection từ danh sách bên trái để xem và quản lý
                  các văn bản pháp luật.
                </p>
                <div className="space-y-2 text-sm text-gray-500">
                  <p>• Xem chi tiết văn bản và trạng thái xử lý</p>
                  <p>• Tải lên văn bản mới với form đi kèm</p>
                  <p>• Quản lý version và metadata</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Modal Components */}
      <CollectionModal
        isOpen={collectionModal.isOpen}
        onClose={collectionModal.closeModal}
        mode="add"
        onConfirm={(data) => {
          console.log("Collection data:", data);
          collectionModal.closeModal();
        }}
      />

      <DocumentModal
        isOpen={documentModal.isOpen}
        onClose={documentModal.closeModal}
        mode="add"
        collectionId={selectedCollection?.id}
        onConfirm={(data) => {
          console.log("Document data:", data);
          documentModal.closeModal();
        }}
      />

      <DocumentViewModal
        isOpen={viewModal.isOpen}
        onClose={viewModal.closeModal}
        data={viewModal.modalState.data as LegalDocument | undefined}
      />

      <DeleteModal
        isOpen={deleteModal.isOpen}
        onClose={deleteModal.closeModal}
        onConfirm={() => {
          console.log("Delete confirmed");
          deleteModal.closeModal();
        }}
        itemName={
          (deleteModal.modalState.data as LegalDocument)?.name || "Văn bản"
        }
        itemType="document"
      />
    </div>
  );
}
