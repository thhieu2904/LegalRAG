/**
 * ❓ QUESTIONS MANAGEMENT - Updated với Admin API
 * Quản lý câu hỏi từ admin service thay vì mock data
 */

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Badge } from "../../components/ui/badge";
import { Search, RefreshCw, Filter, Eye, Edit, Trash2 } from "lucide-react";
import { useAdminData } from "../../hooks/useAdminData";
import { formatCollectionName } from "../../api/collection-mapping";
import type { AdminQuestion } from "../../api/admin-api";

export default function AdminQuestionsRedesigned() {
  // Use admin data hook
  const {
    collections,
    isLoadingCollections,
    questions,
    loadQuestions,
    isLoadingQuestions,
    questionsError,
  } = useAdminData();

  // Local state
  const [selectedCollection, setSelectedCollection] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  const [filteredQuestions, setFilteredQuestions] = useState<AdminQuestion[]>(
    []
  );

  // Load questions when search or collection changes
  useEffect(() => {
    const searchTerm = searchQuery.trim();
    const collectionFilter = selectedCollection || undefined;
    loadQuestions(searchTerm || undefined, collectionFilter);
  }, [searchQuery, selectedCollection, loadQuestions]);

  // Filter questions locally (additional client-side filtering)
  useEffect(() => {
    let filtered = questions;

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = questions.filter(
        (q) =>
          q.main_question.toLowerCase().includes(query) ||
          q.variants?.some((variant) =>
            variant.toLowerCase().includes(query)
          ) ||
          q.category.toLowerCase().includes(query)
      );
    }

    if (selectedCollection) {
      filtered = filtered.filter((q) => q.collection === selectedCollection);
    }

    setFilteredQuestions(filtered);
  }, [questions, searchQuery, selectedCollection]);

  const handleRefresh = () => {
    const searchTerm = searchQuery.trim();
    const collectionFilter = selectedCollection || undefined;
    loadQuestions(searchTerm || undefined, collectionFilter);
  };

  const handleReset = () => {
    setSearchQuery("");
    setSelectedCollection("");
    loadQuestions();
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Quản lý Questions</h1>
          <p className="text-muted-foreground">
            Xem danh sách câu hỏi từ {collections.length} collections
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleRefresh}
            variant="outline"
            disabled={isLoadingQuestions}
          >
            <RefreshCw
              className={`w-4 h-4 mr-2 ${
                isLoadingQuestions ? "animate-spin" : ""
              }`}
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
          <CardTitle className="text-lg">Bộ lọc</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Search Input */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Tìm kiếm câu hỏi
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Nhập từ khóa tìm kiếm..."
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
                disabled={isLoadingCollections}
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
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">
              Danh sách Questions ({filteredQuestions.length})
            </CardTitle>
            {isLoadingQuestions && (
              <div className="flex items-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span className="text-sm text-muted-foreground">
                  Đang tải...
                </span>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {questionsError ? (
            <div className="text-center py-8">
              <div className="text-red-600 mb-4">{questionsError}</div>
              <Button onClick={handleRefresh} variant="outline">
                Thử lại
              </Button>
            </div>
          ) : filteredQuestions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {isLoadingQuestions
                ? "Đang tải questions..."
                : "Không tìm thấy questions nào"}
            </div>
          ) : (
            <div className="space-y-4">
              {filteredQuestions.map((question, index) => (
                <div
                  key={`${question.collection}-${question.doc_id}-${index}`}
                  className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="secondary">{question.category}</Badge>
                        <Badge variant="outline">
                          {formatCollectionName(question.collection)}
                        </Badge>
                        <Badge variant="outline">{question.doc_id}</Badge>
                      </div>

                      <h4 className="font-medium text-lg mb-2">
                        {question.main_question}
                      </h4>

                      {question.variants && question.variants.length > 0 && (
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
                              <Badge variant="outline" className="text-xs">
                                +{question.variants.length - 3} khác
                              </Badge>
                            )}
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2 ml-4">
                      <Button size="sm" variant="outline">
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="outline">
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="outline">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
