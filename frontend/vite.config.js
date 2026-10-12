import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Forward /api to FastAPI in `npm run dev` and `npm run preview`.
const apiProxy = {
  "/api": { target: process.env.API_PROXY_TARGET || "http://localhost:8000", changeOrigin: true },
};

export default defineConfig({
  plugins: [react()],
  server: { port: 3000, proxy: apiProxy },
  preview: { port: 4173, proxy: apiProxy },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
