/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // RTL support
  i18n: {
    locales: ['he', 'en'],
    defaultLocale: 'he',
  },
}

module.exports = nextConfig

