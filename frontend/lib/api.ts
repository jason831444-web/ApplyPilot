const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  token?: string | null;
};

export function getApiErrorMessage(data: unknown, fallback: string): string {
  if (typeof data === "string") {
    return data || fallback;
  }

  if (typeof data === "object" && data !== null && "detail" in data) {
    const detail = (data as { detail?: unknown }).detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (typeof item === "string") {
            return item;
          }
          if (typeof item === "object" && item !== null && "msg" in item) {
            return String((item as { msg?: unknown }).msg);
          }
          return safeStringify(item, fallback);
        })
        .join(", ");
    }

    if (detail !== undefined) {
      return safeStringify(detail, fallback);
    }
  }

  return safeStringify(data, fallback);
}

function safeStringify(data: unknown, fallback: string): string {
  try {
    const value = JSON.stringify(data);
    return value && value !== "{}" ? value : fallback;
  } catch {
    return fallback;
  }
}

function isJsonResponse(response: Response): boolean {
  return response.headers.get("content-type")?.includes("application/json") ?? false;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${normalizeApiBaseUrl(API_BASE_URL)}${normalizeApiPath(path)}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
      ...(options.headers ?? {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const fallback = `API request failed with status ${response.status}`;
    let payload: unknown;
    try {
      payload = isJsonResponse(response) ? await response.json() : await response.text();
    } catch {
      throw new Error(fallback);
    }
    throw new Error(getApiErrorMessage(payload, fallback));
  }

  return response.json() as Promise<T>;
}

function normalizeApiBaseUrl(value: string): string {
  return value.replace(/\/+$/, "");
}

function normalizeApiPath(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  if (normalizeApiBaseUrl(API_BASE_URL).endsWith("/api") && normalizedPath.startsWith("/api/")) {
    return normalizedPath.slice(4);
  }
  return normalizedPath;
}

export { API_BASE_URL };
