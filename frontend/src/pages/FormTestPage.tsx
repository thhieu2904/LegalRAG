/**
 * FormTestPage - Test Form Rendering Giai đoạn 1
 * Test DOCX to HTML conversion và hiển thị
 */

import React, { useState } from "react";
import { FormRenderer } from "../components/forms/FormRenderer";
import "./FormTestPage.css";

const FormTestPage: React.FC = () => {
  const [selectedForm, setSelectedForm] = useState<{
    collectionId: string;
    docId: string;
    formFilename: string;
  } | null>(null);

  const [testResults, setTestResults] = useState<{
    backendStatus: "pending" | "success" | "error";
    frontendStatus: "pending" | "success" | "error";
    message: string;
  }>({
    backendStatus: "pending",
    frontendStatus: "pending",
    message: "Chưa test",
  });

  // Test forms có sẵn
  const testForms = [
    {
      collectionId: "quy_trinh_cap_ho_tich_cap_xa",
      docId: "DOC_001",
      formFilename: "Khai sinh.docx",
      displayName: "📋 Tờ khai đăng ký khai sinh",
    },
  ];

  const handleFormSelect = (form: (typeof testForms)[0]) => {
    setSelectedForm({
      collectionId: form.collectionId,
      docId: form.docId,
      formFilename: form.formFilename,
    });

    setTestResults({
      backendStatus: "pending",
      frontendStatus: "pending",
      message: "Đang test form rendering...",
    });
  };

  const handleFormLoadComplete = (success: boolean) => {
    if (success) {
      setTestResults({
        backendStatus: "success",
        frontendStatus: "success",
        message:
          "✅ Form rendering thành công! Backend convert DOCX → HTML và Frontend hiển thị OK",
      });
    } else {
      setTestResults({
        backendStatus: "error",
        frontendStatus: "error",
        message: "❌ Form rendering thất bại. Kiểm tra backend service",
      });
    }
  };

  const testBackendOnly = async () => {
    if (!selectedForm) return;

    try {
      setTestResults((prev) => ({
        ...prev,
        backendStatus: "pending",
        message: "Đang test backend...",
      }));

      const response = await fetch(
        `http://localhost:8002/api/v1/forms/render/${selectedForm.collectionId}/${selectedForm.docId}/${selectedForm.formFilename}`
      );

      if (response.ok) {
        const data = await response.json();
        console.log("Backend response:", data);

        setTestResults((prev) => ({
          ...prev,
          backendStatus: "success",
          message: `✅ Backend OK: ${data.data.html_content.length} chars HTML generated`,
        }));
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      setTestResults((prev) => ({
        ...prev,
        backendStatus: "error",
        message: `❌ Backend Error: ${error}`,
      }));
    }
  };

  return (
    <div className="form-test-page">
      <div className="test-header">
        <h1>🧪 Form Rendering Test - Giai đoạn 1</h1>
        <p>Test DOCX → HTML conversion và hiển thị frontend</p>
      </div>

      <div className="test-controls">
        <div className="form-selection">
          <h3>📋 Chọn Form để Test:</h3>
          <div className="form-buttons">
            {testForms.map((form, index) => (
              <button
                key={index}
                onClick={() => handleFormSelect(form)}
                className={`form-button ${
                  selectedForm?.formFilename === form.formFilename
                    ? "selected"
                    : ""
                }`}
              >
                {form.displayName}
                <br />
                <small>
                  {form.collectionId}/{form.docId}
                </small>
              </button>
            ))}
          </div>
        </div>

        {selectedForm && (
          <div className="test-actions">
            <h3>🔧 Test Actions:</h3>
            <div className="action-buttons">
              <button onClick={testBackendOnly} className="test-backend-btn">
                🔙 Test Backend Only
              </button>
              <button
                onClick={() => handleFormSelect(testForms[0])}
                className="test-full-btn"
              >
                🔄 Test Full Flow
              </button>
            </div>
          </div>
        )}

        <div className="test-status">
          <h3>📊 Test Results:</h3>
          <div className="status-grid">
            <div className={`status-item backend ${testResults.backendStatus}`}>
              <div className="status-icon">
                {testResults.backendStatus === "pending" && "⏳"}
                {testResults.backendStatus === "success" && "✅"}
                {testResults.backendStatus === "error" && "❌"}
              </div>
              <div className="status-label">Backend (DOCX→HTML)</div>
            </div>

            <div
              className={`status-item frontend ${testResults.frontendStatus}`}
            >
              <div className="status-icon">
                {testResults.frontendStatus === "pending" && "⏳"}
                {testResults.frontendStatus === "success" && "✅"}
                {testResults.frontendStatus === "error" && "❌"}
              </div>
              <div className="status-label">Frontend (HTML Render)</div>
            </div>
          </div>

          <div className="status-message">{testResults.message}</div>
        </div>
      </div>

      <div className="test-result">
        {selectedForm ? (
          <div className="form-display">
            <h3>📄 Form Preview:</h3>
            <div className="form-container">
              <FormRenderer
                collectionId={selectedForm.collectionId}
                docId={selectedForm.docId}
                formFilename={selectedForm.formFilename}
                onLoadComplete={handleFormLoadComplete}
              />
            </div>
          </div>
        ) : (
          <div className="no-form-selected">
            <p>👆 Chọn form ở trên để bắt đầu test</p>
          </div>
        )}
      </div>

      <div className="test-info">
        <h3>ℹ️ Thông tin Test:</h3>
        <ul>
          <li>
            <strong>Backend Service:</strong> IdentiFill Service (Port 8002)
          </li>
          <li>
            <strong>Endpoint:</strong>{" "}
            <code>
              /api/v1/forms/render/&#123;collection&#125;/&#123;doc&#125;/&#123;filename&#125;
            </code>
          </li>
          <li>
            <strong>Technology:</strong> Python Mammoth + FastAPI
          </li>
          <li>
            <strong>Frontend:</strong> React + dangerouslySetInnerHTML
          </li>
          <li>
            <strong>Form File:</strong> <code>Khai sinh.docx</code>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default FormTestPage;
