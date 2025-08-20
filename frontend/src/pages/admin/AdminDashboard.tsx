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
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Tổng quan hệ thống</h1>
        <p className="text-gray-600 mt-2">
          Theo dõi hoạt động và hiệu suất của hệ thống Trợ lý Pháp luật AI
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card key={index} className="relative overflow-hidden">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  {stat.title}
                </CardTitle>
                <Icon className={`h-4 w-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">
                  {stat.value}
                </div>
                <p className="text-xs text-green-600 flex items-center mt-1">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  {stat.change} so với tháng trước
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Questions */}
        <Card>
          <CardHeader>
            <CardTitle>Câu hỏi gần đây</CardTitle>
            <CardDescription>
              Các câu hỏi mới nhất từ người dùng
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentQuestions.map((question) => (
                <div
                  key={question.id}
                  className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {question.question}
                    </p>
                    <p className="text-xs text-gray-500">
                      {question.user} • {question.time}
                    </p>
                  </div>
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      question.status === "Đã trả lời"
                        ? "bg-green-100 text-green-800"
                        : "bg-yellow-100 text-yellow-800"
                    }`}
                  >
                    {question.status}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* System Status */}
        <Card>
          <CardHeader>
            <CardTitle>Trạng thái hệ thống</CardTitle>
            <CardDescription>
              Tình trạng hoạt động các thành phần chính
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  Backend API
                </span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-sm text-green-600">Hoạt động</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  Vector Database
                </span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-sm text-green-600">Hoạt động</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  AI Models
                </span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-sm text-green-600">Hoạt động</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  Text-to-Speech
                </span>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></div>
                  <span className="text-sm text-yellow-600">Bảo trì</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
