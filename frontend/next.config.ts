import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  reactStrictMode: true,
  eslint: {
    ignoreDuringBuilds: true,
  },
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/api/:path*`,
      },
    ]
  },
  webpack: (config, { dev, isServer }) => {
    // Enable polling in development mode
    if (dev && !isServer) {
      config.watchOptions = {
        poll: 1000,      // Check for changes every second
        aggregateTimeout: 300,   // Delay before rebuilding
      };
    }
    return config;
  },
}

export default nextConfig