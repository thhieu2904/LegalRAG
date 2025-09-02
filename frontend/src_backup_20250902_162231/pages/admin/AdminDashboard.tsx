import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import {
  Users,
  MessageSquare,
  Database,
  Activity,
  TrendingUp,
} from "lucide-react";

export default function AdminDashboard() {
  const stats = [
    {
      title: "Tổng câu hỏi hôm nay",
      value: "1,234",
      change: "+12%",
      icon: MessageSquare,
      color: "text-blue-600",
    },
    {
      title: "Người dùng hoạt động",
      value: "456",
      change: "+5%",
      icon: Users,
      color: "text-green-600",
    },
    {
      title: "Tài liệu pháp luật",
      value: "8,901",
      change: "+23",
      icon: Database,
      color: "text-purple-600",
    },
    {
      title: "Độ chính xác AI",
      value: "94.2%",
      change: "+2.1%",
      icon: Activity,
      color: "text-orange-600",
    },
  ];

  const recentQuestions = [
    {
      id: 1,
      question: "Thủ tục xin cấp giấy phép kinh doanh như thế nào?",
      user: "Nguyễn Văn A",
      time: "10 phút trước",
      status: "Đã trả lời",
    },
    {
      id: 2,
      question: "Quy định về thuế thu nhập cá nhân mới nhất?",
      user: "Trần Thị B",
      time: "25 phút trước",
      status: "Đang xử lý",
    },
    {
      id: 3,
      question: "Hướng dẫn thủ tục đăng ký kết hôn?",
      user: "Lê Văn C",
      time: "1 giờ trước",
      status: "Đã trả lời",
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

      {/* Stats Grid */}
      <div className="admin-content-section">
        <div className="admin-dashboard-stats-grid">
          {stats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <Card key={index} className="admin-stat-card">
                <CardHeader className="admin-stat-header">
                  <CardTitle className="admin-stat-title">
                    {stat.title}
                  </CardTitle>
                  <Icon className={`admin-stat-icon ${stat.color}`} />
                </CardHeader>
                <CardContent>
                  <div className="admin-stat-value">{stat.value}</div>
                  <p className="admin-stat-change positive">
                    <TrendingUp className="w-3 h-3" />
                    {stat.change} so với tháng trước
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      <div className="admin-content-section">
        <div className="admin-dashboard-content-grid">
          {/* Recent Questions */}
          <Card className="admin-content-card">
            <CardHeader>
              <CardTitle className="admin-card-title">
                Câu hỏi gần đây
              </CardTitle>
              <CardDescription className="admin-card-description">
                Các câu hỏi mới nhất từ người dùng
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="questions-list">
                {recentQuestions.map((question) => (
                  <div key={question.id} className="question-item">
                    <div className="question-header">
                      <p className="question-text">{question.question}</p>
                      <span
                        className={`question-status ${
                          question.status === "Đã trả lời"
                            ? "status-completed"
                            : "status-processing"
                        }`}
                      >
                        {question.status}
                      </span>
                    </div>
                    <div className="question-meta">
                      <span>{question.user}</span>
                      <span>{question.time}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* System Status */}
          <Card className="admin-content-card">
            <CardHeader>
              <CardTitle className="admin-card-title">
                Trạng thái hệ thống
              </CardTitle>
              <CardDescription className="admin-card-description">
                Tình trạng hoạt động các thành phần chính
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="system-status-list">
                <div className="system-status-item">
                  <span className="system-status-label">Backend API</span>
                  <div className="system-status-indicator">
                    <div className="status-dot status-healthy"></div>
                    <span className="system-status healthy">Hoạt động</span>
                  </div>
                </div>
                <div className="system-status-item">
                  <span className="system-status-label">Vector Database</span>
                  <div className="system-status-indicator">
                    <div className="status-dot status-healthy"></div>
                    <span className="system-status healthy">Hoạt động</span>
                  </div>
                </div>
                <div className="system-status-item">
                  <span className="system-status-label">AI Models</span>
                  <div className="system-status-indicator">
                    <div className="status-dot status-healthy"></div>
                    <span className="system-status healthy">Hoạt động</span>
                  </div>
                </div>
                <div className="system-status-item">
                  <span className="system-status-label">Text-to-Speech</span>
                  <div className="system-status-indicator">
                    <div className="status-dot status-warning"></div>
                    <span className="system-status warning">Bảo trì</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
