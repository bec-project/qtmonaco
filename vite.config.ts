import { defineConfig } from "vite";
import monacoEditorEsmPlugin from "vite-plugin-monaco-editor-esm";

export default defineConfig({
  base: "./",
  plugins: [monacoEditorEsmPlugin()],
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
          if (
            id.includes("monaco-languageclient") ||
            id.includes("vscode-jsonrpc") ||
            id.includes("vscode-ws-jsonrpc")
          ) {
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
