import { clearSession, getAccessToken } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type ApiError = {
  success: false;
  error: {
    code: string;
    message_key: string;
    details: unknown;
  };
};

export type ApiSuccess<T> = {
  success: true;
  data: T;
  meta?: {
    page: number;
    page_size: number;
    total: number;
  };
};

export class ApiClientError extends Error {
  code: string;
  message_key: string;
  details: unknown;

  constructor(code: string, message_key: string, details: unknown) {
    super(message_key);
    this.code = code;
    this.message_key = message_key;
    this.details = details;
  }
}

const PUBLIC_AUTH_PATHS = ["/auth/login/", "/auth/refresh/", "/auth/forgot-password/"];

async function request<T>(path: string, init: RequestInit = {}): Promise<ApiSuccess<T>> {
  const isFormData = typeof FormData !== "undefined" && init.body instanceof FormData;
  const headers = new Headers(init.headers);
  if (!isFormData) {
    headers.set("Content-Type", "application/json");
  }
  const skipAuth = PUBLIC_AUTH_PATHS.some((item) => path.startsWith(item));
  const token = typeof window !== "undefined" && !skipAuth ? getAccessToken() : null;
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers,
    });
  } catch {
    throw new ApiClientError("NETWORK", "errors.network", {});
  }
  const payload = (await response.json()) as ApiSuccess<T> | ApiError;
  if (!response.ok || !payload.success) {
    const error =
      "error" in payload
        ? payload.error
        : { code: "ERROR", message_key: "errors.generic", details: {} };
    if (error.code === "TOKEN_NOT_VALID" || error.message_key === "errors.auth.token_not_valid") {
      clearSession();
    }
    throw new ApiClientError(error.code, error.message_key, error.details);
  }
  return payload;
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const payload = await request<T>(path, init);
  return payload.data;
}

export async function apiFetchPage<T>(
  path: string,
  init: RequestInit = {},
): Promise<{ data: T[]; meta: { page: number; page_size: number; total: number } }> {
  const payload = await request<T[]>(path, init);
  return {
    data: payload.data,
    meta: payload.meta ?? { page: 1, page_size: payload.data.length, total: payload.data.length },
  };
}

export async function apiDownload(path: string, fileName: string): Promise<void> {
  const headers = new Headers();
  const token = typeof window !== "undefined" ? getAccessToken() : null;
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { headers });
  } catch {
    throw new ApiClientError("NETWORK", "errors.network", {});
  }
  if (!response.ok) {
    let message_key = "errors.generic";
    try {
      const payload = (await response.json()) as ApiError;
      message_key = payload.error?.message_key ?? message_key;
    } catch {
      /* binary or empty error body */
    }
    throw new ApiClientError("ERROR", message_key, {});
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = window.document.createElement("a");
  link.href = url;
  link.download = fileName;
  window.document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
