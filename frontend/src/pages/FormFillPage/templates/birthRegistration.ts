import type { FormTemplateConfig } from './types';

/** Mapping of the reviewed scan_/form_ marker template.
 * The missing form_37 is intentional: never renumber an existing template.
 * No QR defaults for nationality, ethnicity, authority or the child's data.
 */
export const birthRegistration: FormTemplateConfig = {
  id: 'birth-registration-v2',
  name: 'Giấy đăng ký khai sinh',
  templateSha256: '527768935ee88fa1e3b167c2a9300fc5b0a2ba7605cd79e75808d7e6db77b3c0',
  roles: [
    { id: 'requester', label: 'Người yêu cầu' },
  ],
  fields: [
    { id: 'form_1', label: 'Cơ quan tiếp nhận (Kính gửi)', group: 'Thông tin chung' },
    { id: 'scan_ho_ten', label: 'Họ tên người yêu cầu', group: 'Người yêu cầu', roleId: 'requester', qrSource: 'field_ho_ten' },
    { id: 'scan_ngay_sinh', label: 'Ngày sinh người yêu cầu', group: 'Người yêu cầu', roleId: 'requester', qrSource: 'field_ngay_sinh' },
    { id: 'scan_dia_chi', label: 'Nơi cư trú người yêu cầu', group: 'Người yêu cầu', roleId: 'requester', qrSource: 'field_dia_chi' },
    { id: 'scan_cccd', label: 'Số căn cước người yêu cầu', group: 'Người yêu cầu', roleId: 'requester', qrSource: 'field_cccd', hint: 'Nếu cần, bổ sung loại giấy tờ, ngày cấp và nơi cấp bằng tay.' },
    { id: 'form_6', label: 'Quan hệ với người được khai sinh', group: 'Người yêu cầu' },
    { id: 'form_7', label: 'Họ tên người được khai sinh', group: 'Người được khai sinh' },
    { id: 'form_8', label: 'Ngày sinh người được khai sinh', group: 'Người được khai sinh' },
    { id: 'form_9', label: 'Ngày sinh ghi bằng chữ', group: 'Người được khai sinh' },
    { id: 'form_10', label: 'Giới tính người được khai sinh', group: 'Người được khai sinh' },
    { id: 'form_11', label: 'Dân tộc người được khai sinh', group: 'Người được khai sinh' },
    { id: 'form_12', label: 'Quốc tịch người được khai sinh', group: 'Người được khai sinh' },
    { id: 'form_13', label: 'Nơi sinh', group: 'Người được khai sinh' },
    { id: 'form_14', label: 'Quê quán', group: 'Người được khai sinh' },
    { id: 'form_15', label: 'Họ tên người mẹ', group: 'Người mẹ' },
    { id: 'form_16', label: 'Ngày sinh hoặc năm sinh người mẹ', group: 'Người mẹ', hint: 'Mẫu ghi năm sinh; chú thích cho phép ghi đủ ngày, tháng, năm nếu có.' },
    { id: 'form_17', label: 'Dân tộc người mẹ', group: 'Người mẹ' },
    { id: 'form_18', label: 'Quốc tịch người mẹ', group: 'Người mẹ' },
    { id: 'form_19', label: 'Nơi cư trú người mẹ', group: 'Người mẹ' },
    { id: 'form_20', label: 'Giấy tờ tùy thân người mẹ', group: 'Người mẹ' },
    { id: 'form_21', label: 'Họ tên người cha', group: 'Người cha' },
    { id: 'form_22', label: 'Ngày sinh hoặc năm sinh người cha', group: 'Người cha', hint: 'Mẫu ghi năm sinh; chú thích cho phép ghi đủ ngày, tháng, năm nếu có.' },
    { id: 'form_23', label: 'Dân tộc người cha', group: 'Người cha' },
    { id: 'form_24', label: 'Quốc tịch người cha', group: 'Người cha' },
    { id: 'form_25', label: 'Nơi cư trú người cha', group: 'Người cha' },
    { id: 'form_26', label: 'Giấy tờ tùy thân người cha', group: 'Người cha' },
    { id: 'form_27', label: 'Số giấy chứng nhận kết hôn', group: 'Đăng ký kết hôn' },
    { id: 'form_28', label: 'Quyển số đăng ký kết hôn', group: 'Đăng ký kết hôn' },
    { id: 'form_29', label: 'Ngày đăng ký kết hôn', group: 'Đăng ký kết hôn' },
    { id: 'form_30', label: 'Tháng đăng ký kết hôn', group: 'Đăng ký kết hôn' },
    { id: 'form_31', label: 'Năm đăng ký kết hôn', group: 'Đăng ký kết hôn' },
    { id: 'form_32', label: 'Nơi đăng ký kết hôn', group: 'Đăng ký kết hôn' },
    { id: 'form_33', label: 'Địa điểm lập tờ khai', group: 'Ngày lập tờ khai và bản sao' },
    { id: 'form_34', label: 'Ngày lập tờ khai', group: 'Ngày lập tờ khai và bản sao' },
    { id: 'form_35', label: 'Tháng lập tờ khai', group: 'Ngày lập tờ khai và bản sao' },
    { id: 'form_36', label: 'Năm lập tờ khai', group: 'Ngày lập tờ khai và bản sao' },
    { id: 'form_38', label: 'Số lượng bản sao', group: 'Ngày lập tờ khai và bản sao', hint: 'Ô Có/Không trong file gốc là hình ảnh, chưa phải ô điền tự động.' },
  ],
};
