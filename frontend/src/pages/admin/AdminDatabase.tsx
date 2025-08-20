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
import {
  FolderOpen,
  FileText,
  Plus,
  Edit,
  Trash2,
  Upload,
  Search,
  Info,
  Save,
  X,
  File,
  FilePlus,
} from "lucide-react";

interface LegalCollection {
  id: string;
  name: string;
  displayName: string;
  documentCount: number;
  lastUpdated: string;
  description: string;
}

interface LegalDocument {
  id: string;
  name: string;
  fileName: string;
  docFile: string; // Path to .doc/.docx file
  jsonFile: string; // Path to .json file
  formFile?: string; // Optional form file
  collection: string;
  uploadDate: string;
  fileSize: string;
  status: "processed" | "processing" | "error";
}

export default function AdminDatabase() {
  const [selectedCollection, setSelectedCollection] =
    useState<LegalCollection | null>(null);
  const [showAddDocument, setShowAddDocument] = useState(false);
  const [showAddCollection, setShowAddCollection] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  // Mock collections data
  const [collections] = useState<LegalCollection[]>([
    {
      id: "quy_trinh_cap_ho_tich_cap_xa",
      name: "quy_trinh_cap_ho_tich_cap_xa",
      displayName: "Quy trình cấp hộ tịch cấp xã",
      documentCount: 15,
      lastUpdated: "2024-03-15",
      description:
        "Các văn bản pháp luật về quy trình cấp giấy tờ hộ tịch tại cấp xã",
    },
    {
      id: "thủ_tục_hành_chính",
      name: "thủ_tục_hành_chính",
      displayName: "Thủ tục hành chính",
      documentCount: 23,
      lastUpdated: "2024-03-12",
      description: "Văn bản hướng dẫn các thủ tục hành chính công",
    },
    {
      id: "luat_dan_su",
      name: "luat_dan_su",
      displayName: "Luật Dân sự",
      documentCount: 8,
      lastUpdated: "2024-03-10",
      description: "Các điều khoản và quy định trong Bộ luật Dân sự",
    },
  ]);

  // Mock documents for selected collection
  const [documents] = useState<LegalDocument[]>([
    {
      id: "doc_001",
      name: "Thông tư 01/2023/TT-BNV",
      fileName: "thong_tu_01_2023_tt_bnv",
      docFile: "/docs/thong_tu_01_2023_tt_bnv.docx",
      jsonFile: "/docs/thong_tu_01_2023_tt_bnv.json",
      formFile: "/forms/form_thong_tu_01.pdf",
      collection: "quy_trinh_cap_ho_tich_cap_xa",
      uploadDate: "2024-03-15",
      fileSize: "2.5 MB",
      status: "processed",
    },
    {
      id: "doc_002",
      name: "Quyết định 15/2023/QĐ-UBND",
      fileName: "quyet_dinh_15_2023_qd_ubnd",
      docFile: "/docs/quyet_dinh_15_2023_qd_ubnd.docx",
      jsonFile: "/docs/quyet_dinh_15_2023_qd_ubnd.json",
      collection: "quy_trinh_cap_ho_tich_cap_xa",
      uploadDate: "2024-03-14",
      fileSize: "1.8 MB",
      status: "processed",
    },
    {
      id: "doc_003",
      name: "Hướng dẫn thực hiện 2024",
      fileName: "huong_dan_thuc_hien_2024",
      docFile: "/docs/huong_dan_thuc_hien_2024.docx",
      jsonFile: "/docs/huong_dan_thuc_hien_2024.json",
      collection: "quy_trinh_cap_ho_tich_cap_xa",
      uploadDate: "2024-03-13",
      fileSize: "3.2 MB",
      status: "processing",
    },
  ]);

  const filteredCollections = collections.filter(
    (collection) =>
      collection.displayName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      collection.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredDocuments = documents.filter(
    (doc) =>
      doc.collection === selectedCollection?.id &&
      (doc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.fileName.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleUploadDocument = () => {
    if (!selectedCollection) {
      alert("Vui lòng chọn collection trước khi tải lên văn bản mới");
      return;
    }
    setShowAddDocument(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "processed":
        return "text-green-600 bg-green-100";
      case "processing":
        return "text-yellow-600 bg-yellow-100";
      case "error":
        return "text-red-600 bg-red-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "processed":
        return "Đã xử lý";
      case "processing":
        return "Đang xử lý";
      case "error":
        return "Lỗi";
      default:
        return "Không xác định";
    }
  };

  return (
    <div className="admin-page-container admin-database-page">
      <div className="admin-page-header-section">
        <div className="admin-page-header-content">
          <h1 className="admin-page-title-main">Cơ sở dữ liệu pháp luật</h1>
          <p className="admin-page-subtitle-main">
            Quản lý collections và documents trong hệ thống
          </p>
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
            onClick={() => setShowAddCollection(true)}
            variant="outline"
            className="flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Thêm Collection
          </Button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
        <Input
          placeholder={
            selectedCollection
              ? "Tìm kiếm văn bản..."
              : "Tìm kiếm collection..."
          }
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Collections Panel */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FolderOpen className="w-5 h-5" />
                Collections ({collections.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 max-h-96 overflow-y-auto">
              {filteredCollections.map((collection) => (
                <div
                  key={collection.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedCollection?.id === collection.id
                      ? "bg-blue-50 border-blue-200"
                      : "bg-white border-gray-200 hover:bg-gray-50"
                  }`}
                  onClick={() => setSelectedCollection(collection)}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-medium text-gray-900">
                      {collection.displayName}
                    </h3>
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      {collection.documentCount} docs
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">
                    {collection.description}
                  </p>
                  <p className="text-xs text-gray-400">
                    Cập nhật: {collection.lastUpdated}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Documents Panel */}
        <div className="lg:col-span-2">
          {selectedCollection ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Văn bản trong "{selectedCollection.displayName}" (
                  {filteredDocuments.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {filteredDocuments.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p>Không có văn bản nào trong collection này</p>
                    <Button
                      onClick={handleUploadDocument}
                      className="mt-4 flex items-center gap-2 mx-auto"
                    >
                      <Upload className="w-4 h-4" />
                      Tải lên văn bản đầu tiên
                    </Button>
                  </div>
                ) : (
                  filteredDocuments.map((doc) => (
                    <div
                      key={doc.id}
                      className="p-4 border rounded-lg bg-white hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900 mb-1">
                            {doc.name}
                          </h4>
                          <p className="text-sm text-gray-600 mb-2">
                            Tên file: {doc.fileName}
                          </p>
                          <div className="flex items-center gap-4 text-xs text-gray-500">
                            <span>Tải lên: {doc.uploadDate}</span>
                            <span>Kích thước: {doc.fileSize}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                              doc.status
                            )}`}
                          >
                            {getStatusText(doc.status)}
                          </span>
                        </div>
                      </div>

                      {/* File Types */}
                      <div className="flex items-center gap-4 mb-3">
                        <div className="flex items-center gap-1 text-xs text-blue-600">
                          <File className="w-3 h-3" />
                          DOC/DOCX
                        </div>
                        <div className="flex items-center gap-1 text-xs text-green-600">
                          <FileText className="w-3 h-3" />
                          JSON
                        </div>
                        {doc.formFile && (
                          <div className="flex items-center gap-1 text-xs text-purple-600">
                            <FilePlus className="w-3 h-3" />
                            FORM
                          </div>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline">
                          <Edit className="w-3 h-3 mr-1" />
                          Chỉnh sửa
                        </Button>
                        <Button size="sm" variant="outline">
                          <FileText className="w-3 h-3 mr-1" />
                          Xem nội dung
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-red-600"
                        >
                          <Trash2 className="w-3 h-3 mr-1" />
                          Xóa
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="text-center py-12">
                <FolderOpen className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Chọn một Collection
                </h3>
                <p className="text-gray-600 mb-4">
                  Chọn một collection từ danh sách bên trái để xem và quản lý
                  các văn bản
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Add Collection Modal */}
      {showAddCollection && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Thêm Collection Mới
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAddCollection(false)}
                >
                  <X className="w-4 h-4" />
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="collection-name">Tên Collection</Label>
                <Input id="collection-name" placeholder="VD: luat_dan_su" />
              </div>
              <div>
                <Label htmlFor="collection-display-name">Tên hiển thị</Label>
                <Input
                  id="collection-display-name"
                  placeholder="VD: Luật Dân sự"
                />
              </div>
              <div>
                <Label htmlFor="collection-description">Mô tả</Label>
                <Input
                  id="collection-description"
                  placeholder="Mô tả ngắn về collection"
                />
              </div>
              <div className="flex gap-2 pt-4">
                <Button className="flex-1">
                  <Save className="w-4 h-4 mr-2" />
                  Tạo Collection
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowAddCollection(false)}
                >
                  Hủy
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Add Document Modal */}
      {showAddDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Tải lên văn bản mới
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAddDocument(false)}
                >
                  <X className="w-4 h-4" />
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <Info className="w-4 h-4" />
                <AlertDescription>
                  Collection được chọn:{" "}
                  <strong>{selectedCollection?.displayName}</strong>
                </AlertDescription>
              </Alert>

              <div>
                <Label htmlFor="document-name">Tên văn bản</Label>
                <Input
                  id="document-name"
                  placeholder="VD: Thông tư 01/2023/TT-BNV"
                />
              </div>

              <div>
                <Label htmlFor="doc-file">File DOC/DOCX</Label>
                <Input id="doc-file" type="file" accept=".doc,.docx" />
              </div>

              <div>
                <Label htmlFor="json-file">File JSON (tùy chọn)</Label>
                <Input id="json-file" type="file" accept=".json" />
              </div>

              <div>
                <Label htmlFor="form-file">File Form (tùy chọn)</Label>
                <Input id="form-file" type="file" accept=".pdf,.doc,.docx" />
              </div>

              <div className="flex gap-2 pt-4">
                <Button className="flex-1">
                  <Upload className="w-4 h-4 mr-2" />
                  Tải lên & Xử lý
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowAddDocument(false)}
                >
                  Hủy
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
