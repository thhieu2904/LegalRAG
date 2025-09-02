import React from "react";
import { Link, useLocation } from "react-router-dom";
import { MessageSquare, CreditCard, Settings } from "lucide-react";

const ServiceNavigation: React.FC = () => {
  const location = useLocation();

  const services = [
    {
      path: "/",
      name: "RAG Service",
      description: "Legal Document Q&A",
      icon: <MessageSquare className="w-5 h-5" />,
      color: "bg-green-500",
    },
    {
      path: "/ocr-service",
      name: "OCR Service",
      description: "CCCD Recognition",
      icon: <CreditCard className="w-5 h-5" />,
      color: "bg-blue-500",
    },
    {
      path: "/admin",
      name: "Admin Panel",
      description: "System Management",
      icon: <Settings className="w-5 h-5" />,
      color: "bg-purple-500",
    },
  ];

  // Don't show navigation on admin pages
  if (location.pathname.startsWith("/admin")) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50">
      <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Services</h3>
        <div className="space-y-2">
          {services.map((service) => (
            <Link
              key={service.path}
              to={service.path}
              className={`
                flex items-center gap-3 p-3 rounded-lg transition-all duration-200
                hover:bg-gray-50 group
                ${
                  location.pathname === service.path
                    ? "bg-blue-50 border border-blue-200"
                    : "hover:shadow-sm"
                }
              `}
            >
              <div
                className={`
                p-2 rounded-lg text-white ${service.color}
                ${location.pathname === service.path ? "shadow-sm" : ""}
              `}
              >
                {service.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div
                  className={`
                  text-sm font-medium
                  ${
                    location.pathname === service.path
                      ? "text-blue-900"
                      : "text-gray-900"
                  }
                `}
                >
                  {service.name}
                </div>
                <div
                  className={`
                  text-xs
                  ${
                    location.pathname === service.path
                      ? "text-blue-700"
                      : "text-gray-500"
                  }
                `}
                >
                  {service.description}
                </div>
              </div>
            </Link>
          ))}
        </div>

        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="text-xs text-gray-500 text-center">
            Legal RAG System
          </div>
        </div>
      </div>
    </div>
  );
};

export default ServiceNavigation;
