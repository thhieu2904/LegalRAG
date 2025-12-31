/**
 * MetadataForm Component
 * Form for document metadata input
 */

import { useState } from 'react';
import styles from './MetadataForm.module.css';
import { Input } from '@/components/common/Input';
import { Select } from '@/components/common/Select';
import { Button } from '@/components/common/Button';
import type { ChuyenNganh, MonHoc, LoaiTaiLieu } from '@/types/admin.types';

export interface MetadataFormData {
  ma_chuyen_nganh: string; // Mã chuyên ngành
  ma_mon: string; // Mã môn học
  ma_giao_vien: string; // Mã giáo viên
  upload_type: string; // Loại tài liệu
  nam_hoc?: number; // Năm học 1-4
  so_chuong?: number; // Số chương
}

interface MetadataFormProps {
  /** Form data */
  data: MetadataFormData;
  /** Change callback */
  onChange: (data: MetadataFormData) => void;
  /** Disabled state */
  disabled?: boolean;
  /** Chuyên ngành options */
  chuyenNganhList?: ChuyenNganh[];
  /** Môn học options */
  monHocList?: MonHoc[];
  /** Loại tài liệu options */
  uploadTypeList?: LoaiTaiLieu[];
  /** Loading state for chuyên ngành */
  isLoadingChuyenNganh?: boolean;
  /** Loading state for môn học */
  isLoadingMonHoc?: boolean;
  /** Loading state for upload type */
  isLoadingUploadType?: boolean;
  /** Callback when chuyên ngành changes */
  onChuyenNganhChange?: (maChuyenNganh: string) => void;
}

const NAM_HOC_OPTIONS = [
  { value: '1', label: 'Năm 1' },
  { value: '2', label: 'Năm 2' },
  { value: '3', label: 'Năm 3' },
  { value: '4', label: 'Năm 4' },
];

export function MetadataForm({
  data,
  onChange,
  disabled = false,
  chuyenNganhList = [],
  monHocList = [],
  uploadTypeList = [],
  isLoadingChuyenNganh = false,
  isLoadingMonHoc = false,
  isLoadingUploadType = false,
  onChuyenNganhChange,
}: MetadataFormProps) {
  const [errors, setErrors] = useState<Partial<Record<keyof MetadataFormData, string>>>({});

  /**
   * Handle field change with validation
   */
  const handleChange = (field: keyof MetadataFormData, value: string | number | undefined) => {
    // Update value
    onChange({ ...data, [field]: value });

    // Realtime validation
    const newErrors = { ...errors };

    // Validate numeric fields
    if (field === 'nam_hoc' && typeof value === 'number') {
      if (value < 1 || value > 4) {
        newErrors.nam_hoc = 'Phải từ 1-4';
      } else {
        delete newErrors.nam_hoc;
      }
    }

    if (field === 'so_chuong' && typeof value === 'number') {
      if (value < 1) {
        newErrors.so_chuong = 'Phải >= 1';
      } else {
        delete newErrors.so_chuong;
      }
    }

    // Clear error for required fields when filled
    if (field === 'ma_chuyen_nganh' || field === 'ma_mon' || field === 'upload_type') {
      if (value) {
        delete newErrors[field];
      }
    }

    setErrors(newErrors);
  };

  /**
   * Clear form
   */
  const handleClear = () => {
    onChange({
      ma_chuyen_nganh: '',
      ma_mon: '',
      ma_giao_vien: data.ma_giao_vien, // Keep teacher
      upload_type: '',
      nam_hoc: undefined,
      so_chuong: undefined,
    });
    setErrors({});
  };

  return (
    <div className={styles.form}>
      <div className={styles.formHeader}>
        <h3 className={styles.formTitle}>Thông tin tài liệu</h3>
        <Button variant="ghost" size="sm" onClick={handleClear} disabled={disabled}>
          Xóa
        </Button>
      </div>

      <div className={styles.formGrid}>
        {/* Chuyên ngành */}
        <div className={styles.formField}>
          <label className={styles.label}>
            Chuyên ngành <span className={styles.required}>*</span>
          </label>
          <Select
            value={data.ma_chuyen_nganh}
            onChange={(value) => {
              handleChange('ma_chuyen_nganh', value);
              onChuyenNganhChange?.(value);
            }}
            options={chuyenNganhList.map((cn) => ({
              value: cn.ma_chuyen_nganh,
              label: cn.ten_chuyen_nganh,
            }))}
            placeholder={isLoadingChuyenNganh ? 'Đang tải...' : 'Chọn chuyên ngành'}
            disabled={disabled || isLoadingChuyenNganh}
          />
          {errors.ma_chuyen_nganh && <div className={styles.error}>{errors.ma_chuyen_nganh}</div>}
        </div>

        {/* Môn học */}
        <div className={styles.formField}>
          <label className={styles.label}>
            Môn học <span className={styles.required}>*</span>
          </label>
          <Select
            value={data.ma_mon}
            onChange={(value) => handleChange('ma_mon', value)}
            options={monHocList.map((mh) => ({
              value: mh.ma_mon,
              label: mh.ten_mon,
            }))}
            placeholder={
              isLoadingMonHoc
                ? 'Đang tải...'
                : !data.ma_chuyen_nganh
                  ? 'Chọn chuyên ngành trước'
                  : 'Chọn môn học'
            }
            disabled={disabled || isLoadingMonHoc || !data.ma_chuyen_nganh}
          />
          {errors.ma_mon && <div className={styles.error}>{errors.ma_mon}</div>}
        </div>

        {/* Loại tài liệu */}
        <div className={styles.formField}>
          <label className={styles.label}>
            Loại tài liệu <span className={styles.required}>*</span>
          </label>
          <Select
            value={data.upload_type || ''}
            onChange={(value) => handleChange('upload_type', value)}
            options={uploadTypeList.map((ut) => ({
              value: ut.ma_loai,
              label: ut.ten_loai,
            }))}
            placeholder={isLoadingUploadType ? 'Đang tải...' : 'Chọn loại'}
            disabled={disabled || isLoadingUploadType}
          />
          {errors.upload_type && <div className={styles.error}>{errors.upload_type}</div>}
        </div>

        {/* Năm học */}
        <div className={styles.formField}>
          <label className={styles.label}>Năm học (1-4)</label>
          <Select
            value={data.nam_hoc?.toString() || ''}
            onChange={(value) => handleChange('nam_hoc', value ? parseInt(value) : undefined)}
            options={NAM_HOC_OPTIONS}
            placeholder="Chọn năm học (tùy chọn)"
            disabled={disabled}
          />
          {errors.nam_hoc && <div className={styles.error}>{errors.nam_hoc}</div>}
        </div>

        {/* Số chương */}
        <div className={styles.formField}>
          <label className={styles.label}>Số chương</label>
          <Input
            type="number"
            value={data.so_chuong?.toString() || ''}
            onChange={(e) => {
              const value = e.target.value;
              handleChange('so_chuong', value ? parseInt(value) : undefined);
            }}
            placeholder="VD: 1"
            disabled={disabled}
          />
          {errors.so_chuong && <div className={styles.error}>{errors.so_chuong}</div>}
        </div>
      </div>
    </div>
  );
}
