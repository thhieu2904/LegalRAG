/**
 * useFormDataManager Hook
 * Quản lý trạng thái dữ liệu form, tracking user edits, và conflict detection
 */

import { useState, useCallback } from "react";
import type { CCCDData } from "../api/qr-scanner-api";

export interface FormDataManagerState {
  cccdData: CCCDData | null;
  manualData: Record<string, string>;
  userEditedFields: Set<string>;
}

export interface FormDataManagerActions {
  handleManualDataChange: (fieldName: string, value: string) => void;
  handleQRScanResult: (
    data: CCCDData,
    onConflict?: (conflicts: string[]) => Promise<boolean>
  ) => Promise<void>;
  resetQRScan: () => void;
  resetAllData: () => void;
  getFinalData: () => Record<string, string>;
  isFieldEdited: (fieldName: string) => boolean;
  getFieldValue: (fieldName: string) => string;
  getFieldSource: (fieldName: string) => "manual" | "cccd" | "empty";
}

export interface UseFormDataManagerReturn
  extends FormDataManagerState,
    FormDataManagerActions {}

export const useFormDataManager = (): UseFormDataManagerReturn => {
  const [cccdData, setCccdData] = useState<CCCDData | null>(null);
  const [manualData, setManualData] = useState<Record<string, string>>({});
  const [userEditedFields, setUserEditedFields] = useState<Set<string>>(
    new Set()
  );

  // Xử lý khi user chỉnh sửa manual
  const handleManualDataChange = useCallback(
    (fieldName: string, value: string) => {
      setManualData((prev) => ({
        ...prev,
        [fieldName]: value,
      }));

      // Track field đã được edit
      setUserEditedFields((prev) => new Set(prev).add(fieldName));

      console.log(`✏️ Manual data updated: ${fieldName} = "${value}"`);
    },
    []
  );

  // Xử lý kết quả QR scan với conflict detection
  const handleQRScanResult = useCallback(
    async (
      data: CCCDData,
      onConflict?: (conflicts: string[]) => Promise<boolean>
    ) => {
      console.log("📱 QR scan result received:", data);

      // Create mapping từ CCCD field names - Manual data và QR data đều dùng prefix scan_
      const qrDataMap: Record<string, string> = {
        scan_ho_ten: data.scan_ho_ten || "",
        scan_cccd: data.scan_cccd || "",
        scan_ngay_sinh: data.scan_ngay_sinh || "",
        scan_gioi_tinh: data.scan_gioi_tinh || "",
        scan_dia_chi: data.scan_dia_chi || "",
        scan_ngay_cap: data.scan_ngay_cap || "",
      };

      // Kiểm tra conflicts với manual data
      const conflicts: string[] = [];
      Object.entries(qrDataMap).forEach(([fieldName, qrValue]) => {
        const manualValue = manualData[fieldName];
        // Only consider it a conflict if both values exist and are different
        if (
          qrValue &&
          qrValue.trim() !== "" &&
          manualValue &&
          manualValue.trim() !== "" &&
          qrValue !== manualValue
        ) {
          conflicts.push(fieldName);
          console.log(
            `⚡ Conflict detected in field "${fieldName}": manual="${manualValue}" vs qr="${qrValue}"`
          );
        }
      });

      console.log("🔍 Detected conflicts:", conflicts);

      // ALWAYS update CCCD data first so UI shows the scanned data
      setCccdData(data);
      console.log("✅ CCCD data updated from QR scan");

      // Nếu có conflicts và có callback xử lý
      if (conflicts.length > 0 && onConflict) {
        const shouldOverride = await onConflict(conflicts);

        if (shouldOverride) {
          // User chọn ghi đè - CCCD data đã được set rồi
          // Xóa manual data cho các trường conflict
          setManualData((prev) => {
            const newData = { ...prev };
            conflicts.forEach((field) => delete newData[field]);
            return newData;
          });
          // Remove các field conflict khỏi edited list
          setUserEditedFields((prev) => {
            const newSet = new Set(prev);
            conflicts.forEach((field) => newSet.delete(field));
            return newSet;
          });
          console.log(
            "✅ User chose QR data, manual data cleared for conflicts"
          );
        } else {
          // User chọn giữ manual data - revert CCCD data về rỗng
          setCccdData({
            scan_ho_ten: "",
            scan_cccd: "",
            scan_ngay_sinh: "",
            scan_gioi_tinh: "",
            scan_dia_chi: "",
            scan_ngay_cap: "",
          });
          console.log("✅ User chose manual data, CCCD data cleared");
        }
      } else {
        console.log("✅ QR scan successful (no conflicts)");
      }
    },
    [manualData]
  );

  // Reset QR scan data
  const resetQRScan = useCallback(() => {
    setCccdData(null);
    console.log("🔄 QR scan data reset");
  }, []);

  // Reset tất cả dữ liệu
  const resetAllData = useCallback(() => {
    setCccdData(null);
    setManualData({});
    setUserEditedFields(new Set());
    console.log("🔄 All form data reset");
  }, []);

  // Lấy dữ liệu cuối cùng để download (manual override cccd)
  const getFinalData = useCallback(() => {
    return {
      ...cccdData,
      ...manualData, // Manual data có priority cao hơn
    };
  }, [cccdData, manualData]);

  // Kiểm tra field đã được edit chưa
  const isFieldEdited = useCallback(
    (fieldName: string) => {
      return userEditedFields.has(fieldName);
    },
    [userEditedFields]
  );

  // Lấy giá trị của field (hiển thị QR data khi có, trừ khi user đã edit manual)
  const getFieldValue = useCallback(
    (fieldName: string) => {
      // Nếu user đã chỉnh sửa manual data cho field này, ưu tiên manual
      if (userEditedFields.has(fieldName) && manualData[fieldName]) {
        return manualData[fieldName];
      }
      // Ngược lại, ưu tiên CCCD data nếu có
      return (
        cccdData?.[fieldName as keyof CCCDData] || manualData[fieldName] || ""
      );
    },
    [manualData, cccdData, userEditedFields]
  );

  // Lấy nguồn gốc của field value
  const getFieldSource = useCallback(
    (fieldName: string): "manual" | "cccd" | "empty" => {
      if (manualData[fieldName]) return "manual";
      if (cccdData?.[fieldName as keyof CCCDData]) return "cccd";
      return "empty";
    },
    [manualData, cccdData]
  );

  return {
    // State
    cccdData,
    manualData,
    userEditedFields,

    // Actions
    handleManualDataChange,
    handleQRScanResult,
    resetQRScan,
    resetAllData,
    getFinalData,
    isFieldEdited,
    getFieldValue,
    getFieldSource,
  };
};
