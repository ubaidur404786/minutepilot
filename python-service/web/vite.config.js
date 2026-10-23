import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// `npm run build` writes the page into ../app/ui, which the Python service serves at "/".
// `npm run dev` serves it on :5173 and sends API calls to the running Python service on :8000.
export default defineConfig({
  plugins: [react()],
  build: { outDir: "../app/ui", emptyOutDir: true },
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:8000", "/health": "http://localhost:8000" },
  },
});
