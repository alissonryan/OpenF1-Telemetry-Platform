export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly detail?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type QueryValue =
  | string
  | number
  | boolean
  | null
  | undefined
  | Array<string | number | boolean>;

export function buildUrl(
  path: string,
  params?: Record<string, QueryValue>
): string {
  const searchParams = new URLSearchParams();

  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return;
    }

    if (Array.isArray(value)) {
      value.forEach((item) => {
        searchParams.append(key, String(item));
      });
      return;
    }

    searchParams.append(key, String(value));
  });

  const query = searchParams.toString();
  return `${API_BASE}${path}${query ? `?${query}` : ''}`;
}

async function getResponseDetail(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    return response.statusText;
  }

  try {
    return await response.json();
  } catch {
    return response.statusText;
  }
}

export async function apiFetch<T>(
  path: string,
  options?: {
    params?: Record<string, QueryValue>;
    init?: RequestInit;
  }
): Promise<T> {
  const response = await fetch(buildUrl(path, options?.params), {
    ...options?.init,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.init?.headers || {}),
    },
  });

  if (!response.ok) {
    const detail = await getResponseDetail(response);
    const message =
      typeof detail === 'string'
        ? detail
        : typeof (detail as { detail?: unknown })?.detail === 'string'
          ? String((detail as { detail: unknown }).detail)
          : `HTTP ${response.status}`;
    throw new ApiError(message, response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
