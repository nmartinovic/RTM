import { readFile } from 'node:fs/promises';
import { join } from 'node:path';

const appJs = await readFile(join(import.meta.dirname, '..', 'dist', 'assets', 'app.js'), 'utf8');

const requiredSnippets = [
  'RTM is connected. Run a read-only sync to refresh counts.',
  'Connect RTM before running read-only sync.',
  'Read-only sync completed.',
  'list_count',
  'active_task_count',
  'Sync status',
  'data-action="sync-rtm"',
];

for (const snippet of requiredSnippets) {
  if (!appJs.includes(snippet)) {
    throw new Error(`Missing dashboard behavior snippet: ${snippet}`);
  }
}
