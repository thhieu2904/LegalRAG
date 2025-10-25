# 📋 Kế Hoạch Triển Khai Hệ Thống Lưu Trữ File CCCD

## 🎯 Mục Tiêu

Lưu trữ các file đã quét từ CCCD (từ Identifill Service) vào thư mục theo số căn cước công dân (scan_cccd), đảm bảo tính toàn vẹn và dễ quản lý.

---

## 📐 Kiến Trúc Đề Xuất

### 1. **Cấu Trúc Thư Mục Lưu Trữ**

```
data/
└── scanned_documents/
    └── {scan_cccd}/                    # Thư mục chính theo số CCCD
        ├── metadata.json               # Metadata của người dùng
        ├── original_images/            # Ảnh gốc đã quét
        │   ├── {timestamp}_image.jpg
        │   └── {timestamp}_image.jpg
        ├── processed_data/             # Dữ liệu đã xử lý
        │   ├── {timestamp}_scan_result.json
        │   └── {timestamp}_scan_result.json
        └── forms/                      # Form đã fill
            ├── {form_id}_{timestamp}.json
            └── {form_id}_{timestamp}.json
```

### 2. **Flow Triển Khai**

```
Frontend (React)
    ↓
[Quét CCCD thành công]
    ↓
POST /api/v1/cccd/save
    ↓
Identifill Service (Python)
    ├─ Validate dữ liệu
    ├─ Tạo thư mục nếu chưa có
    ├─ Lưu file + metadata
    └─ Return success + file_id
    ↓
Frontend
    └─ Store file_id vào localStorage
       (dùng để lấy lại file sau này)
```

---

## 🛠️ Chi Tiết Triển Khai

### **Phase 1: Backend (Identifill Service)**

#### 1.1 Tạo model mới cho File Storage

```python
# identifill_service/app/models/schemas.py - THÊM

class FileSaveRequest(BaseModel):
    """Request model for saving scanned files"""
    image_data: str  # Base64 encoded original image
    scan_result: CCCDData  # Parsed CCCD data
    file_type: str = "cccd_image"  # Type: cccd_image, form_data, etc.

class FileSaveResponse(BaseModel):
    """Response model for file save operation"""
    success: bool
    file_id: str  # Unique file identifier
    storage_path: str  # Server-side storage path
    message: Optional[str] = None

class FileRetrieveResponse(BaseModel):
    """Response model for file retrieval"""
    success: bool
    file_id: str
    file_data: str  # Base64 encoded
    metadata: dict
    created_at: str
    message: Optional[str] = None
```

#### 1.2 Tạo Service cho File Storage

