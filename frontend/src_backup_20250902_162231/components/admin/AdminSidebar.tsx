import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Mic,
  Database,
  MessageSquare,
  BookOpen,
  Settings,
  ChevronLeft,
  ChevronRight,
  Bot,
} from "lucide-react";
import { Button } from "../ui/button";
import { cn } from "../ui/utils";
import { useIsMobile } from "../../hooks/useIsMobile";
import { useEffect } from "react";

interface AdminSidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export default function AdminSidebar({
  collapsed,
  onToggleCollapse,
}: AdminSidebarProps) {
  const isMobile = useIsMobile();

  // Auto-collapse on mobile
  useEffect(() => {
    if (isMobile && !collapsed) {
      onToggleCollapse();
    }
  }, [isMobile, collapsed, onToggleCollapse]);

  const menuItems = [
    {
      id: "dashboard",
      label: "Tổng quan",
      icon: LayoutDashboard,
      path: "/admin",
      exact: true,
    },
    {
      id: "voice",
      label: "Quản lý Giọng nói",
      icon: Mic,
      path: "/admin/voice",
    },
    {
      id: "vector",
      label: "Cơ sở dữ liệu Vector",
      icon: Database,
      path: "/admin/vector",
    },
    {
      id: "legal-database",
      label: "Cơ sở dữ liệu Pháp luật",
      icon: BookOpen,
      path: "/admin/legal-database",
    },
    {
      id: "questions",
      label: "Câu hỏi mẫu",
      icon: MessageSquare,
      path: "/admin/questions",
    },
    {
      id: "models",
      label: "Cài đặt Models",
      icon: Bot,
      path: "/admin/models",
    },
    {
      id: "system",
      label: "Cấu hình Hệ thống",
      icon: Settings,
      path: "/admin/system",
    },
  ];

  return (
    <>
      {/* Mobile overlay */}
      {isMobile && !collapsed && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30"
          onClick={onToggleCollapse}
        />
      )}

      <div
        className={cn(
          "fixed left-0 top-20 bottom-16 bg-white border-r border-gray-200 transition-all duration-300 z-40",
          collapsed ? "w-16" : "w-64",
          isMobile && collapsed && "-translate-x-full"
        )}
      >
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            {!collapsed && (
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-red-600 rounded flex items-center justify-center">
                  <span className="text-white font-bold text-sm">TP</span>
                </div>
                <span className="text-red-600 font-bold text-sm">Admin</span>
              </div>
            )}
            <Button
              variant="ghost"
              onClick={onToggleCollapse}
              className="h-8 w-8 p-0"
            >
              {collapsed ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        <nav className="p-2 space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.id}
                to={item.path}
                end={item.exact}
                className={({ isActive }) =>
                  cn(
                    "flex items-center w-full rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    collapsed ? "justify-center" : "justify-start",
                    isActive
                      ? "bg-blue-600 text-white hover:bg-blue-700"
                      : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                  )
                }
                onClick={isMobile ? onToggleCollapse : undefined}
              >
                <Icon className={cn("h-4 w-4", !collapsed && "mr-3")} />
                {!collapsed && <span>{item.label}</span>}
              </NavLink>
            );
          })}
        </nav>
      </div>
    </>
  );
}
