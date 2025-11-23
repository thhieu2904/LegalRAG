/**
 * ❓ ADMIN QUESTIONS COMPONENT - Clean Implementation
 * Hiển thị danh sách questions từ admin API backend
 */

import { useState, useEffect, useCallback } from "react";
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
  HelpCircle,
  RefreshCw,
  Search,
  Filter,
  AlertCircle,
  Eye,
  FileText,
  MessageSquare,
} from "lucide-react";
import {
  fetchQuestions,
  fetchCollections,
  type AdminQuestion,
  type AdminCollection,
} from "../../../api/admin-api";
import { formatCollectionName } from "../../../api/collection-mapping";

export default function AdminQuestionsManager() {
  // State management
  const [questions, setQuestions] = useState<AdminQuestion[]>([]);
  const [filteredQuestions, setFilteredQuestions] = useState<AdminQuestion[]>(
    []
  );
  const [collections, setCollections] = useState<AdminCollection[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCollection, setSelectedCollection] = useState("");
  const [limit, setLimit] = useState(50);

  // Load data functions
  const loadCollections = async () => {
    try {
      const data = await fetchCollections();
      setCollections(data);
    } catch (err) {
      console.error("❌ Error loading collections:", err);
    }
  };

  const loadQuestions = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      console.log("❓ Loading questions from admin API...");

      const data = await fetchQuestions(
        searchQuery.trim() || undefined,
        selectedCollection || undefined,
        limit
      );
      setQuestions(data);

      console.log(`✅ Loaded ${data.length} questions`);
    } catch (err) {
      console.error("❌ Error loading questions:", err);
      setError("Không thể tải danh sách questions. Vui lòng thử lại.");
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, selectedCollection, limit]);

  // Load collections on mount
  useEffect(() => {
    loadCollections();
  }, []);

  // Load questions when filters change
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      loadQuestions();
    }, 300); // Debounce search

    return () => clearTimeout(timeoutId);
  }, [searchQuery, selectedCollection, limit, loadQuestions]);

  // Local filtering for immediate response
  useEffect(() => {
    let filtered = questions;

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = questions.filter(
        (q) =>
          q.main_question.toLowerCase().includes(query) ||
          q.variants?.some((variant) =>
            variant.toLowerCase().includes(query)
          ) ||
          q.category.toLowerCase().includes(query) ||
          q.doc_id.toLowerCase().includes(query)
      );
    }

    if (selectedCollection) {
      filtered = filtered.filter((q) => q.collection === selectedCollection);
    }

    setFilteredQuestions(filtered);
  }, [questions, searchQuery, selectedCollection]);

  const handleRefresh = () => {
    loadQuestions();
  };

  const handleReset = () => {
    setSearchQuery("");
    setSelectedCollection("");
    setLimit(50);
  };

  const getQuestionsByCollection = () => {
    const grouped: Record<string, AdminQuestion[]> = {};
    filteredQuestions.forEach((q) => {
      if (!grouped[q.collection]) {
        grouped[q.collection] = [];
      }
      grouped[q.collection].push(q);
    });
    return grouped;
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
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <HelpCircle className="w-6 h-6" />
            Quản lý Questions
          </h1>
          <p className="text-muted-foreground">
            Danh sách {filteredQuestions.length} câu hỏi từ {collections.length}{" "}
            collections
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleRefresh}
            disabled={isLoading}
            variant="outline"
          >
            <RefreshCw
              className={`w-4 h-4 mr-2 ${isLoading ? "animate-spin" : ""}`}
            />
            Làm mới
          </Button>
          <Button onClick={handleReset} variant="outline">
            <Filter className="w-4 h-4 mr-2" />
            Reset
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Bộ lọc và Tìm kiếm</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Tìm kiếm questions
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Nhập từ khóa..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Collection Filter */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Lọc theo Collection
              </label>
              <select
                className="w-full px-3 py-2 border border-input bg-background rounded-md text-sm"
                value={selectedCollection}
                onChange={(e) => setSelectedCollection(e.target.value)}
              >
                <option value="">Tất cả collections</option>
                {collections.map((collection) => (
                  <option key={collection.name} value={collection.name}>
                    {formatCollectionName(collection.name)} (
                    {collection.document_count})
                  </option>
                ))}
              </select>
            </div>

            {/* Limit */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Số lượng hiển thị
              </label>
              <select
                className="w-full px-3 py-2 border border-input bg-background rounded-md text-sm"
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
              >
                <option value={25}>25 questions</option>
                <option value={50}>50 questions</option>
                <option value={100}>100 questions</option>
                <option value={200}>200 questions</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Questions List */}
      <div className="space-y-6">
        {isLoading ? (
          // Loading skeleton
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, index) => (
              <Card key={index} className="animate-pulse">
                <CardContent className="pt-6">
                  <div className="space-y-3">
                    <div className="flex gap-2">
                      <div className="h-6 bg-gray-200 rounded w-16"></div>
                      <div className="h-6 bg-gray-200 rounded w-20"></div>
                    </div>
                    <div className="h-6 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : filteredQuestions.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-muted-foreground mb-2">
                  {searchQuery || selectedCollection
                    ? "Không tìm thấy questions"
                    : "Chưa có questions"}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {searchQuery || selectedCollection
                    ? "Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm"
                    : "Hệ thống chưa có questions nào"}
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          // Group by collection if no specific collection selected
          Object.entries(getQuestionsByCollection()).map(
            ([collectionName, collectionQuestions]) => (
              <Card key={collectionName}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <FileText className="w-5 h-5" />
                      {formatCollectionName(collectionName)}
                    </CardTitle>
                    <Badge variant="secondary">
                      {collectionQuestions.length} questions
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {collectionQuestions.map((question, index) => (
                      <div
                        key={`${question.collection}-${question.doc_id}-${index}`}
                        className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge variant="outline">
                                {question.category}
                              </Badge>
                              <Badge variant="secondary">
                                {question.doc_id}
                              </Badge>
                              {!selectedCollection && (
                                <Badge variant="outline" className="text-xs">
                                  {formatCollectionName(question.collection)}
                                </Badge>
                              )}
                            </div>

                            <h4 className="font-medium text-base mb-2">
                              {question.main_question ||
                                "Chưa có câu hỏi chính"}
                            </h4>

                            {question.variants &&
                              question.variants.length > 0 && (
                                <div className="mb-2">
                                  <span className="text-sm text-muted-foreground">
                                    Biến thể:{" "}
                                  </span>
                                  <div className="flex flex-wrap gap-1 mt-1">
                                    {question.variants
                                      .slice(0, 3)
                                      .map((variant, variantIndex) => (
                                        <Badge
                                          key={variantIndex}
                                          variant="outline"
                                          className="text-xs"
                                        >
                                          {variant}
                                        </Badge>
                                      ))}
                                    {question.variants.length > 3 && (
                                      <Badge
                                        variant="outline"
                                        className="text-xs"
                                      >
                                        +{question.variants.length - 3} khác
                                      </Badge>
                                    )}
                                  </div>
                                </div>
                              )}
                          </div>

                          <div className="flex gap-2 ml-4">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() =>
                                console.log("👁️ View question:", question)
                              }
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )
          )
        )}
      </div>

      {/* Summary */}
      {!isLoading && questions.length > 0 && (
        <Card className="bg-muted/50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-4">
                <span>
                  <strong>{filteredQuestions.length}</strong> questions hiển thị
                  {(searchQuery || selectedCollection) &&
                    ` (lọc từ ${questions.length})`}
                </span>
                <span>
                  Từ{" "}
                  <strong>
                    {Object.keys(getQuestionsByCollection()).length}
                  </strong>{" "}
                  collections
                </span>
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
