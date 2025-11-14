import { useState } from "react";
import { identifillAPI } from "@/api/axios-config";

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

  /**
   * Download filled form with save to storage
   *
   * Flow:
   * 1. Call identifill /fill-and-download to get FILLED form (not template!)
   * 2. Save filled form to storage database
   * 3. Trigger browser download
   */
  const downloadForm = async (
    collectionId: string,
    docId: string,
    formFilename: string,
    formData: Record<string, any>,
    cccd: string,
    userName: string
  ): Promise<DownloadResult> => {
    setLoading(true);
    setError(null);

    try {
      // Step 1: Call identifill /fill-and-download to get FILLED form
      console.log("📥 Step 1: Calling identifill fill-and-download...");
      console.log(`   - Collection: ${collectionId}`);
      console.log(`   - Doc ID: ${docId}`);
      console.log(`   - Template: ${formFilename}`);
      console.log(`   - CCCD: ${cccd}`);

      const fillResponse = await identifillAPI.post(
        `/api/v1/forms/fill-and-download/${collectionId}/${docId}`,
        {
          ...formData,
          template_name: formFilename,
        },
        {
          responseType: "blob",
        }
      );

      const filledBlob = fillResponse.data;
      console.log(`✅ Got filled form: ${filledBlob.size} bytes`);

      // Step 2: Save filled form to identifill storage
      console.log("💾 Step 2: Saving filled form to storage...");
      const formDataObj = new FormData();

      // Generate proper filename
      const formName = formFilename
        .replace("_template.docx", "")
        .replace(".docx", "");
      const timestamp = new Date()
        .toISOString()
        .replace(/[-:]/g, "")
        .split(".")[0]
        .replace("T", "_");
      const savedFileName = `${formName}_${timestamp}.docx`;

      formDataObj.append("form_file", filledBlob, savedFileName);
      formDataObj.append("scan_cccd", cccd);
      formDataObj.append("scan_ho_ten", userName);
      formDataObj.append("form_name", formName);

      const saveResponse = await identifillAPI.post(
        "/api/v1/storage/save",
        formDataObj,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      const saveData = saveResponse.data;
      console.log(`✅ Saved to storage:`, saveData);

      // Step 3: Trigger browser download
      console.log("📥 Step 3: Triggering browser download...");
      const url = window.URL.createObjectURL(filledBlob);
      const link = document.createElement("a");
      link.href = url;
      link.download = savedFileName;
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
      console.log(`✅ Downloaded to browser: ${savedFileName}`);

      return {
        success: true,
        fileId: saveData.file_id || "",
        fileName: saveData.file_name || savedFileName,
      };
    } catch (err) {
      const axiosErr = err as AxiosError;
      const errorMsg =
        axiosErr.response?.data?.detail ||
        axiosErr.response?.data?.message ||
        axiosErr.message ||
        "Unknown error";
      setError(errorMsg);
      console.error("❌ Error during download/save:", {
        detail: errorMsg,
        fullError: err,
      });
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { downloadForm, loading, error };
}
