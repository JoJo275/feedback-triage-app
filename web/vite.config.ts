import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const ROOT_DIR = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
    plugins: [react()],
    build: {
        outDir: path.resolve(ROOT_DIR, "../src/feedback_triage/static/app"),
        emptyOutDir: true,
        manifest: true,
    },
    test: {
        environment: "jsdom",
        setupFiles: "./src/test/setup.ts",
    },
});