```python
# identifill_service/app/services/file_storage_service.py - TẠO FILE MỚI

import os
import json
from datetime import datetime
from pathlib import Path
import base64
import logging
from typing import Optional, Dict, Any
import uuid
from app.core.config import settings

logger = logging.getLogger(__name__)

class FileStorageService:
    """Service để quản lý lưu trữ file CCCD được quét"""

    def __init__(self):
        # Base directory for storage
        self.base_storage_dir = Path(settings.STORAGE_DIR)
        self.scanned_docs_dir = self.base_storage_dir / "scanned_documents"

        # Create directories if not exist
        self.scanned_docs_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 File Storage initialized at: {self.scanned_docs_dir}")

    def save_cccd_scan(
        self,
        image_data: str,
        cccd_data: dict
    ) -> Dict[str, Any]:
        """
        Lưu ảnh CCCD đã quét và dữ liệu

        Args:
            image_data: Base64 encoded image
            cccd_data: Dictionary chứa parsed CCCD data

        Returns:
            Dict with file_id, storage_path, success status
        """
        try:
            # Extract CCCD number
            scan_cccd = cccd_data.get("scan_cccd")
            if not scan_cccd:
                return {"success": False, "message": "Missing CCCD number"}

            # Create CCCD-specific directory
            cccd_dir = self.scanned_docs_dir / scan_cccd
            cccd_dir.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            original_images_dir = cccd_dir / "original_images"
            processed_data_dir = cccd_dir / "processed_data"
            original_images_dir.mkdir(exist_ok=True)
            processed_data_dir.mkdir(exist_ok=True)

            # Generate file ID
            file_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()

            # Save original image
            try:
                image_bytes = base64.b64decode(image_data)
                image_path = original_images_dir / f"{file_id}_image.jpg"
                with open(image_path, 'wb') as f:
                    f.write(image_bytes)
                logger.info(f"✅ Saved image: {image_path}")
            except Exception as e:
                logger.error(f"❌ Failed to save image: {e}")
                return {"success": False, "message": f"Failed to save image: {e}"}

            # Save scan result
            scan_result = {
                **cccd_data,
                "file_id": file_id,
                "created_at": timestamp,
                "image_path": str(image_path.relative_to(self.base_storage_dir))
            }

            result_path = processed_data_dir / f"{file_id}_scan_result.json"
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(scan_result, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Saved scan result: {result_path}")

            # Update or create metadata
            metadata_path = cccd_dir / "metadata.json"
            metadata = self._load_or_create_metadata(
                metadata_path,
                cccd_data
            )
            metadata["last_updated"] = timestamp
            metadata["total_scans"] = metadata.get("total_scans", 0) + 1

            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Updated metadata: {metadata_path}")

            return {
                "success": True,
                "file_id": file_id,
                "storage_path": str(cccd_dir.relative_to(self.base_storage_dir)),
                "timestamp": timestamp,
                "message": "File saved successfully"
            }

        except Exception as e:
            logger.error(f"❌ Error saving CCCD scan: {e}")
            return {
                "success": False,
                "message": f"Error saving file: {e}"
            }

    def _load_or_create_metadata(
        self,
        metadata_path: Path,
        cccd_data: dict
    ) -> dict:
        """Load hoặc tạo mới metadata file"""
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "scan_cccd": cccd_data.get("scan_cccd"),
                "scan_ho_ten": cccd_data.get("scan_ho_ten"),
                "created_at": datetime.now().isoformat(),
                "total_scans": 0,
                "file_records": []
            }

    def get_cccd_files(self, scan_cccd: str) -> Dict[str, Any]:
        """Lấy danh sách tất cả file của một CCCD"""
        try:
            cccd_dir = self.scanned_docs_dir / scan_cccd

            if not cccd_dir.exists():
                return {
                    "success": False,
                    "message": f"No files found for CCCD: {scan_cccd}"
                }

            # Load metadata
            metadata_path = cccd_dir / "metadata.json"
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

            # List all scan results
            processed_data_dir = cccd_dir / "processed_data"
            files = []

            if processed_data_dir.exists():
                for file in sorted(processed_data_dir.glob("*_scan_result.json")):
                    with open(file, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                    files.append({
                        "file_id": file_data.get("file_id"),
                        "created_at": file_data.get("created_at"),
                        "scan_data": file_data
                    })

            return {
                "success": True,
                "scan_cccd": scan_cccd,
                "metadata": metadata,
                "files": files,
                "total_files": len(files)
            }

        except Exception as e:
            logger.error(f"❌ Error retrieving files: {e}")
            return {"success": False, "message": str(e)}

    def retrieve_file(
        self,
        scan_cccd: str,
        file_id: str
    ) -> Dict[str, Any]:
        """Lấy file cụ thể"""
        try:
            cccd_dir = self.scanned_docs_dir / scan_cccd
            processed_data_dir = cccd_dir / "processed_data"

            # Load scan result
            result_file = processed_data_dir / f"{file_id}_scan_result.json"
            if not result_file.exists():
                return {"success": False, "message": f"File not found: {file_id}"}

            with open(result_file, 'r', encoding='utf-8') as f:
                scan_result = json.load(f)

            # Load original image
            original_images_dir = cccd_dir / "original_images"
            image_file = original_images_dir / f"{file_id}_image.jpg"

            file_data = {}
            if image_file.exists():
                with open(image_file, 'rb') as f:
                    file_data = base64.b64encode(f.read()).decode()

            return {
                "success": True,
                "file_id": file_id,
                "scan_result": scan_result,
                "image_data": file_data
            }

        except Exception as e:
            logger.error(f"❌ Error retrieving file: {e}")
            return {"success": False, "message": str(e)}

    def delete_file(self, scan_cccd: str, file_id: str) -> Dict[str, Any]:
        """Xóa file cụ thể"""
        try:
            cccd_dir = self.scanned_docs_dir / scan_cccd

            # Delete image
            image_file = cccd_dir / "original_images" / f"{file_id}_image.jpg"
            if image_file.exists():
                image_file.unlink()

            # Delete result
            result_file = cccd_dir / "processed_data" / f"{file_id}_scan_result.json"
            if result_file.exists():
                result_file.unlink()

            logger.info(f"✅ Deleted file: {file_id} for CCCD: {scan_cccd}")
            return {"success": True, "message": "File deleted successfully"}

        except Exception as e:
            logger.error(f"❌ Error deleting file: {e}")
            return {"success": False, "message": str(e)}
```

