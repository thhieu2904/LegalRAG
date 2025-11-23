/**
 * 📋 API INDEX - EXPORT TẤT CẢ API SERVICES
 * Import từ đây thay vì import trực tiếp từ các file riêng lẻ
 */

// RAG Service APIs
export { chatAPI, adminAPI, questionsAPI } from "./rag-api";
export type {
  ChatMessage,
  ChatResponse,
  SystemStats,
  Collection,
  Question,
} from "./rag-api";

// QR Scanner APIs
export { cccdScannerAPI } from "./qr-scanner-api";
export type { CCCDData, CCCDScanResult, ScanMode } from "./qr-scanner-api";

// Collection Mapping APIs
export {
  formatCollectionName,
  formatDocumentName,
  getAvailableCollections,
  getCollectionDisplayName,
  isValidCollection,
} from "./collection-mapping";

// Form APIs
export { formAPI } from "./form-api";
export type { FormRenderResult } from "./form-api";

// OCR Service APIs (UNUSED - commented out for future reference)
// export { ocrAPI_Service } from "./ocr-api";
// export type { CCCDData, OCRResult, OCRHistory } from "./ocr-api";

// Axios instances (nếu cần sử dụng trực tiếp)
export { ragAPI, identifillAPI } from "./axios-config";

// ========================================
// CÁCH SỬ DỤNG TRONG COMPONENTS:
// ========================================
/*

// ✅ ĐÚNG - Import từ api/index.ts
import { chatAPI, cccdScannerAPI, formAPI } from '../api';

// Trong component:
const handleSendMessage = async (message: string) => {
  try {
    const response = await chatAPI.sendMessage(message);
    console.log(response);
  } catch (error) {
    console.error(error);
  }
};

const handleScanCCCD = async (imageData: string) => {
  try {
    const result = await cccdScannerAPI.scanCCCD(imageData);
    console.log(result);
  } catch (error) {
    console.error(error);
  }
};

// ❌ SAI - Không được import trực tiếp axios
import axios from 'axios';
axios.post('http://localhost:8000/chat', ...); // ❌ KHÔNG LÀM VẬY!

*/
