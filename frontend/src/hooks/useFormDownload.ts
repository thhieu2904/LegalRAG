import { useState } from "react";
import { ragAPI } from "@/api/axios-config";
import { storageAPI } from "@/api/storage-api";

interface DownloadResult {
  success: boolean;
  fileId: string;
  fileName: string;
}

interface AxiosError {
  response?: {
    data?: {
      detail?: string;
      message?: string;
    };
  };
  message?: string;
}

export function useFormDownload() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const downloadForm = async (
    formPath: string,
    cccd: string,
    userName: string,
    formName: string,
    fileName: string
  ): Promise<DownloadResult> => {
    setLoading(true);
    setError(null);

    try {
      // Step 1: Get form content from RAG service
      console.log("📥 Step 1: Downloading form from RAG service...");
      const formResponse = await ragAPI.get(`/forms/file/${formPath}`, {
        responseType: "blob",
      });
      const formContent = formResponse.data;
      console.log(`✅ Downloaded: ${formContent.size} bytes`);

      // Step 2: Save to storage API (auto-save)
      console.log("💾 Step 2: Saving to storage API...");
      const formData = new FormData();
      formData.append("form_file", formContent, fileName);
      formData.append("scan_cccd", cccd);
      formData.append("scan_ho_ten", userName);
      formData.append("form_name", formName);

      const saveResponse = await storageAPI.post("/save", formData);
      console.log(`✅ Saved to storage:`, saveResponse.data);

      // Step 3: Trigger browser download
      console.log("📥 Step 3: Triggering browser download...");
      const url = window.URL.createObjectURL(formContent);
      const link = document.createElement("a");
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
      console.log(`✅ Downloaded to browser: ${fileName}`);

      return {
        success: true,
        fileId: saveResponse.data.file_id,
        fileName: saveResponse.data.file_name,
      };
    } catch (err) {
      const axiosErr = err as AxiosError;
      const errorMsg =
        axiosErr.response?.data?.detail ||
        axiosErr.response?.data?.message ||
        axiosErr.message ||
        "Unknown error";
      setError(errorMsg);
      console.error("❌ Error during download/save:", errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { downloadForm, loading, error };
}
