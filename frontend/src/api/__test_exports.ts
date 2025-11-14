/**
 * 🧪 Test Document Preview API Exports
 *
 * Quick test to verify all exports are available
 */

import {
  DocumentPreviewResponse,
  getDocxPreview,
  getJsonPreview,
  getDocumentPreview,
} from "./document-preview-api";

console.log("✅ All exports loaded successfully!");
console.log("📋 Available exports:");
console.log("  - DocumentPreviewResponse (interface)");
console.log("  - getDocxPreview (function)");
console.log("  - getJsonPreview (function)");
console.log("  - getDocumentPreview (function)");

// Type check
const testResponse: DocumentPreviewResponse = {
  success: true,
  doc_id: "test",
  collection: "test",
  type: "docx",
};

console.log("✅ Type check passed:", testResponse);

export {};
