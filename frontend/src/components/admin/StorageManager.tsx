/**
 * 📦 STORAGE MANAGER COMPONENT
 * Quản lý các form đã lưu trữ từ admin panel
 *
 * Features:
 * - Xem danh sách users có form lưu
 * - Xem danh sách form của mỗi user
 * - Download form
 * - Xóa form với confirm modal
 * - Thống kê lưu trữ
 */

import React, { useState, useEffect } from "react";
import {
  Download,
  Trash2,
  RefreshCw,
  AlertCircle,
  Users,
  FileText,
} from "lucide-react";
import * as adminApi from "../../api/admin-api";
import "./StorageManager.css";

type View = "list" | "detail";

interface SelectedUser {
  scan_cccd: string;
  scan_ho_ten: string;
  form_count: number;
}

export const StorageManager: React.FC = () => {
  // State management
  const [view, setView] = useState<View>("list");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<adminApi.StorageStats | null>(null);
  const [forms, setForms] = useState<adminApi.StoredFormInfo[]>([]);
  const [selectedUser, setSelectedUser] = useState<SelectedUser | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  // Load stats on mount
  useEffect(() => {
    loadStats();
  }, []);

  /**
   * 📊 Load storage statistics
   */
  const loadStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminApi.fetchStorageStats();
      setStats(data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to load statistics";
      setError(errorMessage);
      console.error("❌ Error loading stats:", err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 📋 Load forms for selected user
   */
  const loadUserForms = async (
    cccd: string,
    userName: string,
    formCount: number
  ) => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminApi.fetchFormsByCCCD(cccd);
      setForms(data);
      setSelectedUser({
        scan_cccd: cccd,
        scan_ho_ten: userName,
        form_count: formCount,
      });
      setView("detail");
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to load forms";
      setError(errorMessage);
      console.error("❌ Error loading forms:", err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 📥 Handle form download
   */
  const handleDownload = async (fileId: string, fileName: string) => {
    try {
      setDownloading(fileId);
      await adminApi.downloadStoredForm(fileId, fileName);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Download failed";
      setError(errorMessage);
      console.error("❌ Error downloading:", err);
    } finally {
      setDownloading(null);
    }
  };

  /**
   * 🗑️ Handle form delete
   */
  const handleDelete = async (fileId: string) => {
    try {
      setDeleting(fileId);
      await adminApi.deleteStoredForm(fileId);

      // Remove from forms list
      setForms(forms.filter((f) => f.file_id !== fileId));

      // Refresh stats
      await loadStats();

      setDeleteConfirm(null);
      console.log("✅ Form deleted successfully");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Delete failed";
      setError(errorMessage);
      console.error("❌ Error deleting:", err);
    } finally {
      setDeleting(null);
    }
  };

  /**
   * 🔄 Go back to list view
   */
  const handleBackToList = () => {
    setView("list");
    setSelectedUser(null);
    setForms([]);
    setSearchTerm("");
  };

  /**
   * 🔍 Filter forms by filename or user name
   */
  const filteredUsers =
    stats?.cccd_list.filter(
      (user) =>
        user.scan_ho_ten.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.scan_cccd.includes(searchTerm)
    ) || [];

  const filteredForms = forms.filter(
    (form) =>
      form.file_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      form.form_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      form.scan_ho_ten?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (!stats && loading) {
    return (
      <div className="storage-manager loading">
        <div className="spinner"></div>
        <p>Đang tải dữ liệu...</p>
      </div>
    );
  }

  return (
    <div className="storage-manager">
      {error && (
        <div className="error-banner">
          <AlertCircle size={20} />
          <span>{error}</span>
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {view === "list" ? (
        // 📊 STATISTICS & USERS LIST VIEW
        <div className="storage-list-view">
          <div className="header">
            <h2>📦 Quản Lý Lưu Trữ Form</h2>
            <button
              className="btn-refresh"
              onClick={loadStats}
              disabled={loading}
              title="Refresh statistics"
            >
              <RefreshCw size={18} className={loading ? "spinning" : ""} />
            </button>
          </div>

          {/* Statistics Cards */}
          {stats && (
            <div className="stats-grid">
              <div className="stat-card">
                <Users size={24} />
                <div>
                  <div className="stat-value">{stats.total_users}</div>
                  <div className="stat-label">Users</div>
                </div>
              </div>

              <div className="stat-card">
                <FileText size={24} />
                <div>
                  <div className="stat-value">{stats.total_forms}</div>
                  <div className="stat-label">Forms</div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-value">
                  {stats.total_size_mb.toFixed(2)} MB
                </div>
                <div className="stat-label">Total Size</div>
              </div>
            </div>
          )}

          {/* Search */}
          <div className="search-box">
            <input
              type="text"
              placeholder="🔍 Search by name or CCCD..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>

          {/* Users Table */}
          {stats && stats.cccd_list.length > 0 ? (
            <div className="table-container">
              <table className="storage-table">
                <thead>
                  <tr>
                    <th>Tên</th>
                    <th>CCCD</th>
                    <th>Số Form</th>
                    <th>Dung Lượng</th>
                    <th>Thao Tác</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((user) => (
                    <tr key={user.scan_cccd}>
                      <td className="user-name">{user.scan_ho_ten}</td>
                      <td className="user-cccd">{user.scan_cccd}</td>
                      <td className="form-count">
                        <span className="badge">{user.form_count}</span>
                      </td>
                      <td className="file-size">
                        {user.total_size_mb.toFixed(2)} MB
                      </td>
                      <td className="actions">
                        <button
                          className="btn btn-primary"
                          onClick={() =>
                            loadUserForms(
                              user.scan_cccd,
                              user.scan_ho_ten,
                              user.form_count
                            )
                          }
                          disabled={loading}
                        >
                          Xem Form
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">
              <FileText size={48} />
              <p>Không có form nào được lưu trữ</p>
            </div>
          )}
        </div>
      ) : (
        // 📋 USER FORMS DETAIL VIEW
        <div className="storage-detail-view">
          <div className="header">
            <div>
              <button className="btn-back" onClick={handleBackToList}>
                ← Quay Lại
              </button>
              <h2>
                📋 Form của {selectedUser?.scan_ho_ten} (
                {selectedUser?.scan_cccd})
              </h2>
            </div>
            <button
              className="btn-refresh"
              onClick={() =>
                selectedUser &&
                loadUserForms(
                  selectedUser.scan_cccd,
                  selectedUser.scan_ho_ten,
                  selectedUser.form_count
                )
              }
              disabled={loading}
              title="Refresh forms list"
            >
              <RefreshCw size={18} className={loading ? "spinning" : ""} />
            </button>
          </div>

          {/* Search */}
          <div className="search-box">
            <input
              type="text"
              placeholder="🔍 Search form by filename..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>

          {/* Forms Table */}
          {forms.length > 0 ? (
            <div className="table-container">
              <table className="storage-table">
                <thead>
                  <tr>
                    <th>Tên File</th>
                    <th>Dung Lượng</th>
                    <th>Ngày Tạo</th>
                    <th>Cập Nhật</th>
                    <th>Thao Tác</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredForms.map((form) => (
                    <tr key={form.file_id}>
                      <td className="filename">
                        <FileText size={16} />
                        {form.file_name}
                      </td>
                      <td className="file-size">
                        {(form.file_size / 1024).toFixed(2)} KB
                      </td>
                      <td className="timestamp">
                        {new Date(form.created_at).toLocaleString("vi-VN")}
                      </td>
                      <td className="timestamp">
                        {form.updated_at
                          ? new Date(form.updated_at).toLocaleString("vi-VN")
                          : "-"}
                      </td>
                      <td className="actions">
                        <button
                          className="btn btn-download"
                          onClick={() =>
                            handleDownload(form.file_id, form.file_name)
                          }
                          disabled={
                            downloading === form.file_id ||
                            deleting === form.file_id
                          }
                          title="Download form"
                        >
                          {downloading === form.file_id ? (
                            <span>⏳</span>
                          ) : (
                            <Download size={16} />
                          )}
                        </button>
                        <button
                          className="btn btn-delete"
                          onClick={() => setDeleteConfirm(form.file_id)}
                          disabled={
                            deleting === form.file_id ||
                            downloading === form.file_id
                          }
                          title="Delete form"
                        >
                          {deleting === form.file_id ? (
                            <span>⏳</span>
                          ) : (
                            <Trash2 size={16} />
                          )}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">
              <FileText size={48} />
              <p>Không có form nào cho user này</p>
            </div>
          )}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Xác Nhận Xóa</h3>
            <p>Bạn có chắc muốn xóa form này? Thao tác không thể hoàn tác.</p>
            <div className="modal-actions">
              <button
                className="btn btn-cancel"
                onClick={() => setDeleteConfirm(null)}
                disabled={deleting !== null}
              >
                Hủy
              </button>
              <button
                className="btn btn-delete"
                onClick={() => handleDelete(deleteConfirm)}
                disabled={deleting !== null}
              >
                {deleting === deleteConfirm ? "Đang xóa..." : "Xóa Form"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StorageManager;
