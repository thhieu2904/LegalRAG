import { useState, useCallback } from "react";
import type { ModalType, ModalState, ModalProps } from "../types/admin";

// ============================================================================
// Modal Hook for State Management
// ============================================================================

export function useModal() {
  const [modalState, setModalState] = useState<ModalState>({
    type: null,
    isOpen: false,
    data: undefined,
    options: {
      size: "md",
      closable: true,
      backdrop: true,
    },
  });

  const openModal = useCallback(
    (type: ModalType, data?: unknown, options?: ModalState["options"]) => {
      setModalState({
        type,
        isOpen: true,
        data,
        options: { ...modalState.options, ...options },
      });
    },
    [modalState.options]
  );

  const closeModal = useCallback(() => {
    setModalState((prev) => ({
      ...prev,
      isOpen: false,
    }));

    // Clear data after animation
    setTimeout(() => {
      setModalState({
        type: null,
        isOpen: false,
        data: undefined,
        options: {
          size: "md",
          closable: true,
          backdrop: true,
        },
      });
    }, 300);
  }, []);

  const updateModalData = useCallback((data: unknown) => {
    setModalState((prev) => ({
      ...prev,
      data,
    }));
  }, []);

  return {
    modalState,
    openModal,
    closeModal,
    updateModalData,
    isOpen: modalState.isOpen,
    modalType: modalState.type,
    modalData: modalState.data,
    modalOptions: modalState.options,
  };
}

// ============================================================================
// Modal Component Props Factory
// ============================================================================

export function createModalProps<T = unknown>(
  isOpen: boolean,
  onClose: () => void,
  onConfirm?: (data: T) => void | Promise<void>,
  data?: T,
  title?: string,
  size?: ModalProps["size"]
): ModalProps<T> {
  return {
    isOpen,
    onClose,
    onConfirm,
    data,
    title,
    size: size || "md",
  };
}

// ============================================================================
// Modal Registry - Map modal types to their configurations
// ============================================================================

export interface ModalConfig {
  title: string;
  size: ModalProps["size"];
  closable: boolean;
  backdrop: boolean;
}

export const MODAL_CONFIGS: Record<ModalType, ModalConfig> = {
  "add-collection": {
    title: "Thêm Collection Mới",
    size: "lg",
    closable: true,
    backdrop: true,
  },
  "edit-collection": {
    title: "Chỉnh Sửa Collection",
    size: "lg",
    closable: true,
    backdrop: true,
  },
  "delete-collection": {
    title: "Xóa Collection",
    size: "sm",
    closable: true,
    backdrop: true,
  },
  "add-document": {
    title: "Tải Lên Văn Bản Mới",
    size: "xl",
    closable: true,
    backdrop: true,
  },
  "edit-document": {
    title: "Chỉnh Sửa Văn Bản",
    size: "xl",
    closable: true,
    backdrop: true,
  },
  "view-document": {
    title: "Chi Tiết Văn Bản",
    size: "xl",
    closable: true,
    backdrop: true,
  },
  "delete-document": {
    title: "Xóa Văn Bản",
    size: "sm",
    closable: true,
    backdrop: true,
  },
  "upload-files": {
    title: "Tải Lên Files",
    size: "lg",
    closable: true,
    backdrop: true,
  },
  "processing-details": {
    title: "Chi Tiết Xử Lý",
    size: "lg",
    closable: true,
    backdrop: true,
  },
  "vector-rebuild": {
    title: "Xây Dựng Lại Vector Database",
    size: "md",
    closable: true,
    backdrop: true,
  },
  "system-config": {
    title: "Cấu Hình Hệ Thống",
    size: "lg",
    closable: true,
    backdrop: true,
  },
  "model-config": {
    title: "Cấu Hình Model",
    size: "lg",
    closable: true,
    backdrop: true,
  },
  "export-data": {
    title: "Xuất Dữ Liệu",
    size: "md",
    closable: true,
    backdrop: true,
  },
  "import-data": {
    title: "Nhập Dữ Liệu",
    size: "lg",
    closable: true,
    backdrop: true,
  },
};

// ============================================================================
// Helper Functions
// ============================================================================

export function getModalConfig(type: ModalType): ModalConfig {
  return MODAL_CONFIGS[type];
}

export function createModalTitle(type: ModalType, data?: unknown): string {
  const config = getModalConfig(type);

  // Customize titles based on data
  switch (type) {
    case "edit-collection":
      return data &&
        typeof data === "object" &&
        data !== null &&
        "displayName" in data
        ? `Chỉnh Sửa "${(data as { displayName: string }).displayName}"`
        : config.title;

    case "delete-collection":
      return data &&
        typeof data === "object" &&
        data !== null &&
        "displayName" in data
        ? `Xóa Collection "${(data as { displayName: string }).displayName}"`
        : config.title;

    case "edit-document":
      return data && typeof data === "object" && data !== null && "name" in data
        ? `Chỉnh Sửa "${(data as { name: string }).name}"`
        : config.title;

    case "view-document":
      return data && typeof data === "object" && data !== null && "name" in data
        ? `Chi Tiết "${(data as { name: string }).name}"`
        : config.title;

    case "delete-document":
      return data && typeof data === "object" && data !== null && "name" in data
        ? `Xóa Văn Bản "${(data as { name: string }).name}"`
        : config.title;

    default:
      return config.title;
  }
}

// ============================================================================
// Modal Size Classes
// ============================================================================

export const MODAL_SIZE_CLASSES = {
  sm: "max-w-md",
  md: "max-w-lg",
  lg: "max-w-2xl",
  xl: "max-w-4xl",
  full: "max-w-7xl",
} as const;

export function getModalSizeClass(size: ModalProps["size"] = "md"): string {
  return MODAL_SIZE_CLASSES[size];
}

// ============================================================================
// Modal Animation Classes
// ============================================================================

export const MODAL_ANIMATION_CLASSES = {
  enter: "transition-all duration-300 ease-out",
  enterFrom: "opacity-0 scale-95 translate-y-4",
  enterTo: "opacity-100 scale-100 translate-y-0",
  leave: "transition-all duration-200 ease-in",
  leaveFrom: "opacity-100 scale-100 translate-y-0",
  leaveTo: "opacity-0 scale-95 translate-y-4",
} as const;

// ============================================================================
// Validation Helpers
// ============================================================================

export function validateModalData<T>(
  type: ModalType,
  data: unknown
): data is T {
  // Add specific validation logic for each modal type
  switch (type) {
    case "add-collection":
    case "edit-collection":
      return typeof data === "object" && data !== null;

    case "add-document":
    case "edit-document":
      return typeof data === "object" && data !== null;

    default:
      return true;
  }
}

// ============================================================================
// Modal Event Handlers
// ============================================================================

export interface ModalHandlers {
  onOpen: (type: ModalType, data?: unknown) => void;
  onClose: () => void;
  onConfirm: (data: unknown) => void | Promise<void>;
  onCancel: () => void;
}

export function createModalHandlers(
  openModal: (
    type: ModalType,
    data?: unknown,
    options?: ModalState["options"]
  ) => void,
  closeModal: () => void,
  onConfirm?: (data: unknown) => void | Promise<void>
): ModalHandlers {
  return {
    onOpen: openModal,
    onClose: closeModal,
    onConfirm: onConfirm || (() => {}),
    onCancel: closeModal,
  };
}
