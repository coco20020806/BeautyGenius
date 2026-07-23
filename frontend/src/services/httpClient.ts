export class HttpError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
    readonly requestId?: string,
  ) {
    super(message);
    this.name = 'HttpError';
  }
}

type ErrorBody = {
  code?: string;
  message?: string;
  requestId?: string;
  details?: unknown;
};

const DEFAULT_TIMEOUT_MS = 120_000;
const VIP_CODE_STORAGE_KEY = 'makeupVipCode';
const VIP_HEADER = 'X-Vip-Code';

function apiBase(): string {
  const raw = import.meta.env.VITE_API_BASE_URL;
  if (raw === undefined || raw === '') return '';
  return raw.replace(/\/$/, '');
}

export function readVipCode(): string {
  try {
    return sessionStorage.getItem(VIP_CODE_STORAGE_KEY)?.trim() ?? '';
  } catch {
    return '';
  }
}

export function writeVipCode(code: string) {
  try {
    const trimmed = code.trim();
    if (trimmed) sessionStorage.setItem(VIP_CODE_STORAGE_KEY, trimmed);
    else sessionStorage.removeItem(VIP_CODE_STORAGE_KEY);
  } catch {
    /* ignore */
  }
}

function withVipHeaders(headers?: HeadersInit): Headers {
  const merged = new Headers(headers ?? undefined);
  if (!merged.has('Accept')) merged.set('Accept', 'application/json');
  const vip = readVipCode();
  if (vip) merged.set(VIP_HEADER, vip);
  return merged;
}

async function parseError(response: Response): Promise<HttpError> {
  let body: ErrorBody = {};
  try {
    body = (await response.json()) as ErrorBody;
  } catch {
    /* ignore */
  }
  const message = body.message || response.statusText || '请求失败';
  return new HttpError(message, response.status, body.code, body.requestId);
}

export async function requestJson<T>(
  path: string,
  init: RequestInit & { timeoutMs?: number } = {},
): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, ...fetchInit } = init;
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${apiBase()}${path}`, {
      ...fetchInit,
      signal: controller.signal,
      headers: withVipHeaders(fetchInit.headers),
    });
    if (!response.ok) throw await parseError(response);
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('请求超时，请稍后重试', { cause: error });
    }
    throw error;
  } finally {
    window.clearTimeout(timer);
  }
}

export async function requestMultipart<T>(path: string, formData: FormData): Promise<T> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  try {
    const headers = withVipHeaders();
    headers.delete('Content-Type');
    const response = await fetch(`${apiBase()}${path}`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
      headers,
    });
    if (!response.ok) throw await parseError(response);
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('上传超时，请稍后重试', { cause: error });
    }
    throw error;
  } finally {
    window.clearTimeout(timer);
  }
}

export function delay(ms: number) {
  return new Promise<void>((resolve) => {
    window.setTimeout(resolve, ms);
  });
}
