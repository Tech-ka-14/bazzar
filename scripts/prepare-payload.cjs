// Stages the original repository source payload into build/repository/ so
// electron-builder can install it under resources/repository via
// extraResources.
//
// NOTE: extraResources "from" must NOT be the project root. electron-builder
// applies the parsed extraResources patterns as exclude patterns to the main
// app file matcher when "from" equals the app directory, which silently drops
// app files (electron/, package.json) from app.asar. Staging under build/
// avoids this (build/ is already excluded from the app matcher).
//
// Excludes: .git, node_modules, dist, release, build.
// Includes: Python modules, Go sources, JSX sources, SPEC.md,
// requirements.txt, go.mod, docs, and the app sources/manifests.
const fs = require('fs');
const path = require('path');

const projectDir = path.resolve(__dirname, '..');
const payloadDir = path.join(projectDir, 'build', 'repository');

const EXCLUDED = new Set(['.git', 'node_modules', 'dist', 'release', 'build']);

fs.rmSync(payloadDir, { recursive: true, force: true });
fs.mkdirSync(payloadDir, { recursive: true });

let fileCount = 0;

function copyRecursive(src, dest) {
  const stat = fs.statSync(src);
  if (stat.isDirectory()) {
    fs.mkdirSync(dest, { recursive: true });
    for (const entry of fs.readdirSync(src)) {
      copyRecursive(path.join(src, entry), path.join(dest, entry));
    }
  } else if (stat.isFile()) {
    fs.copyFileSync(src, dest);
    fileCount += 1;
  }
}

for (const entry of fs.readdirSync(projectDir)) {
  if (EXCLUDED.has(entry)) continue;
  copyRecursive(path.join(projectDir, entry), path.join(payloadDir, entry));
}

console.log(`Repository payload staged at ${path.relative(projectDir, payloadDir)} (${fileCount} files)`);
