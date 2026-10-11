import { createReadStream, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig, loadEnv, type Plugin } from 'vite';

const repoRoot = resolve(__dirname, '..');

const PDF_FILES: Record<string, string> = {
  en: 'MP_Bhumi_Vikas_Rules_2012_upto_2025-03-06_EN.pdf',
  hi: 'MP_Bhumi_Vikas_Rules_2012_upto_2025-03-06_HI.pdf',
};

/**
 * In mock mode there is no backend, so serve the official PDFs from
 * ../resources at /pdf/en and /pdf/hi, matching the backend contract.
 */
function serveRulePdfs(): Plugin {
  return {
    name: 'serve-rule-pdfs',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const match = /^\/pdf\/(en|hi)(?:[?#].*)?$/.exec(req.url ?? '');
        const file = match?.[1] ? PDF_FILES[match[1]] : undefined;
        if (!file) return next();
        const path = resolve(repoRoot, 'resources', file);
        if (!existsSync(path)) {
          res.statusCode = 404;
          res.end('PDF not found');
          return;
        }
        res.setHeader('Content-Type', 'application/pdf');
        createReadStream(path).pipe(res);
      });
    },
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const useMock = env.VITE_USE_MOCK === 'true' || process.env.VITE_USE_MOCK === 'true';
  const backend = env.BVS_BACKEND_URL ?? 'http://127.0.0.1:8000';

  return {
    plugins: [react(), tailwindcss(), ...(useMock ? [serveRulePdfs()] : [])],
    server: {
      port: 5173,
      strictPort: true,
      fs: { allow: [repoRoot] },
      proxy: useMock
        ? undefined
        : {
            '/api': backend,
            '/pdf': backend,
          },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
    },
  };
});
