// Compiles installer/BazzarTerminal.nsi with makensis.
// This is a wine-free alternative to electron-builder's NSIS target. Run after
// release/win-unpacked has been produced (for example with:
// electron-builder --win --x64 --dir -c.win.signAndEditExecutable=false).
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const projectDir = path.resolve(__dirname, '..');
const pkg = require('../package.json');

const productName = pkg.build?.productName || pkg.productName || pkg.name;
const version = pkg.version;
const sourceDir = path.join(projectDir, 'release', 'win-unpacked');
const outFile = path.join(projectDir, 'release', `${productName} Setup ${version}.exe`);

function commandExists(command, args = ['--version']) {
  const result = spawnSync(command, args, { stdio: 'ignore' });
  return !result.error && result.status === 0;
}

function findMakensis() {
  if (process.env.MAKENSIS && fs.existsSync(process.env.MAKENSIS)) {
    return process.env.MAKENSIS;
  }

  if (commandExists('makensis', ['-VERSION'])) return 'makensis';

  const candidates = [];
  if (process.platform === 'win32') {
    candidates.push(
      'C\\Program Files (x86)\\NSIS\\makensis.exe',
      'C\\Program Files\\NSIS\\makensis.exe',
      'C\\Program Files (x86)\\NSIS\\Bin\\makensis.exe',
      'C\\Program Files\\NSIS\\Bin\\makensis.exe'
    );
  } else {
    const home = process.env.HOME || '';
    candidates.push(
      path.join(home, '.cache', 'electron-builder', 'nsis', 'nsis-3.0.4.1', 'linux', 'makensis'),
      '/usr/bin/makensis',
      '/usr/local/bin/makensis'
    );
  }

  return candidates.find((candidate) => fs.existsSync(candidate));
}

function nsisRootFor(makensisPath) {
  const parent = path.dirname(makensisPath);
  const leaf = path.basename(parent).toLowerCase();
  // electron-builder stores makensis under <NSISDIR>/linux or <NSISDIR>/Bin.
  if (leaf === 'linux' || leaf === 'mac' || leaf === 'bin') {
    return path.dirname(parent);
  }
  return parent;
}

if (!fs.existsSync(path.join(sourceDir, `${productName}.exe`))) {
  console.error(`Missing ${sourceDir}. Build it first, for example:`);
  console.error('  npm run build && npm run prepare:payload');
  console.error('  npx electron-builder --win --x64 --dir -c.win.signAndEditExecutable=false');
  process.exit(1);
}

const makensis = findMakensis();
if (!makensis) {
  console.error('makensis was not found. Install NSIS or set MAKENSIS=/path/to/makensis.');
  process.exit(1);
}

fs.mkdirSync(path.join(projectDir, 'release'), { recursive: true });

const optionPrefix = process.platform === 'win32' ? '/' : '-';
const args = [
  `${optionPrefix}V2`,
  `${optionPrefix}DAPP_NAME=${productName}`,
  `${optionPrefix}DAPP_VERSION=${version}`,
  `${optionPrefix}DAPP_EXE=${productName}.exe`,
  `${optionPrefix}DSOURCE_DIR=${sourceDir}`,
  `${optionPrefix}DOUT_FILE=${outFile}`,
  path.join('installer', 'BazzarTerminal.nsi'),
];

const result = spawnSync(makensis, args, {
  cwd: projectDir,
  stdio: 'inherit',
  env: {
    ...process.env,
    NSISDIR: process.env.NSISDIR || nsisRootFor(makensis),
  },
});

if (result.error) {
  console.error(result.error);
  process.exit(1);
}
process.exit(result.status ?? 1);
