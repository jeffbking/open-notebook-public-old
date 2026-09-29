import type { MetadataRoute } from 'next'

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: '/',
    name: 'Open Notebook',
    short_name: 'Notebook',
    description: 'Privacy-focused research and knowledge management',
    start_url: '/notebooks',
    scope: '/',
    display: 'standalone',
    orientation: 'any',
    background_color: '#f5f5f2',
    theme_color: '#eeeee9',
    categories: ['productivity', 'education'],
    icons: [
      { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
      { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
      { src: '/icons/maskable-192.png', sizes: '192x192', type: 'image/png', purpose: 'maskable' },
      { src: '/icons/maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
    ],
    shortcuts: [
      { name: 'Notebooks', url: '/notebooks', icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }] },
      { name: 'Ask and Search', url: '/search', icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }] },
      { name: 'Podcasts', url: '/podcasts', icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }] },
    ],
  }
}
