import { Link } from "react-router-dom";
import { Settings } from "lucide-react";
import logoHCC from "../../assets/LOGO_HCC.jpg";

export default function AdminHeader() {
  return (
    <div className="bg-white border-b shadow-sm">
      {/* Main header bar */}
      <div className="flex items-center px-6 py-4">
        {/* Logo bên trái */}
        <div className="w-1/4 flex items-center">
          <img
            src={logoHCC}
            alt="Logo Trung tâm Hành chính công"
            className="w-12 h-12 object-contain"
          />
        </div>

        {/* Tên trung tâm ở giữa */}
        <div className="w-1/2 text-center">
          <h1 className="font-medium text-red-600 text-lg">
            TRUNG TÂM PHỤC VỤ HÀNH CHÍNH CÔNG XÃ LONG PHÚ
          </h1>
        </div>

        {/* Thông tin admin bên phải */}
        <div className="w-1/4 text-right flex flex-col items-end space-y-1">
          <div className="flex items-center space-x-3">
            <div className="text-right">
              <div className="font-medium text-blue-600 text-base">
                Quản trị hệ thống
              </div>
              <div className="text-gray-600 text-sm">
                Admin Panel - Trợ lý Pháp luật AI
              </div>
            </div>
            <Link
              to="/"
              className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              title="Quay lại Chat"
            >
              <Settings className="h-5 w-5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
