import type { CCCDData } from './types';
import type { FormTemplateConfig } from './templates/types';

export interface FormDraft {
  values: Record<string, string>;
  scans: Record<string, CCCDData>;
  sources: Record<string, 'qr' | 'manual'>;
  scanReport: { role: string; applied: number; protected: number } | null;
}

export type DraftAction =
  | { type: 'reset' }
  | { type: 'field'; field: string; value: string }
  | { type: 'clearScan'; role: string }
  | { type: 'scan'; role: string; data: CCCDData; template: FormTemplateConfig | null };

export function createFormDraft(): FormDraft {
  return { values: {}, scans: {}, sources: {}, scanReport: null };
}

export function qrValuesForRole(
  template: FormTemplateConfig | null,
  role: string,
  data: CCCDData,
): Record<string, string> {
  if (!template || !template.roles.some((item) => item.id === role)) return {};
  const result: Record<string, string> = {};
  for (const field of template.fields) {
    if (field.roleId !== role || !field.qrSource) continue;
    const value = field.qrSource === 'identity_document'
      ? `Căn cước số ${data.field_cccd}, cấp ngày ${data.field_ngay_cap}`
      : data[field.qrSource];
    if (value?.trim()) result[field.id] = value.trim();
  }
  return result;
}

export function draftReducer(draft: FormDraft, action: DraftAction): FormDraft {
  switch (action.type) {
    case 'reset':
      return createFormDraft();
    case 'field':
      return {
        ...draft,
        values: { ...draft.values, [action.field]: action.value },
        sources: { ...draft.sources, [action.field]: 'manual' },
      };
    case 'clearScan': {
      const scans = { ...draft.scans };
      delete scans[action.role];
      // A new scan must never erase the draft, including an intentional blank.
      return { ...draft, scans, scanReport: null };
    }
    case 'scan': {
      const patch = qrValuesForRole(action.template, action.role, action.data);
      const values = { ...draft.values };
      const sources = { ...draft.sources };
      let applied = 0;
      let protectedCount = 0;
      for (const [field, value] of Object.entries(patch)) {
        if (Object.hasOwn(values, field)) {
          if (values[field] !== value) protectedCount++;
          continue;
        }
        values[field] = value;
        sources[field] = 'qr';
        applied++;
      }
      return {
        values,
        sources,
        scans: { ...draft.scans, [action.role]: action.data },
        scanReport: { role: action.role, applied, protected: protectedCount },
      };
    }
  }
}
