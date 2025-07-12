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
        // Disable filename hashing for consistent builds
        entryFileNames: "assets/[name].js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: "assets/[name].[ext]",
      },
    },
  },
});
