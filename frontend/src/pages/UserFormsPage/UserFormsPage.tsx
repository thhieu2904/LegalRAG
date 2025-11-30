/**
 * User Forms Management Page
 * Admin interface for viewing, downloading, and deleting user-filled forms
 */

import { useEffect, useState, useMemo } from 'react';
import { RefreshCw, FileText, Download, Trash2, Users, CreditCard, FolderOpen } from 'lucide-react';
import { userFormsService } from '@/services/admin/userFormsService';
import type { UserFormItem } from '@/types/userForms.types';
import styles from './UserFormsPage.module.css';

export const UserFormsPage = () => {
  const [forms, setForms] = useState<UserFormItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [deletingForm, setDeletingForm] = useState<UserFormItem | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Fetch forms
  const fetchForms = async () => {
    setLoading(true);
    try {
      const response = await userFormsService.getUserForms();
      if (response.success) {
        setForms(response.forms);
      }
    } catch (error) {
      console.error('Error fetching forms:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForms();
  }, []);

  // Filtered forms based on search
  const filteredForms = useMemo(() => {
    if (!searchQuery.trim()) return forms;

    const query = searchQuery.toLowerCase();
    return forms.filter(
      (form) =>
        form.filename.toLowerCase().includes(query) ||
        form.session_id.toLowerCase().includes(query) ||
        form.form_name.toLowerCase().includes(query) ||
        (form.cccd_number && form.cccd_number.includes(query))
    );
  }, [forms, searchQuery]);

  // Stats
  const stats = useMemo(() => {
    const uniqueSessions = new Set(forms.map((f) => f.session_id)).size;
    const formsWithCccd = forms.filter((f) => f.cccd_number).length;
    return {
      totalForms: forms.length,
      totalSessions: uniqueSessions,
      formsWithCccd,
    };
  }, [forms]);

  // Handle download
  const handleDownload = async (form: UserFormItem) => {
    try {
      const blob = await userFormsService.downloadUserForm(form.session_id, form.filename);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = form.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading form:', error);
      alert('Lỗi khi tải file. Vui lòng thử lại.');
    }
  };

  // Handle delete
  const handleDelete = async () => {
    if (!deletingForm) return;

    setDeleteLoading(true);
    try {
      const response = await userFormsService.deleteUserForm(
        deletingForm.session_id,
        deletingForm.filename
      );
      if (response.success) {
        setForms((prev) => prev.filter((f) => f.file_path !== deletingForm.file_path));
        setDeletingForm(null);
      }
    } catch (error) {
      console.error('Error deleting form:', error);
      alert('Lỗi khi xóa file. Vui lòng thử lại.');
    } finally {
      setDeleteLoading(false);
    }
  };

  // Format file size
  const formatFileSize = (bytes: number | null): string => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  // Format date
  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return '-';
    try {
      const date = new Date(dateStr);
      return date.toLocaleString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className={styles.userFormsPage}>
      {/* Header */}
      <div className={styles.header}>
        <h1 className={styles.title}>Biểu mẫu đã điền</h1>
        <div className={styles.headerActions}>
          <input
            type="text"
            className={styles.searchInput}
            placeholder="Tìm kiếm theo tên file, session, CCCD..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button className={styles.refreshButton} onClick={fetchForms} disabled={loading}>
            <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
            Làm mới
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className={styles.statsRow}>
        <div className={styles.statCard}>
          <div className={`${styles.statIcon} ${styles.forms}`}>
            <FileText size={24} />
          </div>
          <div>
            <div className={styles.statValue}>{stats.totalForms}</div>
            <div className={styles.statLabel}>Tổng số biểu mẫu</div>
          </div>
        </div>
        <div className={styles.statCard}>
          <div className={`${styles.statIcon} ${styles.sessions}`}>
            <Users size={24} />
          </div>
          <div>
            <div className={styles.statValue}>{stats.totalSessions}</div>
            <div className={styles.statLabel}>Phiên làm việc</div>
          </div>
        </div>
        <div className={styles.statCard}>
          <div className={`${styles.statIcon} ${styles.cccd}`}>
            <CreditCard size={24} />
          </div>
          <div>
            <div className={styles.statValue}>{stats.formsWithCccd}</div>
            <div className={styles.statLabel}>Có CCCD</div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className={styles.tableContainer}>
        {loading ? (
          <div className={styles.loadingState}>
            <div className={styles.spinner} />
            <p>Đang tải danh sách biểu mẫu...</p>
          </div>
        ) : filteredForms.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>
              <FolderOpen size={40} />
            </div>
            <div className={styles.emptyTitle}>
              {searchQuery ? 'Không tìm thấy kết quả' : 'Chưa có biểu mẫu nào'}
            </div>
            <div className={styles.emptyText}>
              {searchQuery
                ? 'Thử tìm kiếm với từ khóa khác'
                : 'Các biểu mẫu do người dùng điền sẽ xuất hiện ở đây'}
            </div>
          </div>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Tên file</th>
                <th>Phiên</th>
                <th>CCCD</th>
                <th>Kích thước</th>
                <th>Ngày tạo</th>
                <th>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {filteredForms.map((form) => (
                <tr key={form.file_path}>
                  <td>
                    <div className={styles.fileInfo}>
                      <div className={styles.fileIcon}>
                        <FileText size={20} />
                      </div>
                      <div>
                        <div className={styles.fileName}>{form.filename}</div>
                        <div className={styles.formName}>{form.form_name}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className={styles.sessionBadge}>{form.session_id}</span>
                  </td>
                  <td>
                    {form.cccd_number ? (
                      <span className={styles.cccdBadge}>{form.cccd_number}</span>
                    ) : (
                      <span className={styles.noCccd}>Không có</span>
                    )}
                  </td>
                  <td>
                    <span className={styles.fileSize}>{formatFileSize(form.file_size)}</span>
                  </td>
                  <td>
                    <span className={styles.date}>{formatDate(form.created_at)}</span>
                  </td>
                  <td>
                    <div className={styles.actions}>
                      <button
                        className={`${styles.actionBtn} ${styles.downloadBtn}`}
                        onClick={() => handleDownload(form)}
                        title="Tải xuống"
                      >
                        <Download size={18} />
                      </button>
                      <button
                        className={`${styles.actionBtn} ${styles.deleteBtn}`}
                        onClick={() => setDeletingForm(form)}
                        title="Xóa"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Delete Confirm Dialog */}
      {deletingForm && (
        <div className={styles.deleteDialog} onClick={() => setDeletingForm(null)}>
          <div className={styles.deleteDialogContent} onClick={(e) => e.stopPropagation()}>
            <h3 className={styles.deleteDialogTitle}>Xác nhận xóa</h3>
            <p className={styles.deleteDialogText}>
              Bạn có chắc chắn muốn xóa biểu mẫu <strong>{deletingForm.filename}</strong>?
              <br />
              <br />
              Hành động này không thể hoàn tác.
            </p>
            <div className={styles.deleteDialogActions}>
              <button className={styles.cancelBtn} onClick={() => setDeletingForm(null)}>
                Hủy
              </button>
              <button
                className={styles.confirmDeleteBtn}
                onClick={handleDelete}
                disabled={deleteLoading}
              >
                {deleteLoading ? 'Đang xóa...' : 'Xóa'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
