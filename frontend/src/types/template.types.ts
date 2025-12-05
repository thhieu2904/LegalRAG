/**
 * Type definitions for hybrid form template workflow
 */

export interface DetectedPosition {
  index: number;
  paragraph_index: number;
  text: string;
  pattern_type: 'dots' | 'tab';
  label: string;
  full_paragraph: string;
  context_before: string[];
  context_after: string[];
}

export interface DetectResponse {
  success: boolean;
  total_positions: number;
  positions: DetectedPosition[];
  message: string;
}

export interface FinalizeResponse {
  success: boolean;
  message: string;
  form: {
    id: string;
    form_name: string;
    template_path: string;
    placeholders: string[];
    created_at: string;
  };
}
