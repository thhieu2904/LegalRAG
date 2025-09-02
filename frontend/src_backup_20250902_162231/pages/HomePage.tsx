import React from "react";
import { Link } from "react-router-dom";
import {
  MessageSquare,
  CreditCard,
  ArrowRight,
  Zap,
  Shield,
  Clock,
  Search,
} from "lucide-react";

const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <div className="relative pt-16 pb-32 flex content-center items-center justify-center min-h-screen-75">
        <div className="container mx-auto px-4">
          <div className="text-center">
            <h1 className="text-5xl font-bold text-gray-900 leading-tight mb-6">
              Legal RAG System
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
              Hệ thống AI hỗ trợ thủ tục hành chính Việt Nam với hai dịch vụ
              chuyên biệt:
              <br />
              <strong>RAG Service</strong> cho tìm kiếm thông tin pháp lý và{" "}
              <strong>OCR Service</strong> cho nhận dạng CCCD
            </p>

            <div className="flex flex-wrap justify-center gap-4 mb-12">
              <Link
                to="/ocr-service"
                className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                <CreditCard className="w-5 h-5" />
                OCR Service
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/"
                className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-8 py-4 rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                <MessageSquare className="w-5 h-5" />
                RAG Service
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Services Grid */}
      <div className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 max-w-6xl mx-auto">
            {/* OCR Service */}
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl p-8 hover:shadow-xl transition-all">
              <div className="flex items-center gap-4 mb-6">
                <div className="bg-blue-600 p-3 rounded-xl">
                  <CreditCard className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-gray-900">
                    OCR Service
                  </h3>
                  <p className="text-blue-700">CCCD Recognition Microservice</p>
                </div>
              </div>

              <p className="text-gray-700 mb-6">
                Dịch vụ nhận dạng căn cước công dân Việt Nam tự động, trích xuất
                thông tin chính xác từ ảnh CCCD với công nghệ VietOCR
                CPU-optimized.
              </p>

              <div className="space-y-3 mb-6">
                <div className="flex items-center gap-3">
                  <Zap className="w-5 h-5 text-blue-600" />
                  <span className="text-gray-700">Xử lý nhanh trên CPU</span>
                </div>
                <div className="flex items-center gap-3">
                  <Shield className="w-5 h-5 text-blue-600" />
                  <span className="text-gray-700">Bảo mật và riêng tư</span>
                </div>
                <div className="flex items-center gap-3">
                  <Clock className="w-5 h-5 text-blue-600" />
                  <span className="text-gray-700">Session tự động hết hạn</span>
                </div>
              </div>

              <Link
                to="/ocr-service"
                className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-all"
              >
                Sử dụng OCR Service
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {/* RAG Service */}
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-2xl p-8 hover:shadow-xl transition-all">
              <div className="flex items-center gap-4 mb-6">
                <div className="bg-green-600 p-3 rounded-xl">
                  <MessageSquare className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-gray-900">
                    RAG Service
                  </h3>
                  <p className="text-green-700">Legal Document Q&A System</p>
                </div>
              </div>

              <p className="text-gray-700 mb-6">
                Hệ thống hỏi đáp thông minh về thủ tục hành chính, tìm kiếm
                semantic trong cơ sở dữ liệu pháp luật Việt Nam với AI.
              </p>

              <div className="space-y-3 mb-6">
                <div className="flex items-center gap-3">
                  <Search className="w-5 h-5 text-green-600" />
                  <span className="text-gray-700">Tìm kiếm semantic</span>
                </div>
                <div className="flex items-center gap-3">
                  <MessageSquare className="w-5 h-5 text-green-600" />
                  <span className="text-gray-700">Chatbot AI thông minh</span>
                </div>
                <div className="flex items-center gap-3">
                  <Shield className="w-5 h-5 text-green-600" />
                  <span className="text-gray-700">
                    Thông tin pháp lý chính xác
                  </span>
                </div>
              </div>

              <Link
                to="/"
                className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold transition-all"
              >
                Sử dụng RAG Service
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Architecture Info */}
      <div className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-8">
              Kiến trúc Microservice
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="bg-blue-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white font-bold text-xl">OCR</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Port 8001</h4>
                <p className="text-gray-600 text-sm">
                  Independent OCR microservice
                </p>
              </div>
              <div className="text-center">
                <div className="bg-green-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white font-bold text-xl">RAG</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Port 8000</h4>
                <p className="text-gray-600 text-sm">
                  Main RAG service backend
                </p>
              </div>
              <div className="text-center">
                <div className="bg-purple-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white font-bold text-xl">UI</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Port 3000</h4>
                <p className="text-gray-600 text-sm">
                  React frontend interface
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gray-900 text-white py-8">
        <div className="container mx-auto px-4 text-center">
          <p className="text-gray-400">
            © 2025 Legal RAG System - Vietnamese Administrative Procedures AI
            Assistant
          </p>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
