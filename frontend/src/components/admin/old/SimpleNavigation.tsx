/**
 * 🧭 SIMPLE NAVIGATION - ĐIỀU HƯỚNG ĐƠN GIẢN
 * Navigation component cho 3 pages chính
 */
import { Link, useLocation } from "react-router-dom";
import { MessageSquare, Settings, CreditCard, Home } from "lucide-react";

const SimpleNavigation = () => {
  const location = useLocation();

  const navItems = [
    {
      path: "/",
      name: "Chat",
      description: "Legal RAG Assistant",
      icon: <MessageSquare className="w-5 h-5" />,
      color: "bg-green-500",
      service: "RAG Service (8000)",
    },
    {
      path: "/ocr",
      name: "OCR",
      description: "CCCD Recognition",
      icon: <CreditCard className="w-5 h-5" />,
      color: "bg-blue-500",
      service: "OCR Service (8001)",
    },
    {
      path: "/admin",
      name: "Admin",
      description: "System Management",
      icon: <Settings className="w-5 h-5" />,
      color: "bg-purple-500",
      service: "RAG Admin Panel",
    },
  ];

  return (
    <div className="fixed top-4 right-4 z-50">
      <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-4 min-w-[280px]">
        <div className="flex items-center gap-2 mb-3">
          <Home className="w-4 h-4 text-gray-600" />
          <h3 className="text-sm font-medium text-gray-900">Microservices</h3>
        </div>

        <div className="space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`
                flex items-center gap-3 p-3 rounded-lg transition-all duration-200
                hover:bg-gray-50 group border
                ${
                  location.pathname === item.path
                    ? "bg-blue-50 border-blue-200 shadow-sm"
                    : "border-transparent hover:shadow-sm"
                }
              `}
            >
              <div className={`p-2 rounded-lg text-white ${item.color}`}>
                {item.icon}
              </div>

              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h4 className="font-medium text-gray-900">{item.name}</h4>
                  {location.pathname === item.path && (
                    <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  )}
                </div>
                <p className="text-xs text-gray-600">{item.description}</p>
                <p className="text-xs text-gray-500 mt-1">{item.service}</p>
              </div>
            </Link>
          ))}
        </div>

        <div className="mt-3 pt-3 border-t border-gray-200 text-center">
          <p className="text-xs text-gray-500">Legal RAG System v1.0</p>
        </div>
      </div>
    </div>
  );
};

export default SimpleNavigation;
