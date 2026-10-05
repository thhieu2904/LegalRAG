import type { CCCDData } from '../types';

export type QrSource = keyof CCCDData | 'identity_document';

export interface FormFieldConfig {
  id: string;
  label: string;
  group: string;
  roleId?: string;
  qrSource?: QrSource;
  hint?: string;
}

export interface FormTemplateConfig {
  id: string;
  name: string;
  /** Bind the mapping to the exact Word file, not a filename or field count. */
  templateSha256: string;
  roles: readonly { id: string; label: string }[];
  fields: readonly FormFieldConfig[];
}
