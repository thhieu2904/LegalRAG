import { useState } from "react";
import { Outlet } from "react-router-dom";
import AdminHeader from "../components/admin/AdminHeader";
import AdminSidebar from "../components/admin/AdminSidebar";

export default function AdminLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="admin-layout h-screen bg-gray-50 flex flex-col overflow-hidden">
      <AdminHeader />

      <div className="flex-1 flex overflow-hidden">
        <AdminSidebar
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />

        <main
          className={`flex-1 transition-all duration-300 overflow-y-auto overflow-x-hidden ${
            sidebarCollapsed ? "ml-16" : "ml-64"
          }`}
          style={{ height: "calc(100vh - 80px - 60px)" }}
        >
          <div className="p-6 h-full">
            <div className="max-w-7xl mx-auto h-full">
              <Outlet />
            </div>
          </div>
        </main>
      </div>

      <footer className="bg-gray-100 border-t border-gray-200 py-3">
        <div className="text-center text-gray-600 text-sm space-y-1">
          <div>
            <span className="font-medium">Cơ quan chủ quản:</span> TRUNG TÂM PHỤ
            VỤ HÀNH CHÍNH CÔNG XÃ LONG PHÚ
          </div>
          <div>
            <span className="font-medium">Địa chỉ:</span> Ấp 4, xã Long Phú - TP
            Cần Thơ | <span className="font-medium">Điện thoại:</span>{" "}
            0907007397
          </div>
        </div>
      </footer>
    </div>
  );
}
