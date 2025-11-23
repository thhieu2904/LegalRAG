import { useState } from 'react';
import { X, AlertTriangle, AlertCircle } from 'lucide-react';
import { useDocumentStore } from '../../stores/useDocumentStore';

interface DeleteDocumentDialogProps {
  isOpen: boolean;
  documentId: string | null;
  documentTitle: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const DeleteDocumentDialog = ({
  isOpen,
  documentId,
  documentTitle,
  onClose,
  onSuccess,
}: DeleteDocumentDialogProps) => {
  const { deleteDocument, loading } = useDocumentStore();
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    if (!documentId) {
      setError('Document ID is missing');
      return;
    }

    setError(null);
    try {
      await deleteDocument(documentId);
      onClose();
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document');
    }
  };

  const handleClose = () => {
    if (!loading) {
      setError(null);
      onClose();
    }
  };

  if (!isOpen || !documentId) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900">Delete Document</h2>
          </div>
          <button
            onClick={handleClose}
            disabled={loading}
            className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800">Error</p>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          )}

          {/* Warning Message */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm text-gray-700">
              Are you sure you want to permanently delete this document?
            </p>
            <p className="text-sm font-semibold text-gray-900 mt-2 wrap-break-word">
              "{documentTitle}"
            </p>
          </div>

          {/* Consequences */}
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm font-medium text-red-800 mb-2">This action will:</p>
            <ul className="text-sm text-red-700 space-y-1 list-disc list-inside">
              <li>Permanently delete the document</li>
              <li>Remove all associated chunks</li>
              <li>Remove all extracted forms</li>
              <li>Cannot be undone</li>
            </ul>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              onClick={handleDelete}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Deleting...
                </>
              ) : (
                'Delete Permanently'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
