import { useState, useEffect, useCallback } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Badge } from "../../components/ui/badge";
import { questionsService } from "../../services/questionsService";
import { useModal } from "../../hooks/useModal";
import { QuestionModals } from "../../components/admin/modals/QuestionModals";

export default function AdminQuestionsRedesigned() {
  const [collections, setCollections] = useState<any[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [questions, setQuestions] = useState<any[]>([]);

  const [selectedCollection, setSelectedCollection] = useState<string>("");
  const [selectedDocument, setSelectedDocument] = useState<string>("");

  const [loading, setLoading] = useState({
    collections: false,
    documents: false,
    questions: false,
  });

  const [searchQuestions, setSearchQuestions] = useState("");

  const questionModal = useModal();
  const viewModal = useModal();
  const deleteModal = useModal();

  const loadCollections = useCallback(async () => {
    setLoading((prev) => ({ ...prev, collections: true }));
    try {
      const response = await questionsService.getCollections();
      setCollections(response);
    } catch (error) {
      console.error("Error loading collections:", error);
    } finally {
      setLoading((prev) => ({ ...prev, collections: false }));
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    if (!selectedCollection) return;
    setLoading((prev) => ({ ...prev, documents: true }));
    try {
      const response = await questionsService.getCollectionDocuments(
        selectedCollection
      );
      setDocuments(response);
    } catch (error) {
      console.error("Error loading documents:", error);
      setDocuments([]);
    } finally {
      setLoading((prev) => ({ ...prev, documents: false }));
    }
  }, [selectedCollection]);

  const loadQuestions = useCallback(async () => {
    if (!selectedCollection || !selectedDocument) return;
    setLoading((prev) => ({ ...prev, questions: true }));
    try {
      console.log(
        "Loading questions for:",
        selectedCollection,
        selectedDocument
      );
      const response = await questionsService.getDocumentQuestions(
        selectedCollection,
        selectedDocument
      );
      console.log("Questions loaded:", response.length, response);
      setQuestions(response);
    } catch (error) {
      console.error("Error loading questions:", error);
      setQuestions([]);
    } finally {
      setLoading((prev) => ({ ...prev, questions: false }));
    }
  }, [selectedCollection, selectedDocument]);

  useEffect(() => {
    loadCollections();
  }, [loadCollections]);

  useEffect(() => {
    if (selectedCollection) {
      loadDocuments();
    } else {
      setDocuments([]);
      setSelectedDocument("");
      setQuestions([]);
    }
  }, [selectedCollection, loadDocuments]);

  useEffect(() => {
    if (selectedDocument) {
      loadQuestions();
    } else {
      setQuestions([]);
    }
  }, [selectedDocument, loadQuestions]);

  const handleAddQuestion = () => {
    questionModal.openModal("add-question", {
      collection: selectedCollection,
      document: selectedDocument,
    });
  };

  const handleEditQuestion = (question: any) => {
    questionModal.openModal("edit-question", {
      question,
      collection: selectedCollection,
      document: selectedDocument,
    });
  };

  const handleViewQuestion = (question: any) => {
    viewModal.openModal("view-question", question);
  };

  const handleDeleteQuestion = (question: any) => {
    deleteModal.openModal("delete-question", question);
  };

  const handleQuestionSaved = () => {
    loadQuestions();
  };

  const handleQuestionDeleted = () => {
    loadQuestions();
  };

  const filteredQuestions = questions.filter(
    (question: any) =>
      question.text?.toLowerCase().includes(searchQuestions.toLowerCase()) ||
      question.keywords?.some((keyword: any) =>
        keyword.toLowerCase().includes(searchQuestions.toLowerCase())
      )
  );

  console.log("Debug info:", {
    selectedCollection,
    selectedDocument,
    questionsLength: questions.length,
    filteredLength: filteredQuestions.length,
    searchQuestions,
    sampleQuestion: questions[0],
  });

  return (
    <div className="flex h-full gap-4">
      <Card className="w-1/3">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Bộ sưu tập
            <Button
              onClick={loadCollections}
              disabled={loading.collections}
              size="sm"
              variant="outline"
            >
              {loading.collections ? "Đang tải..." : "Làm mới"}
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {collections.map((collection: any) => (
              <div
                key={collection.name}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedCollection === collection.name
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-gray-50"
                }`}
                onClick={() => setSelectedCollection(collection.name)}
              >
                <div className="font-medium">{collection.name}</div>
                <div className="text-sm opacity-70">
                  {collection.document_count || 0} tài liệu
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="w-1/3">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Tài liệu
            {selectedCollection && (
              <Button
                onClick={loadDocuments}
                disabled={loading.documents}
                size="sm"
                variant="outline"
              >
                {loading.documents ? "Đang tải..." : "Làm mới"}
              </Button>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!selectedCollection ? (
            <div className="text-center text-gray-500 py-8">
              Chọn một bộ sưu tập để xem tài liệu
            </div>
          ) : (
            <div className="space-y-2">
              {documents.map((doc: any) => (
                <div
                  key={doc.id || doc.title}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedDocument === (doc.id || doc.title)
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-gray-50"
                  }`}
                  onClick={() => setSelectedDocument(doc.id || doc.title)}
                >
                  <div className="font-medium truncate">
                    {doc.title || doc.name}
                  </div>
                  <div className="text-xs opacity-70 truncate">
                    {doc.path || doc.file_path}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="w-1/3">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span>Câu hỏi</span>
              {selectedDocument && (
                <span className="text-sm font-normal text-gray-500">
                  ({questions.length} câu hỏi)
                </span>
              )}
            </div>
            {selectedDocument && (
              <div className="flex gap-2">
                <Button onClick={handleAddQuestion} size="sm">
                  Thêm câu hỏi
                </Button>
                <Button
                  onClick={loadQuestions}
                  disabled={loading.questions}
                  size="sm"
                  variant="outline"
                >
                  {loading.questions ? "Đang tải..." : "Làm mới"}
                </Button>
                <Button
                  onClick={() => {
                    console.log("Force test load questions");
                    questionsService
                      .getDocumentQuestions(
                        "quy_trinh_cap_ho_tich_cap_xa",
                        "DOC_001"
                      )
                      .then((result) => {
                        console.log("Test result:", result);
                        setQuestions(result);
                      })
                      .catch((err) => console.error("Test error:", err));
                  }}
                  size="sm"
                  variant="ghost"
                >
                  Test
                </Button>
              </div>
            )}
          </CardTitle>
          {selectedDocument && (
            <Input
              placeholder="Tìm kiếm câu hỏi..."
              value={searchQuestions}
              onChange={(e) => setSearchQuestions(e.target.value)}
              className="mt-2"
            />
          )}
        </CardHeader>
        <CardContent>
          {!selectedDocument ? (
            <div className="text-center text-gray-500 py-8">
              Chọn một tài liệu để xem câu hỏi
            </div>
          ) : loading.questions ? (
            <div className="text-center text-gray-500 py-8">
              Đang tải câu hỏi...
            </div>
          ) : filteredQuestions.length === 0 && questions.length > 0 ? (
            <div className="text-center text-gray-500 py-8">
              Không tìm thấy câu hỏi phù hợp với từ khóa "{searchQuestions}"
              <br />
              <span className="text-sm">
                ({questions.length} câu hỏi có sẵn)
              </span>
            </div>
          ) : filteredQuestions.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              Chưa có câu hỏi nào cho tài liệu này
            </div>
          ) : (
            <div className="space-y-3">
              {filteredQuestions.map((question: any) => (
                <div
                  key={question.id}
                  className="p-3 border rounded-lg hover:bg-gray-50"
                >
                  <div className="font-medium mb-2 line-clamp-2">
                    {question.question || question.text}
                  </div>

                  <div className="flex flex-wrap gap-1 mb-2">
                    {(question.keywords || [])
                      .slice(0, 3)
                      .map((keyword: any, index: number) => (
                        <Badge
                          key={index}
                          variant="secondary"
                          className="text-xs"
                        >
                          {keyword}
                        </Badge>
                      ))}
                    {(question.keywords || []).length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{(question.keywords || []).length - 3}
                      </Badge>
                    )}
                  </div>

                  <div className="text-xs text-gray-500 mb-2">
                    Độ tin cậy:{" "}
                    {((question.confidence_threshold || 0) * 100).toFixed(0)}%
                  </div>

                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleViewQuestion(question)}
                    >
                      Xem
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleEditQuestion(question)}
                    >
                      Sửa
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDeleteQuestion(question)}
                    >
                      Xóa
                    </Button>
                  </div>
                </div>
              ))}

              {filteredQuestions.length === 0 && questions.length > 0 && (
                <div className="text-center text-gray-500 py-8">
                  Không tìm thấy câu hỏi phù hợp
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <QuestionModals
        questionModal={questionModal}
        viewModal={viewModal}
        deleteModal={deleteModal}
        onSaved={handleQuestionSaved}
        onDeleted={handleQuestionDeleted}
      />
    </div>
  );
}
