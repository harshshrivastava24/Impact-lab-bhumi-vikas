import type { z } from 'zod';
import {
  CitationSchema,
  ErrorBodySchema,
  LookupResponseSchema,
  ParseResponseSchema,
  PlanCheckResponseSchema,
  type Citation,
  type LookupRequest,
  type LookupResponse,
  type ParseResponse,
  type PlanCheckRequest,
  type PlanCheckResponse,
} from './schemas';

/** Error kinds the UI distinguishes when rendering the error card. */
export type ApiErrorKind = 'network' | 'http' | 'schema';

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status: number | undefined;

  constructor(kind: ApiErrorKind, message: string, status?: number) {
    super(message);
    this.name = 'ApiError';
    this.kind = kind;
    this.status = status;
  }
}

async function request<S extends z.ZodType>(
  path: string,
  schema: S,
  init?: RequestInit,
): Promise<z.infer<S>> {
  let res: Response;
  try {
    res = await fetch(path, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    });
  } catch (err) {
    throw new ApiError('network', err instanceof Error ? err.message : String(err));
  }

  let body: unknown;
  try {
    body = await res.json();
  } catch {
    throw new ApiError('schema', `Response from ${path} was not JSON`, res.status);
  }

  if (!res.ok) {
    const parsedErr = ErrorBodySchema.safeParse(body);
    throw new ApiError('http', parsedErr.success ? parsedErr.data.detail : `HTTP ${res.status}`, res.status);
  }

  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    throw new ApiError('schema', parsed.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`).join('; '));
  }
  return parsed.data;
}

const post = (body: unknown): RequestInit => ({ method: 'POST', body: JSON.stringify(body) });

export const api = {
  parse(text: string): Promise<ParseResponse> {
    return request('/api/parse', ParseResponseSchema, post({ text }));
  },
  lookup(req: LookupRequest): Promise<LookupResponse> {
    return request('/api/lookup', LookupResponseSchema, post(req));
  },
  planCheck(req: PlanCheckRequest): Promise<PlanCheckResponse> {
    return request('/api/plan-check', PlanCheckResponseSchema, post(req));
  },
  getRule(rule: string): Promise<Citation> {
    return request(`/api/rules/${encodeURIComponent(rule)}`, CitationSchema);
  },
};

export function pdfUrl(lang: 'en' | 'hi', page: number): string {
  return `/pdf/${lang}#page=${page}`;
}
