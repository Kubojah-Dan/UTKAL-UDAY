import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";

import { VitePWA } from "vite-plugin-pwa";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.ico", "apple-touch-icon.png", "masked-icon.svg"],
      manifest: {
        name: "Utkal Uday",
        short_name: "UtkalUday",
        description: "An offline-first learning platform for rural India",
        theme_color: "#0f766e",
        icons: [
          {
            src: "pwa-192x192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "pwa-512x512.png",
            sizes: "512x512",
            type: "image/png",
          },
          {
            src: "pwa-512x512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any maskable",
          },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,ico,png,svg}"],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: "CacheFirst",
            options: {
              cacheName: "google-fonts-cache",
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
              },
              cacheableResponse: {
                statuses: [0, 200],
              },
            },
          },
          {
            urlPattern:
              /\/(?:questions(?:\/|$)|student\/questions\/download(?:\?|$)|student\/streak(?:\/|$)|student\/daily-challenge(?:\?|$)|leaderboard(?:\?|$)|bkt\/latest(?:\?|$))/i,
            handler: "NetworkFirst",
            options: {
              cacheName: "stable-api-cache",
              networkTimeoutSeconds: 5,
              expiration: {
                maxEntries: 300,
                maxAgeSeconds: 60 * 60 * 24 * 7,
              },
              cacheableResponse: {
                statuses: [0, 200],
              },
            },
          },
          {
            urlPattern:
              /\/(?:quests\/next(?:\/|$)|recommend(?:\/|$)|tools\/notifications(?:\/|$)|student\/spaced-review(?:\/|$))/i,
            handler: "NetworkOnly",
          },
        ],
      },
    }),
  ],

  ssr: {
    noExternal: ["pouchdb-core", "pouchdb-adapter-idb"],
  },

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
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
