/**
 * useLocalStorage Hook
 * Sync state with localStorage
 */

import { useState, useEffect } from 'react';
import { getStorageItem, setStorageItem } from '@/utils';

export const useLocalStorage = <T>(key: string, initialValue: T): [T, (value: T) => void] => {
  // Get initial value from localStorage
  const [storedValue, setStoredValue] = useState<T>(() => {
    return getStorageItem(key, initialValue);
  });

  // Update localStorage when value changes
  useEffect(() => {
    setStorageItem(key, storedValue);
  }, [key, storedValue]);

  return [storedValue, setStoredValue];
};
