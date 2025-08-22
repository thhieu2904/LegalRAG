import React, { useState, useEffect } from "react";
import {
  ChevronRight,
  ChevronDown,
  Plus,
  Edit,
  Trash2,
  Search,
  Loader,
  FileText,
  Folder,
  MessageCircle,
} from "lucide-react";

import { Card } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Alert } from "../../components/ui/alert";
import { questionsService } from "../../services/questionsService";
import type {
  Collection,
  Document,
  Question,
} from "../../services/questionsService";

interface CollectionState {
  expanded: boolean;
  documents: Document[];
  loading: boolean;
}

interface DocumentState {
  expanded: boolean;
  questions: Question[];
  loading: boolean;
}

const AdminQuestionsHierarchical: React.FC = () => {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [collectionStates, setCollectionStates] = useState<
    Record<string, CollectionState>
  >({});
  const [documentStates, setDocumentStates] = useState<
    Record<string, DocumentState>
  >({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    loadCollections();
  }, []);

  const loadCollections = async () => {
    try {
      setLoading(true);
      const collectionsData = await questionsService.getCollections();
      setCollections(collectionsData);
      setError(null);
    } catch (err) {
      setError("Không thể tải danh sách collections");
      console.error("Error loading collections:", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleCollection = async (collectionName: string) => {
    const currentState = collectionStates[collectionName];

    if (!currentState?.expanded) {
      // Expanding - load documents
      setCollectionStates((prev) => ({
        ...prev,
        [collectionName]: {
          ...prev[collectionName],
          loading: true,
          expanded: true,
        },
      }));

      try {
        const documents = await questionsService.getCollectionDocuments(
          collectionName
        );
        setCollectionStates((prev) => ({
          ...prev,
          [collectionName]: {
            expanded: true,
            documents,
            loading: false,
          },
        }));
      } catch (err) {
        console.error("Error loading documents:", err);
        setCollectionStates((prev) => ({
          ...prev,
          [collectionName]: {
            expanded: false,
            documents: [],
            loading: false,
          },
        }));
      }
    } else {
      // Collapsing
      setCollectionStates((prev) => ({
        ...prev,
        [collectionName]: {
          ...prev[collectionName],
          expanded: false,
        },
      }));
    }
  };

  const toggleDocument = async (collectionName: string, documentId: string) => {
    const documentKey = `${collectionName}_${documentId}`;
    const currentState = documentStates[documentKey];

    if (!currentState?.expanded) {
      // Expanding - load questions
      setDocumentStates((prev) => ({
        ...prev,
        [documentKey]: {
          ...prev[documentKey],
          loading: true,
          expanded: true,
        },
      }));

      try {
        const questions = await questionsService.getDocumentQuestions(
          collectionName,
          documentId
        );
        setDocumentStates((prev) => ({
          ...prev,
          [documentKey]: {
            expanded: true,
            questions,
            loading: false,
          },
        }));
      } catch (err) {
        console.error("Error loading questions:", err);
        setDocumentStates((prev) => ({
          ...prev,
          [documentKey]: {
            expanded: false,
            questions: [],
            loading: false,
          },
        }));
      }
    } else {
      // Collapsing
      setDocumentStates((prev) => ({
        ...prev,
        [documentKey]: {
          ...prev[documentKey],
          expanded: false,
        },
      }));
    }
  };

  const handleDeleteQuestion = async (
    questionId: string,
    collectionName: string
  ) => {
    if (!window.confirm("Bạn có chắc chắn muốn xóa câu hỏi này?")) return;

    try {
      await questionsService.deleteQuestion(collectionName, questionId);
      // Refresh document questions
      // Find which document this question belongs to and refresh it
      // For now, we'll refresh all expanded documents in the collection
      const updatedDocumentStates = { ...documentStates };
      Object.keys(updatedDocumentStates).forEach((key) => {
        if (
          key.startsWith(`${collectionName}_`) &&
          updatedDocumentStates[key].expanded
        ) {
          const documentId = key.split("_")[1];
          toggleDocument(collectionName, documentId);
        }
      });
    } catch (err) {
      setError("Không thể xóa câu hỏi");
      console.error("Error deleting question:", err);
    }
  };

  const filteredCollections = collections.filter(
    (collection) =>
      collection.display_name
        .toLowerCase()
        .includes(searchTerm.toLowerCase()) ||
      collection.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="admin-page-container">
        <div className="flex items-center justify-center py-12">
          <Loader className="w-8 h-8 animate-spin mr-3" />
          <span className="text-lg">Đang tải dữ liệu...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-page-container admin-questions-page">
      <div className="admin-page-header-section">
        <div className="admin-page-title-row">
          <h1 className="admin-page-title">
            <MessageCircle className="admin-page-title-icon" />
            Quản lý Câu hỏi Router (Hierarchical)
          </h1>
        </div>

        <div className="admin-search-section">
          <div className="admin-search-box">
            <Search className="admin-search-icon" />
            <Input
              placeholder="Tìm kiếm collections..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="admin-search-input"
            />
          </div>
        </div>

        {error && (
          <Alert className="mb-6 bg-red-50 border-red-200 text-red-800">
            {error}
          </Alert>
        )}

        <div className="admin-stats-grid">
          <Card className="admin-stat-card">
            <Folder className="admin-stat-icon text-blue-500" />
            <div className="admin-stat-content">
              <div className="admin-stat-number">{collections.length}</div>
              <div className="admin-stat-label">Collections</div>
            </div>
          </Card>

          <Card className="admin-stat-card">
            <FileText className="admin-stat-icon text-green-500" />
            <div className="admin-stat-content">
              <div className="admin-stat-number">
                {Object.values(collectionStates).reduce(
                  (acc, state) => acc + (state.documents?.length || 0),
                  0
                )}
              </div>
              <div className="admin-stat-label">Documents</div>
            </div>
          </Card>

          <Card className="admin-stat-card">
            <MessageCircle className="admin-stat-icon text-purple-500" />
            <div className="admin-stat-content">
              <div className="admin-stat-number">
                {collections.reduce((acc, col) => acc + col.total_questions, 0)}
              </div>
              <div className="admin-stat-label">Total Questions</div>
            </div>
          </Card>
        </div>
      </div>

      <div className="admin-page-content-section">
        <div className="space-y-4">
          {filteredCollections.map((collection) => {
            const collectionState = collectionStates[collection.name];
            const isExpanded = collectionState?.expanded || false;
            const isLoading = collectionState?.loading || false;
            const documents = collectionState?.documents || [];

            return (
              <Card key={collection.name} className="p-0 overflow-hidden">
                {/* Collection Header */}
                <div
                  className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 border-b"
                  onClick={() => toggleCollection(collection.name)}
                >
                  <div className="flex items-center space-x-3">
                    {isExpanded ? (
                      <ChevronDown className="w-5 h-5 text-gray-500" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-500" />
                    )}
                    <Folder className="w-5 h-5 text-blue-500" />
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        {collection.display_name}
                      </h3>
                      <p className="text-sm text-gray-500">{collection.name}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-500">
                      {collection.total_questions} questions
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        // Handle add new document or question
                      }}
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* Documents List */}
                {isExpanded && (
                  <div className="border-l-2 border-blue-200 ml-8">
                    {isLoading ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader className="w-5 h-5 animate-spin mr-2" />
                        <span className="text-sm text-gray-500">
                          Đang tải documents...
                        </span>
                      </div>
                    ) : (
                      documents.map((document) => {
                        const documentKey = `${collection.name}_${document.id}`;
                        const documentState = documentStates[documentKey];
                        const isDocExpanded = documentState?.expanded || false;
                        const isDocLoading = documentState?.loading || false;
                        const questions = documentState?.questions || [];

                        return (
                          <div
                            key={document.id}
                            className="border-b border-gray-100 last:border-b-0"
                          >
                            {/* Document Header */}
                            <div
                              className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
                              onClick={() =>
                                toggleDocument(collection.name, document.id)
                              }
                            >
                              <div className="flex items-center space-x-3">
                                {isDocExpanded ? (
                                  <ChevronDown className="w-4 h-4 text-gray-500" />
                                ) : (
                                  <ChevronRight className="w-4 h-4 text-gray-500" />
                                )}
                                <FileText className="w-4 h-4 text-green-500" />
                                <div>
                                  <h4 className="font-medium text-gray-800">
                                    {document.title}
                                  </h4>
                                  <p className="text-xs text-gray-500">
                                    {document.id}
                                  </p>
                                </div>
                              </div>
                              <div className="flex items-center space-x-3">
                                <span className="text-xs text-gray-500">
                                  {document.question_count} questions
                                </span>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    // Handle add new question to document
                                  }}
                                >
                                  <Plus className="w-3 h-3" />
                                </Button>
                              </div>
                            </div>

                            {/* Questions List */}
                            {isDocExpanded && (
                              <div className="border-l-2 border-green-200 ml-8 bg-gray-50">
                                {isDocLoading ? (
                                  <div className="flex items-center justify-center py-6">
                                    <Loader className="w-4 h-4 animate-spin mr-2" />
                                    <span className="text-xs text-gray-500">
                                      Đang tải questions...
                                    </span>
                                  </div>
                                ) : questions.length > 0 ? (
                                  <div className="space-y-2 p-4">
                                    {questions.map((question) => (
                                      <div
                                        key={question.id}
                                        className="flex items-start justify-between p-3 bg-white rounded border hover:border-gray-300 transition-colors"
                                      >
                                        <div className="flex-1">
                                          <div className="flex items-center space-x-2 mb-1">
                                            <MessageCircle className="w-3 h-3 text-purple-500" />
                                            <span
                                              className={`text-xs px-2 py-1 rounded ${
                                                question.type === "main"
                                                  ? "bg-blue-100 text-blue-800"
                                                  : "bg-gray-100 text-gray-800"
                                              }`}
                                            >
                                              {question.type}
                                            </span>
                                            <span className="text-xs text-gray-500">
                                              Score: {question.priority_score}
                                            </span>
                                          </div>
                                          <p className="text-sm text-gray-800 leading-relaxed">
                                            {question.text}
                                          </p>
                                          {question.keywords &&
                                            question.keywords.length > 0 && (
                                              <div className="flex flex-wrap gap-1 mt-2">
                                                {question.keywords.map(
                                                  (keyword, idx) => (
                                                    <span
                                                      key={idx}
                                                      className="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded"
                                                    >
                                                      {keyword}
                                                    </span>
                                                  )
                                                )}
                                              </div>
                                            )}
                                        </div>
                                        <div className="flex items-center space-x-1 ml-3">
                                          <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => {
                                              // Handle edit question
                                            }}
                                          >
                                            <Edit className="w-3 h-3" />
                                          </Button>
                                          <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() =>
                                              handleDeleteQuestion(
                                                question.id,
                                                collection.name
                                              )
                                            }
                                          >
                                            <Trash2 className="w-3 h-3" />
                                          </Button>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <div className="text-center py-6 text-gray-500 text-sm">
                                    Chưa có câu hỏi nào
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                )}
              </Card>
            );
          })}

          {filteredCollections.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              {searchTerm
                ? "Không tìm thấy collection nào"
                : "Chưa có collection nào"}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminQuestionsHierarchical;
