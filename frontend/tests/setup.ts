import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterAll, afterEach, beforeAll } from 'vitest';
import { mockConfig } from '../src/mocks/handlers';
import { server } from '../src/mocks/server';

// Browsers resolve '/api/...' against the page; Node's fetch does not.
const nativeFetch = globalThis.fetch;
globalThis.fetch = (input: RequestInfo | URL, init?: RequestInit) =>
  nativeFetch(typeof input === 'string' && input.startsWith('/') ? new URL(input, window.location.origin) : input, init);

beforeAll(() => {
  mockConfig.delayMs = 0;
  server.listen({ onUnhandledRequest: 'error' });
});
afterEach(() => {
  cleanup();
  server.resetHandlers();
});
afterAll(() => server.close());
