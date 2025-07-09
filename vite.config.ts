import { defineConfig } from "vite";
import monacoEditorEsmPlugin from "vite-plugin-monaco-editor-esm";

export default defineConfig({
  base: "./",
  plugins: [monacoEditorEsmPlugin()],
  server: {
    cors: true,
  },
});
