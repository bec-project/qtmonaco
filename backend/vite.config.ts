import { defineConfig } from "vite";
import monacoEditorEsmPlugin from "vite-plugin-monaco-editor-esm";

export default defineConfig({
  base: "./",
  plugins: [
    monacoEditorEsmPlugin({
      languageWorkers: [],
      customWorkers: [
        {
          label: "editorWorkerService",
          entry: "monaco-editor/esm/vs/editor/editor.worker.js",
        },
        {
          label: "css",
          entry: "monaco-editor/esm/vs/language/css/css.worker.js",
        },
        {
          label: "html",
          entry: "monaco-editor/esm/vs/language/html/html.worker.js",
        },
        {
          label: "json",
          entry: "monaco-editor/esm/vs/language/json/json.worker.js",
        },
        {
          label: "typescript",
          entry: "monaco-editor/esm/vs/language/typescript/ts.worker.js",
        },
      ],
    }),
  ],
  server: {
    cors: true,
  },
  build: {
    rollupOptions: {
      output: {
        // Ensure consistent file naming without hashes
        entryFileNames: "assets/[name].js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: "assets/[name].[ext]",
        // Explicit manual chunking for consistency
        manualChunks: (id) => {
          if (id.includes("vscode-jsonrpc") || id.includes("vscode-ws-jsonrpc")) {
            return "vendor";
          }
          if (id.includes("monaco-editor")) {
            return "monaco-core";
          }
        },
      },
    },
  },
});
