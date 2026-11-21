// Round-3 entry for "Sum up 21 November's world news in one image".
// Node 22, standard library only. It runs render.py (Pillow) beside
// this file, which draws news.png (1024x1024), then copies it to the
// grader's output directory as entry.png — the one file the gate reads.
//
// Round-3 fix: the grader mounts the repository read-only at /bot, so
// rendering into the script's own directory (round 2) failed with
// "OSError: [Errno 30] Read-only file system: '/bot/news.png'" and the
// run exited 1. The renderer now writes to the writable temp directory
// instead; only the final copy goes to $MAKEFUN_OUTPUT_DIR.
//
// Local run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, existsSync, mkdirSync, readFileSync, statSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
// The repo is read-only in the grader, so render into the temp dir.
const rendered = join(tmpdir(), 'news-image-20261121-rendered.png');

// The gate takes a whole PNG of at most 1 MiB and 1024 by 1024 pixels.
const MAX_BYTES = 1_048_576;

function runRenderer() {
  for (const python of ['python3', 'python']) {
    try {
      execFileSync(python, [join(here, 'render.py'), rendered], {
        cwd: here,
        stdio: 'inherit',
      });
      return;
    } catch (err) {
      if (err.code !== 'ENOENT') throw err;
    }
  }
  throw new Error('no python3 or python on PATH to run render.py');
}

function pngSize(path) {
  // PNG signature (8 bytes) + IHDR chunk: width and height are the
  // first two big-endian uint32s of the IHDR data, at offsets 16/20.
  const buf = readFileSync(path);
  if (buf.length < 24 || buf.readUInt32BE(12) !== 0x49484452) {
    throw new Error(`${path} is not a PNG file`);
  }
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
}

runRenderer();

if (!existsSync(rendered)) {
  throw new Error(`render.py did not produce ${rendered}`);
}
const { width, height } = pngSize(rendered);
if (width !== 1024 || height !== 1024) {
  throw new Error(`rendered image is ${width}x${height}, expected 1024x1024`);
}
if (statSync(rendered).size > MAX_BYTES) {
  throw new Error(`rendered image exceeds the 1 MiB gate`);
}

mkdirSync(outDir, { recursive: true });
copyFileSync(rendered, join(outDir, 'entry.png'));
console.log(`wrote ${join(outDir, 'entry.png')} (${width}x${height})`);
