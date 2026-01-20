/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: '/api',
        destination: 'http://localhost:8000/api',
      },
    ]
  },
}

export default nextConfig
