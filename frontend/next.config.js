/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/api/:path*`,
      },
    ];
  },
  // Handle react-pdf and pdfjs-dist for webpack
  webpack: (config) => {
    // Add canvas alias for pdfjs (not needed in browser)
    config.resolve.alias.canvas = false;

    // Handle pdfjs-dist worker
    config.resolve.alias["pdfjs-dist"] = "pdfjs-dist/legacy/build/pdf";

    return config;
  },
};

module.exports = nextConfig;
