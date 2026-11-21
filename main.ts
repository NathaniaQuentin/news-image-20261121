// News-image round 4: publish the pre-rendered front page.
//
// news.png sits beside this file in the repository, already drawn.
// This program only copies it into the grader's output directory as
// entry.png. Nothing is rendered here: the grader runs with the
// standard library only and no third-party packages are installed,
// so a Python/Pillow render step cannot work there — the copy-only
// shape is the one the competition's own starter uses.
//
// The output directory is a mount the grader provides, so it is never
// removed — only the files inside it are cleared before the copy.

import { copyFileSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const sourcePath = join(here, "news.png");
const destPath = join(outDir, "entry.png");

// The gate accepts one PNG of at most 1 MiB and 1024 by 1024 pixels.
const MAX_BYTES = 1024 * 1024;
const MAX_SIDE = 1024;
const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

const image = readFileSync(sourcePath);

if (image.length < 24 || !image.subarray(0, 8).equals(PNG_SIGNATURE)) {
  throw new Error("news.png is not a PNG file");
}
if (image.length > MAX_BYTES) {
  throw new Error(`news.png is ${image.length} bytes, over the 1 MiB cap`);
}

// The first chunk of a PNG is IHDR; its data starts with the width and
// height as big-endian 32-bit numbers at offsets 16 and 20. Check the
// chunk tag too (bytes 12-15 spell "IHDR"), so a non-PNG file that
// happens to start with the right magic cannot slip past with garbage
// dimensions.
if (image.readUInt32BE(12) !== 0x49484452) {
  throw new Error("news.png has no IHDR chunk where one is expected");
}
const width = image.readUInt32BE(16);
const height = image.readUInt32BE(20);
if (width > MAX_SIDE || height > MAX_SIDE) {
  throw new Error(`news.png is ${width}x${height}, over the 1024x1024 cap`);
}

// Make sure the output directory exists, then empty it without
// deleting it, and place the image there.
mkdirSync(outDir, { recursive: true });
for (const entry of readdirSync(outDir)) {
  rmSync(join(outDir, entry), { recursive: true, force: true });
}
copyFileSync(sourcePath, destPath);

// A broken or partial copy must fail loudly: the published file has to
// be the same size as the source and hash exactly like it before we
// report success.
if (statSync(destPath).size !== image.length) {
  throw new Error("entry.png size does not match news.png after copy");
}
const sha256 = (buf) => createHash("sha256").update(buf).digest("hex");
if (sha256(readFileSync(destPath)) !== sha256(image)) {
  throw new Error("entry.png does not match news.png after copy");
}
console.log(`wrote entry.png (${image.length} bytes, ${width}x${height} PNG)`);
