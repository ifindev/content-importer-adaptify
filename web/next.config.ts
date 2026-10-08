import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Minimal server.js plus only the node_modules it needs, for the Docker image.
  output: "standalone",
  experimental: {
    serverActions: {
      // UploadPanel caps files at 30 MB; the extra 1 MB covers multipart overhead.
      // Both hosts stop bodies over 32 MB before Next: Cloud Run (HTTP/1) and
      // nginx on the VPS (infra/app/nginx).
      bodySizeLimit: "31mb",
    },
  },
  async headers() {
    return [
      {
        // Clicking a live-page link from the review reader must not leak the
        // token in the Referer header to the client's own site.
        source: "/review/:path*",
        headers: [{ key: "Referrer-Policy", value: "no-referrer" }],
      },
    ];
  },
};

export default nextConfig;
