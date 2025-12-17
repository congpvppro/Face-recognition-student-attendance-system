import { writable } from "svelte/store";

export interface Toast {
  message: string;
  type: "success" | "error";
}

export const toastStore = writable<Toast | null>(null);
let timeoutId: ReturnType<typeof setTimeout> | null = null;

// Overloads: accept a message string, a Toast object, or a partial Toast
export function showToast(message: string, duration?: number): () => void;
export function showToast(toast: Partial<Toast>, duration?: number): () => void;
export function showToast(toastOrMessage: any, duration = 5000) {
  // Normalize input into a full Toast object
  const toast: Toast =
    typeof toastOrMessage === "string"
      ? { message: toastOrMessage, type: "success" }
      : {
          message: toastOrMessage?.message ?? "",
          type: toastOrMessage?.type ?? "success",
        };

  // Clear any existing timeout to avoid overlapping
  if (timeoutId) {
    clearTimeout(timeoutId);
    timeoutId = null;
  }
  toastStore.set(toast);
  // Auto-hide after specified duration
  timeoutId = setTimeout(() => {
    toastStore.set(null);
    timeoutId = null;
  }, duration);
  // return a function to manually clear the toast and timeout
  return () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
    toastStore.set(null);
  };
}

export function hideToast() {
  if (timeoutId) {
    clearTimeout(timeoutId);
    timeoutId = null;
  }
  toastStore.set(null);
}
