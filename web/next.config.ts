import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Intentionally minimal. The app is a static-leaning demo surface; later
  // tracks (C1/C2) add codegen and artifact ingestion, not runtime config.
  reactStrictMode: true,
};

export default nextConfig;
