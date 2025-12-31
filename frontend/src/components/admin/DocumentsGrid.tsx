import { FileText } from 'lucide-react';
import { DocumentCard } from '../admin/DocumentCard';
import type { Document } from '../../types/document.types';

interface DocumentsGridProps {
  documents: Document[];
  loading: boolean;
  onClick?: (id: string) => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onCreate: () => void;
  onDownload?: (filePath: string, filename: string) => void;
}

export const DocumentsGrid = ({
  documents,
  loading,
  onClick,
  onEdit,
  onDelete,
  onCreate,
  onDownload,
}: DocumentsGridProps) => {
  // Loading State
  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="text-gray-600 mt-2">Đang tải tài liệu...</p>
      </div>
    );
  }

  // Empty State
  if (documents.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Chưa có tài liệu nào</h3>
        <p className="text-gray-600 mb-4">Bắt đầu bằng cách thêm tài liệu đầu tiên của bạn</p>
        <button
          onClick={onCreate}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <FileText className="w-5 h-5" />
          Thêm tài liệu đầu tiên
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Documents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {documents.map((doc) => (
          <DocumentCard
            key={doc.id}
            document={doc}
            onClick={onClick}
            onEdit={onEdit}
            onDelete={onDelete}
            onDownload={onDownload}
          />
        ))}
      </div>

      {/* Results Count */}
      <div className="text-sm text-gray-600 text-center">Tổng số {documents.length} tài liệu</div>
    </div>
  );
};
