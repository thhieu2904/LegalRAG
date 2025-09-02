/**
 * 🛠️ ADMIN PAGE - QUẢN LÝ RAG SERVICE
 * Trang admin tổng hợp cho RAG service
 */
import React, { useState, useEffect } from "react";
import {
  Settings,
  Database,
  Activity,
  Users,
  MessageSquare,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  XCircle,
} from "lucide-react";
import { adminAPI, questionsAPI } from "../../api";
import type { SystemStats, Collection, Question } from "../../api";

const AdminPage: React.FC = () => {
  // State management
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<
    "overview" | "database" | "questions"
  >("overview");

  // Load data khi component mount
  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Load parallel data
      const [statsData, collectionsData, questionsData] = await Promise.all([
        adminAPI.getSystemStats(),
        adminAPI.getCollections(),
        questionsAPI.getQuestions(),
      ]);

      setStats(statsData);
      setCollections(collectionsData);
      setQuestions(questionsData);
    } catch (error) {
      console.error("Failed to load admin data:", error);
      setError("Không thể tải dữ liệu admin. Vui lòng thử lại.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRebuildVectorDB = async () => {
    if (
      !confirm(
        "Bạn có chắc muốn rebuild Vector Database? Quá trình này có thể mất vài phút."
      )
    ) {
      return;
    }

    try {
      const result = await adminAPI.rebuildVectorDB();
      alert(`Success: ${result.message}`);
      // Reload stats after rebuild
      const newStats = await adminAPI.getSystemStats();
      setStats(newStats);
    } catch (error) {
      console.error("Failed to rebuild Vector DB:", error);
      alert("Lỗi khi rebuild Vector Database");
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case "healthy":
      case "active":
      case "online":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "warning":
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case "error":
      case "offline":
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Activity className="w-5 h-5 text-gray-500" />;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center gap-3">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
          <span className="text-gray-600">Đang tải dữ liệu admin...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Settings className="w-6 h-6 text-purple-600" />
            <h1 className="text-xl font-semibold text-gray-800">
              Admin Dashboard
            </h1>
            <span className="text-sm text-gray-500">
              • RAG Service Management
            </span>
          </div>

          <button
            onClick={loadAdminData}
            className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="max-w-7xl mx-auto p-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-600">{error}</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="max-w-7xl mx-auto p-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="border-b border-gray-200">
            <nav className="flex">
              {[
                { key: "overview", label: "Tổng quan", icon: Activity },
                { key: "database", label: "Database", icon: Database },
                { key: "questions", label: "Questions", icon: MessageSquare },
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() =>
                    setActiveTab(
                      tab.key as "overview" | "database" | "questions"
                    )
                  }
                  className={`flex items-center gap-2 px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                    activeTab === tab.key
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700"
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {/* Overview Tab */}
            {activeTab === "overview" && stats && (
              <div className="space-y-6">
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <div className="flex items-center gap-3">
                      <Users className="w-8 h-8 text-blue-600" />
                      <div>
                        <p className="text-2xl font-bold text-blue-900">
                          {stats.totalUsers}
                        </p>
                        <p className="text-sm text-blue-700">Total Users</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                    <div className="flex items-center gap-3">
                      <MessageSquare className="w-8 h-8 text-green-600" />
                      <div>
                        <p className="text-2xl font-bold text-green-900">
                          {stats.totalChats}
                        </p>
                        <p className="text-sm text-green-700">Total Chats</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                    <div className="flex items-center gap-3">
                      <Database className="w-8 h-8 text-purple-600" />
                      <div>
                        <p className="text-2xl font-bold text-purple-900">
                          {collections.length}
                        </p>
                        <p className="text-sm text-purple-700">Collections</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(stats.systemHealth)}
                      <div>
                        <p className="text-lg font-bold text-gray-900 capitalize">
                          {stats.systemHealth}
                        </p>
                        <p className="text-sm text-gray-700">System Status</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* System Health */}
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <Activity className="w-5 h-5" />
                    System Health
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <span className="text-gray-700">RAG Service</span>
                      {getStatusIcon(stats.systemHealth)}
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <span className="text-gray-700">Vector Database</span>
                      {getStatusIcon(stats.vectordbStatus)}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Database Tab */}
            {activeTab === "database" && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-800">
                    Vector Database Management
                  </h3>
                  <button
                    onClick={handleRebuildVectorDB}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Rebuild VectorDB
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {collections.map((collection) => (
                    <div
                      key={collection.id}
                      className="bg-white border border-gray-200 rounded-lg p-4"
                    >
                      <h4 className="font-medium text-gray-800 mb-2">
                        {collection.name}
                      </h4>
                      <p className="text-sm text-gray-600 mb-2">
                        {collection.documentsCount} documents
                      </p>
                      <p className="text-xs text-gray-500">
                        Created:{" "}
                        {new Date(collection.createdAt).toLocaleDateString(
                          "vi-VN"
                        )}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Questions Tab */}
            {activeTab === "questions" && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-800">
                    Questions Management
                  </h3>
                  <span className="text-sm text-gray-500">
                    {questions.length} questions total
                  </span>
                </div>

                <div className="space-y-3">
                  {questions.map((question) => (
                    <div
                      key={question.id}
                      className="bg-white border border-gray-200 rounded-lg p-4"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-gray-800 mb-2">
                            {question.question}
                          </p>
                          <div className="flex items-center gap-4 text-sm text-gray-500">
                            <span>Collection: {question.collection}</span>
                            <span>
                              {new Date(question.createdAt).toLocaleDateString(
                                "vi-VN"
                              )}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 ml-4">
                          <button className="p-1 text-blue-600 hover:bg-blue-50 rounded">
                            <Settings className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;
