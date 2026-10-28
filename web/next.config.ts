import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Self-contained server in .next/standalone, used by the production Docker image.
  output: "standalone",
  experimental: {
    // src/proxy.ts runs on every /api call, and Next.js keeps only this much of a request body
    // while it does (10 MB by default, silently truncating the rest). Keep it above the API's
    // MAX_UPLOAD_MB.
    proxyClientMaxBodySize: "30mb",
  },
  cacheComponents: true,
  partialPrefetching: true,
  reactCompiler: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
