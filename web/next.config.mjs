/** @type {import('next').NextConfig} */
const nextConfig = {
  // El navegador solo habla con el origen Next; la API se alcanza por rewrite
  // (mismo origen → cookie SameSite=Lax válida, sin CORS).
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.API_URL || "http://localhost:8001"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
