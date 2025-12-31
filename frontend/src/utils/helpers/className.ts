/**
 * ClassName Helper Utility
 */

import clsx, { type ClassValue } from 'clsx';

/**
 * Merge classNames conditionally
 * @param classes - ClassNames to merge
 */
export const cn = (...classes: ClassValue[]): string => {
  return clsx(classes);
};
