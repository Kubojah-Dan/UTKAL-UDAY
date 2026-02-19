import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  ssr: {
    noExternal: ["pouchdb-core", "pouchdb-adapter-idb"],
  },

  resolve: {
    alias: {
      "spark-md5": "spark-md5/spark-md5.js",
      "vuvuzela": "vuvuzela/index.js",
      "events": "events",
    },
  },

  optimizeDeps: {
    exclude: ["pouchdb-core", "pouchdb-adapter-idb"],
  },

  build: {
    commonjsOptions: {
      include: [/spark-md5/, /vuvuzela/, /pouchdb/, /node_modules/],
    },
  },

  server: {
    host: true,
    port: 5173,
  },
});
