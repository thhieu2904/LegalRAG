import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import {
  FileText,
  Server,
  BarChart3,
  Gauge,
  Loader2,
  AlertCircle,
  MessageSquare,
  Clock,
} from "lucide-react";
import { useState, useEffect } from "react";
import {
  fetchDashboardAnalytics,
  type DashboardAnalytics,
} from "../../api/admin-api";

export default function AdminDashboard() {
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchDashboardAnalytics();
        setAnalytics(data);
        console.log("📊 Dashboard data loaded:", data);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load dashboard data";
        setError(errorMessage);
        console.error("❌ Dashboard loading error:", err);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  // Loading state
  if (loading) {
    return (
      <div className="admin-page-container admin-dashboard-page">
        <div className="admin-page-header-section">
          <div className="admin-page-header-content">
            <h1 className="admin-page-title-main">Tổng quan hệ thống</h1>
            <p className="admin-page-subtitle-main">
              Đang tải dữ liệu dashboard...
            </p>
          </div>
        </div>
        <div className="admin-content-section">
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin" />
            <span className="ml-2">Đang tải...</span>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="admin-page-container admin-dashboard-page">
        <div className="admin-page-header-section">
          <div className="admin-page-header-content">
            <h1 className="admin-page-title-main">Tổng quan hệ thống</h1>
            <p className="admin-page-subtitle-main">
              Có lỗi xảy ra khi tải dữ liệu
            </p>
          </div>
        </div>
        <div className="admin-content-section">
          <div className="flex items-center justify-center py-8 text-red-600">
            <AlertCircle className="w-6 h-6 mr-2" />
            <span>{error}</span>
          </div>
        </div>
      </div>
    );
  }

  // Helper functions for enhanced display
  const formatResponseTime = (time?: number) => {
    if (!time) return "0s";
    return time < 1 ? `${(time * 1000).toFixed(0)}ms` : `${time.toFixed(1)}s`;
  };

  const getSystemHealthColor = (status?: {
    rag_service: string;
    admin_service: string;
  }) => {
    if (!status) return "border-gray-300";
    const { rag_service, admin_service } = status;
    return rag_service === "healthy" && admin_service === "healthy"
      ? "border-green-500"
      : "border-red-500";
  };

  const getSystemHealthStatus = (status?: {
    rag_service: string;
    admin_service: string;
  }) => {
    if (!status) return "Đang kiểm tra...";
    const { rag_service, admin_service } = status;
    return rag_service === "healthy" && admin_service === "healthy"
      ? "Hệ thống hoạt động bình thường"
      : "Phát hiện sự cố hệ thống";
  };

  const isSystemHealthy = (status?: {
    rag_service: string;
    admin_service: string;
  }) => {
    if (!status) return false;
    const { rag_service, admin_service } = status;
    return rag_service === "healthy" && admin_service === "healthy";
  }; // Enhanced stats with better context
  const heroStats = [
    {
      title: "Hoạt động hôm nay",
      value: analytics?.stats.total_queries_today?.toString() || "0",
      subtitle: analytics?.stats.active_sessions
        ? `${analytics.stats.active_sessions} phiên đang hoạt động`
        : "Không có phiên nào",
      icon: BarChart3,
      color: "text-blue-600",
      bgColor: "bg-blue-50",
    },
    {
      title: "Cơ sở dữ liệu",
      value: analytics?.stats.total_documents?.toString() || "0",
      subtitle: `Trên ${analytics?.stats.total_collections || 0} bộ thủ tục`,
      icon: FileText,
      color: "text-purple-600",
      bgColor: "bg-purple-50",
    },
    {
      title: "Hiệu suất",
      value: formatResponseTime(analytics?.stats.avg_response_time || 0),
      subtitle: "Thời gian phản hồi trung bình",
      icon: Gauge,
      color:
        analytics?.stats.avg_response_time &&
        analytics.stats.avg_response_time > 10
          ? "text-yellow-600"
          : "text-green-600",
      bgColor:
        analytics?.stats.avg_response_time &&
        analytics.stats.avg_response_time > 10
          ? "bg-yellow-50"
          : "bg-green-50",
    },
    {
      title: "Hệ thống",
      value:
        analytics?.system_status.rag_service === "healthy" &&
        analytics?.system_status.admin_service === "healthy"
          ? "Tốt"
          : "Cảnh báo",
      subtitle: getSystemHealthStatus(),
      icon: Server,
      color: getSystemHealthColor(),
      bgColor:
        analytics?.system_status.rag_service === "healthy" &&
        analytics?.system_status.admin_service === "healthy"
          ? "bg-green-50"
          : "bg-yellow-50",
    },
  ];

  // Mock sessions data based on your session structure
  const mockSessions = [
    {
      session_id: "20250927-002",
      created_at: 1759003886.5412395,
      last_accessed: 1759003916.67418,
      query_count: 3,
      is_active: true,
      current_document: "01. Đăng ký khai sinh",
      current_collection: "quy_trinh_cap_ho_tich_cap_xa",
      confidence_level: 1.0,
      last_query: "Thủ tục đăng ký khai sinh cần những giấy tờ gì?",
      time_ago: "5 phút trước",
    },
    {
      session_id: "20250927-001",
      created_at: 1759001234.123456,
      last_accessed: 1759002800.987654,
      query_count: 7,
      is_active: false,
      current_document: "02. Đăng ký kết hôn",
      current_collection: "quy_trinh_cap_ho_tich_cap_xa",
      confidence_level: 0.85,
      last_query: "Quy trình đăng ký kết hôn tại UBND cấp xã như thế nào?",
      time_ago: "2 giờ trước",
    },
    {
      session_id: "20250926-003",
      created_at: 1758917234.56789,
      last_accessed: 1758918000.123456,
      query_count: 2,
      is_active: false,
      current_document: "03. Cấp lại giấy khai sinh",
      current_collection: "quy_trinh_cap_ho_tich_cap_xa",
      confidence_level: 0.92,
      last_query: "Làm sao để cấp lại giấy khai sinh bị mất?",
      time_ago: "1 ngày trước",
    },
    {
      session_id: "20250926-002",
      created_at: 1758910000.111222,
      last_accessed: 1758912000.333444,
      query_count: 5,
      is_active: false,
      current_document: "04. Đăng ký ly hôn",
      current_collection: "quy_trinh_cap_ho_tich_cap_xa",
      confidence_level: 0.78,
      last_query: "Thủ tục ly hôn đơn phương cần những điều kiện gì?",
      time_ago: "1 ngày trước",
    },
    {
      session_id: "20250925-001",
      created_at: 1758830000.555666,
      last_accessed: 1758832000.777888,
      query_count: 1,
      is_active: false,
      current_document: "05. Đổi tên",
      current_collection: "quy_trinh_cap_ho_tich_cap_xa",
      confidence_level: 0.65,
      last_query: "Quy trình đổi tên trong giấy khai sinh?",
      time_ago: "2 ngày trước",
    },
  ];

  return (
    <div className="admin-page-container admin-dashboard-page">
      {/* Header */}
      <div className="admin-page-header-section">
        <div className="admin-page-header-content">
          <h1 className="admin-page-title-main">Tổng quan hệ thống</h1>
          <p className="admin-page-subtitle-main">
            Theo dõi hoạt động và hiệu suất của hệ thống Trợ lý Pháp luật AI
          </p>
        </div>
      </div>

      {/* Hero Stats */}
      <div className="admin-content-section">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {heroStats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <Card
                key={index}
                className="relative overflow-hidden border-0 shadow-sm hover:shadow-md transition-shadow"
              >
                <div
                  className={`absolute inset-0 ${stat.bgColor} opacity-10`}
                ></div>
                <CardContent className="relative p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600 mb-1">
                        {stat.title}
                      </p>
                      <p className={`text-3xl font-bold ${stat.color} mb-1`}>
                        {stat.value}
                      </p>
                      <p className="text-xs text-gray-500">{stat.subtitle}</p>
                    </div>
                    <div
                      className={`${stat.bgColor} p-3 rounded-full opacity-80`}
                    >
                      <Icon className={`w-6 h-6 ${stat.color}`} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* System Status Banner */}
        <div className="mt-6">
          <Card
            className={`border-l-4 ${getSystemHealthColor(
              analytics?.system_status
            )} bg-gradient-to-r from-white to-gray-50`}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div
                    className={`w-3 h-3 rounded-full ${
                      isSystemHealthy(analytics?.system_status)
                        ? "bg-green-500 animate-pulse"
                        : "bg-red-500"
                    }`}
                  ></div>
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      Trạng thái hệ thống
                    </h3>
                    <p className="text-sm text-gray-600">
                      {getSystemHealthStatus(analytics?.system_status)} • Thời
                      gian phản hồi:{" "}
                      {formatResponseTime(analytics?.stats?.avg_response_time)}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">Cập nhật lần cuối</p>
                  <p className="text-xs text-gray-400">
                    {new Date().toLocaleString("vi-VN")}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Active Sessions Overview */}
      <div className="admin-content-section">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-4">
                <CardTitle className="text-xl font-semibold text-gray-900 flex items-center">
                  <MessageSquare className="w-5 h-5 mr-2 text-green-600" />
                  Phiên làm việc hoạt động
                </CardTitle>
                <CardDescription className="text-gray-600">
                  Danh sách các phiên tương tác và câu hỏi gần đây
                </CardDescription>
              </CardHeader>
              <CardContent>
                {mockSessions.length > 0 ? (
                  <div className="space-y-4">
                    {mockSessions.map((session, index) => (
                      <div
                        key={index}
                        className="flex items-start justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors border-l-4 border-blue-500"
                      >
                        <div className="flex items-start space-x-3 flex-1">
                          <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mt-1">
                            <MessageSquare className="w-5 h-5 text-green-600" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <h4 className="font-semibold text-gray-900">
                                Session {session.session_id}
                              </h4>
                              <span
                                className={`px-2 py-1 text-xs rounded-full ${
                                  session.is_active
                                    ? "bg-green-100 text-green-800"
                                    : "bg-gray-100 text-gray-600"
                                }`}
                              >
                                {session.is_active
                                  ? "Hoạt động"
                                  : "Đã kết thúc"}
                              </span>
                            </div>
                            <p className="text-sm text-gray-700 mb-2 line-clamp-2">
                              <strong>Câu hỏi:</strong> {session.last_query}
                            </p>
                            <div className="flex items-center space-x-4 text-xs text-gray-500">
                              <span className="flex items-center">
                                <FileText className="w-3 h-3 mr-1" />
                                {session.current_document}
                              </span>
                              <span className="flex items-center">
                                <Clock className="w-3 h-3 mr-1" />
                                {session.time_ago}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="text-right ml-4">
                          <p className="text-2xl font-bold text-gray-900">
                            {session.query_count}
                          </p>
                          <p className="text-xs text-gray-500">câu hỏi</p>
                          <div className="mt-1">
                            <div
                              className={`w-2 h-2 rounded-full ${
                                session.confidence_level > 0.8
                                  ? "bg-green-500"
                                  : session.confidence_level > 0.6
                                  ? "bg-yellow-500"
                                  : "bg-red-500"
                              }`}
                            ></div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p className="font-medium">Chưa có phiên làm việc nào</p>
                    <p className="text-sm">
                      Dữ liệu sẽ hiển thị khi có người dùng tương tác
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Detailed System Status */}
          <div>
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-4">
                <CardTitle className="text-xl font-semibold text-gray-900 flex items-center">
                  <Server className="w-5 h-5 mr-2 text-green-600" />
                  Chi tiết hệ thống
                </CardTitle>
                <CardDescription className="text-gray-600">
                  Trạng thái các thành phần chính
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-3 h-3 rounded-full ${
                        analytics?.system_status.admin_service === "healthy"
                          ? "bg-green-500"
                          : "bg-red-500"
                      }`}
                    ></div>
                    <span className="font-medium text-gray-700">
                      Admin Service
                    </span>
                  </div>
                  <span
                    className={`text-sm px-2 py-1 rounded-full ${
                      analytics?.system_status.admin_service === "healthy"
                        ? "bg-green-100 text-green-800"
                        : "bg-red-100 text-red-800"
                    }`}
                  >
                    {analytics?.system_status.admin_service === "healthy"
                      ? "Hoạt động"
                      : "Có vấn đề"}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-3 h-3 rounded-full ${
                        analytics?.system_status.rag_service === "healthy"
                          ? "bg-green-500"
                          : "bg-red-500"
                      }`}
                    ></div>
                    <span className="font-medium text-gray-700">
                      RAG Service
                    </span>
                  </div>
                  <span
                    className={`text-sm px-2 py-1 rounded-full ${
                      analytics?.system_status.rag_service === "healthy"
                        ? "bg-green-100 text-green-800"
                        : "bg-red-100 text-red-800"
                    }`}
                  >
                    {analytics?.system_status.rag_service === "healthy"
                      ? "Hoạt động"
                      : "Lỗi kết nối"}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-3 h-3 rounded-full ${
                        analytics?.system_status.collections_accessible
                          ? "bg-green-500"
                          : "bg-red-500"
                      }`}
                    ></div>
                    <span className="font-medium text-gray-700">
                      Collections
                    </span>
                  </div>
                  <span
                    className={`text-sm px-2 py-1 rounded-full ${
                      analytics?.system_status.collections_accessible
                        ? "bg-green-100 text-green-800"
                        : "bg-red-100 text-red-800"
                    }`}
                  >
                    {analytics?.system_status.collections_accessible
                      ? `${analytics.system_status.total_collections} sẵn sàng`
                      : "Không truy cập"}
                  </span>
                </div>

                {analytics?.system_status.llm_loaded !== undefined && (
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div
                        className={`w-3 h-3 rounded-full ${
                          analytics.system_status.llm_loaded
                            ? "bg-green-500"
                            : "bg-yellow-500"
                        }`}
                      ></div>
                      <span className="font-medium text-gray-700">
                        AI Models
                      </span>
                    </div>
                    <span
                      className={`text-sm px-2 py-1 rounded-full ${
                        analytics.system_status.llm_loaded
                          ? "bg-green-100 text-green-800"
                          : "bg-yellow-100 text-yellow-800"
                      }`}
                    >
                      {analytics.system_status.llm_loaded
                        ? "Đã tải"
                        : "Đang tải"}
                    </span>
                  </div>
                )}

                {analytics?.system_status.router_ready !== undefined && (
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div
                        className={`w-3 h-3 rounded-full ${
                          analytics.system_status.router_ready
                            ? "bg-green-500"
                            : "bg-yellow-500"
                        }`}
                      ></div>
                      <span className="font-medium text-gray-700">
                        Query Router
                      </span>
                    </div>
                    <span
                      className={`text-sm px-2 py-1 rounded-full ${
                        analytics.system_status.router_ready
                          ? "bg-green-100 text-green-800"
                          : "bg-yellow-100 text-yellow-800"
                      }`}
                    >
                      {analytics.system_status.router_ready
                        ? "Sẵn sàng"
                        : "Chưa sẵn sàng"}
                    </span>
                  </div>
                )}

                {analytics?.system_status.embedding_device && (
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>Embedding Device:</strong>{" "}
                      {analytics.system_status.embedding_device}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
