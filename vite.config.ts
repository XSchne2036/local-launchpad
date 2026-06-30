import { defineConfig } from "vite";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import viteReact from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import tsConfigPaths from "vite-tsconfig-paths";

// Standard Vite config for Replit — bypasses @lovable.dev/vite-tanstack-config
// which patches SSR handlers in ways that cause dual-React hydration errors
// outside of the Lovable sandbox environment.
export default defineConfig({
  plugins: [
    tailwindcss(),
    tsConfigPaths({ projects: ["./tsconfig.json"] }),
    tanstackStart({
      server: { entry: "server" },
    }),
    viteReact(),
  ],
  server: {
    allowedHosts: true,
    host: "0.0.0.0",
    port: 5000,
  },
  resolve: {
    dedupe: [
      "react",
      "react-dom",
      "@tanstack/react-start",
      "@tanstack/react-router",
    ],
  },
});
