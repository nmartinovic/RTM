import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const publicRoot = process.argv[2] === 'dist' ? join(root, 'dist') : root;
const port = Number(process.env.PORT ?? 5173);
const contentTypes = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'],
  ['.css', 'text/css; charset=utf-8'],
  ['.ts', 'text/typescript; charset=utf-8'],
]);

createServer(async (request, response) => {
  const url = new URL(request.url ?? '/', `http://${request.headers.host}`);
  const path = normalize(url.pathname === '/' ? '/index.html' : url.pathname);
  const filePath = join(publicRoot, path);

  try {
    let body = await readFile(filePath, 'utf8');
    if (path.endsWith('index.html') && publicRoot === root) {
      body = body
        .replace('/src/main.tsx', '/src/main.ts')
        .replace('</head>', '    <link rel="stylesheet" href="/src/styles.css" />\n  </head>');
    }
    response.writeHead(200, { 'content-type': contentTypes.get(extname(filePath)) ?? 'text/plain' });
    response.end(body);
  } catch {
    response.writeHead(404, { 'content-type': 'text/plain' });
    response.end('Not found');
  }
}).listen(port, () => {
  console.log(`Dashboard available at http://localhost:${port}`);
});