#### 1.3 Cập nhật Config

```python
# identifill_service/app/core/config.py - CẬP NHẬT

class Settings(BaseSettings):
    # ... existing settings ...

    # 📁 Storage Configuration
    STORAGE_DIR: str = "data"  # Relative path: data/scanned_documents/

    # Hoặc nếu muốn absolute path:
    # STORAGE_DIR: str = os.path.join(os.path.dirname(__file__), "../../data")
```

#### 1.4 Thêm API Endpoints

```python
# identifill_service/app/api/v1/cccd.py - THÊM

from app.services.file_storage_service import FileStorageService
from app.models.schemas import FileSaveRequest, FileSaveResponse

# Initialize storage service
storage_service = FileStorageService()

@router.post("/save", response_model=FileSaveResponse)
async def save_scanned_cccd(request: FileSaveRequest):
    """
    Lưu ảnh CCCD đã quét + dữ liệu CCCD
    Tạo thư mục theo scan_cccd nếu chưa có
    """
    try:
        logger.info(f"📁 Saving CCCD scan for: {request.scan_result.get('scan_cccd')}")

        # Validate scan result
        if not request.scan_result.get("scan_cccd"):
            raise HTTPException(
                status_code=400,
                detail="Missing CCCD number in scan result"
            )

        # Save to storage
        result = storage_service.save_cccd_scan(
            request.image_data,
            request.scan_result.dict()
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return FileSaveResponse(
            success=True,
            file_id=result["file_id"],
            storage_path=result["storage_path"],
            message=result["message"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in save endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{scan_cccd}")
async def get_cccd_files(scan_cccd: str):
    """
    Lấy danh sách tất cả file được quét của một CCCD
    """
    try:
        result = storage_service.get_cccd_files(scan_cccd)

        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{scan_cccd}/{file_id}")
async def retrieve_file(scan_cccd: str, file_id: str):
    """
    Lấy file cụ thể (ảnh + dữ liệu)
    """
    try:
        result = storage_service.retrieve_file(scan_cccd, file_id)

        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/{scan_cccd}/{file_id}")
async def delete_file(scan_cccd: str, file_id: str):
    """
    Xóa file cụ thể
    """
    try:
        result = storage_service.delete_file(scan_cccd, file_id)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

### **Phase 2: Frontend (React/TypeScript)**

#### 2.1 Thêm API Service

```typescript
// frontend/src/api/cccd-storage-api.ts - TẠO FILE MỚI

import { identifillAPI } from "./axios-config";

export interface CCCDFileMetadata {
  file_id: string;
  created_at: string;
  scan_cccd: string;
  scan_ho_ten: string;
}

export const cccdStorageAPI = {
  // 💾 Lưu file CCCD vừa quét
  saveScannedFile: async (
    imageData: string,
    scanResult: any
  ): Promise<{
    success: boolean;
    file_id?: string;
    storage_path?: string;
    message?: string;
  }> => {
    try {
      const response = await identifillAPI.post("/api/v1/cccd/save", {
        image_data: imageData,
        scan_result: scanResult,
        file_type: "cccd_image",
      });
      return response.data;
    } catch (error: any) {
      console.error("❌ Save file error:", error);
      return {
        success: false,
        message: error.response?.data?.detail || "Failed to save file",
      };
    }
  },

  // 📋 Lấy danh sách file của 1 CCCD
  getFiles: async (
    scanCCCD: string
  ): Promise<{
    success: boolean;
    files?: any[];
    total_files?: number;
    message?: string;
  }> => {
    try {
      const response = await identifillAPI.get(
        `/api/v1/cccd/files/${scanCCCD}`
      );
      return response.data;
    } catch (error: any) {
      console.error("❌ Get files error:", error);
      return {
        success: false,
        message: error.response?.data?.detail || "Failed to fetch files",
      };
    }
  },

  // 📄 Lấy file cụ thể
  getFile: async (
    scanCCCD: string,
    fileId: string
  ): Promise<{
    success: boolean;
    file_id?: string;
    scan_result?: any;
    image_data?: string;
    message?: string;
  }> => {
    try {
      const response = await identifillAPI.get(
        `/api/v1/cccd/files/${scanCCCD}/${fileId}`
      );
      return response.data;
    } catch (error: any) {
      console.error("❌ Get file error:", error);
      return {
        success: false,
        message: error.response?.data?.detail || "Failed to fetch file",
      };
    }
  },

  // 🗑️ Xóa file
  deleteFile: async (
    scanCCCD: string,
    fileId: string
  ): Promise<{
    success: boolean;
    message?: string;
  }> => {
    try {
      const response = await identifillAPI.delete(
        `/api/v1/cccd/files/${scanCCCD}/${fileId}`
      );
      return response.data;
    } catch (error: any) {
      console.error("❌ Delete file error:", error);
      return {
        success: false,
        message: error.response?.data?.detail || "Failed to delete file",
      };
    }
  },
};
```

#### 2.2 Tạo Hook Custom

```typescript
// frontend/src/hooks/useCCCDFileStorage.ts - TẠO FILE MỚI

