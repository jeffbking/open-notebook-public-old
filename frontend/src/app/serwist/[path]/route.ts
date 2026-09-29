import { spawnSync } from 'node:child_process'
import { createSerwistRoute } from '@serwist/turbopack'

// Revision for the precached offline page. Docker builds have no .git, so fall
// back to a random value (a fresh build then always refreshes the entry).
const revision =
  spawnSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf-8' }).stdout?.trim() ||
  crypto.randomUUID()

export const { dynamic, dynamicParams, revalidate, generateStaticParams, GET } = createSerwistRoute({
  additionalPrecacheEntries: [{ url: '/~offline', revision }],
  swSrc: 'src/app/sw.ts',
  useNativeEsbuild: true,
})
