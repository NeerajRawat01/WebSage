import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Hide the bottom-left Next.js dev popup (Route/Preferences) in development
  devIndicators: {
    appIsrStatus: false,
    buildActivity: false,
  },
};

export default nextConfig;
