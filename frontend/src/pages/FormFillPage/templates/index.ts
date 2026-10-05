import { birthRegistration } from './birthRegistration';
import type { FormTemplateConfig } from './types';

/** Register another template here after reviewing its field mapping. */
export const formTemplates: readonly FormTemplateConfig[] = [birthRegistration];

export function findTemplateConfig(
  sha256: string | undefined,
  placeholders: readonly string[],
): FormTemplateConfig | null {
  if (!sha256) return null;
  const actual = new Set(placeholders);
  return formTemplates.find((template) =>
    template.templateSha256 === sha256.toLowerCase()
    && template.fields.length === actual.size
    && template.fields.every((field) => actual.has(field.id)),
  ) ?? null;
}

export type { FormFieldConfig, FormTemplateConfig } from './types';
