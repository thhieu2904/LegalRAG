import { useState, useEffect } from 'react';
import { X, FileText, Database, File, ChevronDown, ChevronUp } from 'lucide-react';
import { format } from 'date-fns';
import { useDocumentStore } from '../../stores/useDocumentStore';
import type { DocumentDetailResponse } from '../../types/document.types';

interface DocumentDetailModalProps {
  isOpen: boolean;
  documentId: string | null;
  onClose: () => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}

const formatFileSize = (bytes: number | null): string => {
  if (!bytes) return 'N/A';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

export const DocumentDetailModal = ({
  isOpen,
  documentId,
  onClose,
  onEdit,
  onDelete,
}: DocumentDetailModalProps) => {
  const { getDocumentDetail, loading } = useDocumentStore();
  const [documentDetail, setDocumentDetail] = useState<DocumentDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedChunks, setExpandedChunks] = useState(false);

  const loadDocumentDetail = async () => {
    if (!documentId) return;

    setError(null);
    try {
      const detail = await getDocumentDetail(documentId);
      setDocumentDetail(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load document details');
    }
  };

  useEffect(() => {
    if (isOpen && documentId) {
      loadDocumentDetail();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, documentId]);

  const handleEdit = () => {
    if (documentId) {
      onEdit(documentId);
      onClose();
    }
  };

  const handleDelete = () => {
    if (documentId) {
      onDelete(documentId);
      onClose();
    }
  };

  if (!isOpen || !documentId) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Document Details</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="text-gray-600 mt-2">Loading details...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {documentDetail && !loading && (
            <div className="space-y-6">
              {/* Document Info */}
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div className="flex items-start gap-3">
                  <FileText className="w-5 h-5 text-blue-600 mt-0.5" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 text-lg">
                      {documentDetail.document.title}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1 flex items-center gap-1">
                      <File className="w-3 h-3" />
                      {documentDetail.document.filename}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-3 border-t border-gray-200">
                  <div>
                    <p className="text-xs text-gray-500">Collection</p>
                    <p className="text-sm font-medium text-gray-900 mt-1">
                      {documentDetail.collection_name}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">File Size</p>
                    <p className="text-sm font-medium text-gray-900 mt-1">
                      {formatFileSize(documentDetail.document.file_size)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Chunks</p>
                    <p className="text-sm font-medium text-gray-900 mt-1">
                      {documentDetail.document.chunk_count}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Created</p>
                    <p className="text-sm font-medium text-gray-900 mt-1">
                      {format(new Date(documentDetail.document.created_at), 'dd/MM/yyyy HH:mm')}
                    </p>
                  </div>
                </div>
              </div>

              {/* Forms Section (PRIORITY) */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Database className="w-5 h-5 text-purple-600" />
                  Extracted Forms ({documentDetail.forms.length})
                </h3>

                {documentDetail.forms.length === 0 ? (
                  <div className="bg-gray-50 rounded-lg p-6 text-center">
                    <Database className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                    <p className="text-gray-600">No forms extracted from this document</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {documentDetail.forms.map((form) => (
                      <div
                        key={form.id}
                        className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="font-medium text-gray-900">{form.form_name}</h4>
                            <p className="text-sm text-gray-600 mt-1">
                              Type: <span className="font-medium">{form.form_type}</span>
                            </p>
                          </div>
                          {form.template_path && (
                            <a
                              href={form.template_path}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="ml-4 px-3 py-1 text-sm bg-blue-50 text-blue-600 rounded hover:bg-blue-100 transition-colors"
                            >
                              Download
                            </a>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Chunks Section (Expandable) */}
              <div>
                <button
                  onClick={() => setExpandedChunks(!expandedChunks)}
                  className="w-full flex items-center justify-between text-lg font-semibold text-gray-900 mb-3 hover:text-blue-600 transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <Database className="w-5 h-5 text-green-600" />
                    Document Chunks ({documentDetail.chunks.length})
                  </span>
                  {expandedChunks ? (
                    <ChevronUp className="w-5 h-5" />
                  ) : (
                    <ChevronDown className="w-5 h-5" />
                  )}
                </button>

                {expandedChunks && (
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {documentDetail.chunks.map((chunk, index) => (
                      <div
                        key={chunk.id}
                        className="bg-white border border-gray-200 rounded-lg p-4"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <span className="text-xs font-medium text-gray-500">
                            Chunk {index + 1} (Index: {chunk.chunk_index})
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{chunk.content}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Close
          </button>
          <button
            onClick={handleEdit}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Edit Title
          </button>
          <button
            onClick={handleDelete}
            disabled={loading}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
};
