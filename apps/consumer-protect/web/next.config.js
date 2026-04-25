/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    // onnxruntime-node uses native bindings — keep it server-side only
    serverComponentsExternalPackages: ["onnxruntime-node"],
  },
};

module.exports = nextConfig;
