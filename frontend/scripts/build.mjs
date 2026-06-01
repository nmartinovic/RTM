import { copyFile, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const dist = join(root, 'dist');
const assetDir = join(dist, 'assets');

await rm(dist, { recursive: true, force: true });
await mkdir(assetDir, { recursive: true });

const apiBaseUrl = process.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
let appJs = await readFile(join(root, 'build/assets/main.js'), 'utf8');
appJs = appJs.replace("import { apiBaseUrl } from './config';", '');
let configJs = await readFile(join(root, 'build/assets/config.js'), 'utf8');
configJs = configJs.replace(
  "import.meta.env?.VITE_API_BASE_URL ?? 'http://localhost:8000'",
  JSON.stringify(apiBaseUrl),
);
await writeFile(join(assetDir, 'app.js'), `${configJs}\n${appJs}`);
await copyFile(join(root, 'src/styles.css'), join(assetDir, 'styles.css'));

const html = await readFile(join(root, 'index.html'), 'utf8');
await writeFile(
  join(dist, 'index.html'),
  html
    .replace('<script type="module" src="/src/main.tsx"></script>', '<script type="module" src="./assets/app.js"></script>')
    .replace('<script type="module" src="/src/main.ts"></script>', '<script type="module" src="./assets/app.js"></script>')
    .replace('</head>', '    <link rel="stylesheet" href="./assets/styles.css" />\n  </head>'),
);
