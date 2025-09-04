import React from "react";
import { User, Calendar, MapPin, Hash, Clock, CheckCircle } from "lucide-react";
import type { CCCDData } from "../../api/qr-scanner-api";
import "./CCCDResultDisplay.css";

interface CCCDResultDisplayProps {
  data: CCCDData;
  processingTime?: number;
  className?: string;
}

export const CCCDResultDisplay: React.FC<CCCDResultDisplayProps> = ({
  data,
  processingTime,
  className = "",
}) => {
  const formatDate = (dateString: string): string => {
    try {
      // Handle various date formats
      const cleanDate = dateString.replace(/\s+/g, "");

      // Try DD/MM/YYYY format first
      if (cleanDate.includes("/")) {
        const parts = cleanDate.split("/");
        if (parts.length === 3) {
          const day = parts[0].padStart(2, "0");
          const month = parts[1].padStart(2, "0");
          const year = parts[2];
          return `${day}/${month}/${year}`;
        }
      }

      // Try DD-MM-YYYY format
      if (cleanDate.includes("-")) {
        const parts = cleanDate.split("-");
        if (parts.length === 3) {
          const day = parts[0].padStart(2, "0");
          const month = parts[1].padStart(2, "0");
          const year = parts[2];
          return `${day}/${month}/${year}`;
        }
      }

      // Return as-is if no formatting needed
      return dateString;
    } catch {
      return dateString;
    }
  };

  const formatGender = (gender: string): string => {
    const genderLower = gender.toLowerCase();
    if (
      genderLower.includes("nam") ||
      genderLower === "male" ||
      genderLower === "m"
    ) {
      return "Nam";
    } else if (
      genderLower.includes("nữ") ||
      genderLower === "female" ||
      genderLower === "f"
    ) {
      return "Nữ";
    }
    return gender;
  };

  const dataItems = [
    {
      icon: Hash,
      label: "Số CCCD",
      value: data.citizen_id,
      important: true,
    },
    {
      icon: User,
      label: "Họ và tên",
      value: data.full_name,
      important: true,
    },
    {
      icon: Calendar,
      label: "Ngày sinh",
      value: formatDate(data.date_of_birth),
    },
    {
      icon: User,
      label: "Giới tính",
      value: formatGender(data.gender),
    },
    {
      icon: MapPin,
      label: "Địa chỉ",
      value: data.address,
      multiline: true,
    },
    {
      icon: Clock,
      label: "Ngày cấp",
      value: formatDate(data.issue_date),
    },
  ];

  // Add old ID if available
  if (data.old_id) {
    dataItems.splice(2, 0, {
      icon: Hash,
      label: "Số CMND cũ",
      value: data.old_id,
      important: false,
    });
  }

  return (
    <div className={`cccd-result-display ${className}`}>
      {/* Header */}
      <div className="result-header">
        <div className="success-badge">
          <CheckCircle className="success-icon" />
          <span>Quét mã QR thành công</span>
        </div>
        {processingTime && (
          <div className="processing-time">
            <Clock className="time-icon" />
            <span>{processingTime}ms</span>
          </div>
        )}
      </div>

      {/* Data Grid */}
      <div className="data-grid">
        {dataItems.map((item, index) => (
          <div
            key={index}
            className={`data-item ${item.important ? "important" : ""} ${
              item.multiline ? "multiline" : ""
            }`}
          >
            <div className="item-header">
              <item.icon className="item-icon" />
              <label className="item-label">{item.label}</label>
            </div>
            <div className="item-value">{item.value || "N/A"}</div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="result-footer">
        <p className="disclaimer">
          ℹ️ Thông tin được trích xuất từ mã QR trên thẻ CCCD. Vui lòng kiểm tra
          lại tính chính xác.
        </p>
      </div>
    </div>
  );
};