import { useState, useCallback } from "react";
import { cccdStorageAPI } from "../api/cccd-storage-api";
import type { CCCDData } from "../api/qr-scanner-api";

interface StoredFile {
  file_id: string;
  created_at: string;
  scan_data: any;
}

export const useCCCDFileStorage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [files, setFiles] = useState<StoredFile[]>([]);

  // 💾 Lưu file vừa quét
  const saveScanResult = useCallback(
    async (imageData: string, scanResult: CCCDData) => {
      setIsLoading(true);
      setError(null);

      try {
        const result = await cccdStorageAPI.saveScannedFile(
          imageData,
          scanResult
        );

        if (result.success) {
          console.log("✅ File saved successfully:", result.file_id);
          // Store file_id in localStorage
          const storedFileIds = JSON.parse(
            localStorage.getItem(`cccd_files_${scanResult.scan_cccd}`) || "[]"
          );
          storedFileIds.push({
            file_id: result.file_id,
            saved_at: new Date().toISOString(),
          });
          localStorage.setItem(
            `cccd_files_${scanResult.scan_cccd}`,
            JSON.stringify(storedFileIds)
          );

          return result;
        } else {
          throw new Error(result.message || "Failed to save file");
        }
      } catch (err) {
        const errorMsg =
          err instanceof Error ? err.message : "Unknown error occurred";
        setError(errorMsg);
        console.error("❌ Save error:", err);
        return { success: false, message: errorMsg };
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  // 📋 Lấy danh sách file
  const loadFiles = useCallback(async (scanCCCD: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await cccdStorageAPI.getFiles(scanCCCD);

      if (result.success) {
        setFiles(result.files || []);
        return result.files;
      } else {
        throw new Error(result.message || "Failed to load files");
      }
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Unknown error occurred";
      setError(errorMsg);
      setFiles([]);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 📄 Lấy file cụ thể
  const loadFile = useCallback(async (scanCCCD: string, fileId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await cccdStorageAPI.getFile(scanCCCD, fileId);

      if (result.success) {
        return result;
      } else {
        throw new Error(result.message || "Failed to load file");
      }
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Unknown error occurred";
      setError(errorMsg);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 🗑️ Xóa file
  const removeFile = useCallback(async (scanCCCD: string, fileId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await cccdStorageAPI.deleteFile(scanCCCD, fileId);

      if (result.success) {
        // Remove from local state
        setFiles((prev) => prev.filter((f) => f.file_id !== fileId));
        // Update localStorage
        const storedFileIds = JSON.parse(
          localStorage.getItem(`cccd_files_${scanCCCD}`) || "[]"
        );
        const updatedIds = storedFileIds.filter(
          (f: any) => f.file_id !== fileId
        );
        localStorage.setItem(
          `cccd_files_${scanCCCD}`,
          JSON.stringify(updatedIds)
        );
        return result;
      } else {
        throw new Error(result.message || "Failed to delete file");
      }
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Unknown error occurred";
      setError(errorMsg);
      return { success: false, message: errorMsg };
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    isLoading,
    error,
    files,
    saveScanResult,
    loadFiles,
    loadFile,
    removeFile,
  };
};
```

#### 2.3 Cập nhật QRScanner Component

```typescript
// frontend/src/components/qrscan/QRScanner.tsx - CẬP NHẬT

import { useCCCDFileStorage } from "../../hooks/useCCCDFileStorage";

export const QRScanner: React.FC<QRScannerProps> = ({
  onResult,
  onError,
  className = "",
}) => {
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { saveScanResult, isLoading: isSaving } = useCCCDFileStorage();

  const handleImageCapture = useCallback(
    async (imageData: string) => {
      setIsScanning(true);
      setError(null);

      try {
        // Quét QR code
        const result = await cccdScannerAPI.scanCCCD(imageData);

        if (result.success && result.data) {
          console.log("✅ QR scan successful:", result.data);

          // 💾 Lưu file
          console.log("💾 Saving scan result...");
          const saveResult = await saveScanResult(imageData, result.data);

          if (saveResult.success) {
            console.log("✅ File saved with ID:", saveResult.file_id);
            // Callback với data + file_id
            onResult?.(result.data, saveResult.file_id);
          } else {
            console.warn(
              "⚠️ File saved but failed to store:",
              saveResult.message
            );
            // Vẫn trả về result, chỉ warn về lỗi lưu trữ
            onResult?.(result.data, undefined);
          }
        } else {
          // ... existing error handling ...
        }
      } catch (err) {
        // ... existing error handling ...
      } finally {
        setIsScanning(false);
      }
    },
    [onResult, onError, saveScanResult]
  );

  // ... rest of component ...
};
```

#### 2.4 Tạo Component History

```typescript
// frontend/src/components/qrscan/CCCDHistoryPanel.tsx - TẠO FILE MỚI

import React, { useEffect } from "react";
import { useCCCDFileStorage } from "../../hooks/useCCCDFileStorage";
import { Trash2, Download, Calendar } from "lucide-react";

interface CCCDHistoryPanelProps {
  scanCCCD: string;
  onSelectFile?: (fileId: string) => void;
}

export const CCCDHistoryPanel: React.FC<CCCDHistoryPanelProps> = ({
  scanCCCD,
  onSelectFile,
}) => {
  const { files, isLoading, loadFiles, removeFile } = useCCCDFileStorage();

  useEffect(() => {
    loadFiles(scanCCCD);
  }, [scanCCCD, loadFiles]);

  return (
    <div className="cccd-history-panel">
      <h3>📋 Lịch Sử Quét</h3>

      {isLoading ? (
        <div className="loading">Đang tải...</div>
      ) : files.length === 0 ? (
        <div className="empty-state">Chưa có file nào được lưu</div>
      ) : (
        <div className="files-list">
          {files.map((file) => (
            <div key={file.file_id} className="file-item">
              <div className="file-info">
                <Calendar size={16} />
                <span className="date">
                  {new Date(file.created_at).toLocaleDateString("vi-VN", {
                    year: "numeric",
                    month: "2-digit",
                    day: "2-digit",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>

              <div className="file-actions">
                <button
                  className="btn-view"
                  onClick={() => onSelectFile?.(file.file_id)}
                >
                  <Download size={16} />
                </button>
                <button
                  className="btn-delete"
                  onClick={() => removeFile(scanCCCD, file.file_id)}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
```

---

## 🚀 Hướng Dẫn Triển Khai

### **Bước 1: Backend Setup**

1. Tạo file `identifill_service/app/services/file_storage_service.py`
2. Cập nhật `identifill_service/app/models/schemas.py` với các model mới
3. Cập nhật `identifill_service/app/core/config.py` với STORAGE_DIR
4. Cập nhật `identifill_service/app/api/v1/cccd.py` với endpoints mới
5. Tạo thư mục `data/` ở root project (tự động tạo khi chạy)

### **Bước 2: Frontend Setup**

1. Tạo file `frontend/src/api/cccd-storage-api.ts`
2. Tạo file `frontend/src/hooks/useCCCDFileStorage.ts`
3. Cập nhật `frontend/src/components/qrscan/QRScanner.tsx`
4. Tạo file `frontend/src/components/qrscan/CCCDHistoryPanel.tsx` (optional)

### **Bước 3: Testing**

1. Start services (Frontend + Identifill)
2. Quét CCCD → File tự động lưu
3. Check folder `data/scanned_documents/{scan_cccd}/`
4. Verify metadata.json được tạo

---

## 📊 Lợi Ích

✅ **Tính toàn vẹn**: Mỗi người dùng có thư mục riêng  
✅ **Dễ quản lý**: Organize theo CCCD  
✅ **Dễ scale**: Thêm form, documents sau  
✅ **Reversible**: Không phải DB phức tạp  
✅ **Accessible**: API đơn giản, dễ debug

---

## ⚠️ Lưu Ý

- 📁 Phải có write permission cho thư mục `data/`
- 🔒 Nên bảo vệ dữ liệu (CCCD là dữ liệu nhạy cảm)
- 📈 Khi data lớn: xem xét dùng database thay thế
- 🧹 Thêm cleanup logic nếu cần xóa cũ

---

## 🔄 Mở Rộng Sau

```
Phase 2:
- Thêm form storage
- Backup to cloud (AWS S3, Azure Blob)
- Database migration (PostgreSQL)

Phase 3:
- Analytics dashboard
- Search/filter
- Export reports
```
