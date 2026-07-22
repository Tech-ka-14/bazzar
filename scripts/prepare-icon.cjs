// Decodes installer/icon.base64 into build/icon.ico for electron-builder.
// Keeping the icon as base64 text lets the complete packaging source be pushed
// through text-based GitHub tooling without corrupting a binary ICO file.
const fs = require('fs');
const path = require('path');

const projectDir = path.resolve(__dirname, '..');
const source = path.join(projectDir, 'installer', 'icon.base64');
const target = path.join(projectDir, 'build', 'icon.ico');

const encoded = fs.readFileSync(source, 'utf8').replace(/\s+/g, '');
if (!encoded) throw new Error('installer/icon.base64 is empty');

fs.mkdirSync(path.dirname(target), { recursive: true });
fs.writeFileSync(target, Buffer.from(encoded, 'base64'));
console.log(`Icon prepared at ${path.relative(projectDir, target)}`);
