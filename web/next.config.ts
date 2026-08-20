import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // C2: the engagement data is imported straight from the repo's
  // artifacts/demo-engagement/ (via the @artifacts/* tsconfig path) — the
  // drift-tested originals, never vendored copies. Point file tracing at the
  // repo root so Next resolves across the package boundary.
  outputFileTracingRoot: path.join(__dirname, ".."),
  reactStrictMode: true,
};

export default nextConfig;
