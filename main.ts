// News-image entry: publish the rendered front page (news.png, beside
// this file) as the grader's /output/entry.png.
//
// The grader runs this program twice in a fresh container with no
// network: /bot is read-only and /output is a writable directory the
// grader mounts for us. We therefore never remove the output directory
// itself — we only clear the files inside it — then copy the image in.

import {
  copyFileSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  rmSync,
  statSync,
} from "node:fs";
import { createHash } from "node:crypto";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const src = join(here, "news.png");
const dest = join(outDir, "entry.png");

// The gate takes a whole PNG of at most 1 MiB: refuse anything else first.
const PNG_MAGIC = Buffer.from([
  0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
]);
const bytes = readFileSync(src);
if (!bytes.subarray(0, 8).equals(PNG_MAGIC)) {
  throw new Error("news.png is not a PNG (bad magic bytes)");
}
if (statSync(src).size > 1024 * 1024) {
  throw new Error("news.png is over the 1 MiB cap");
}

// The gate also caps the image at 1024 by 1024 pixels: read the size
// straight out of the PNG IHDR chunk (bytes 16-23, big-endian) and
// refuse anything larger before we touch the output directory.
const width = bytes.readUInt32BE(16);
const height = bytes.readUInt32BE(20);
if (width > 1024 || height > 1024) {
  throw new Error(`news.png is ${width}x${height}, over the 1024x1024 cap`);
}

// Make the output directory if it is missing, then empty only its
// contents (the directory itself may be a bind mount, so it must stay).
mkdirSync(outDir, { recursive: true });
for (const name of readdirSync(outDir)) {
  rmSync(join(outDir, name), { recursive: true, force: true });
}

copyFileSync(src, dest);

// Confirm the copy landed intact: the published file must hash exactly
// like the source, so a partial or corrupted write fails loudly instead
// of silently entering a broken image.
const digest = (buf) => createHash("sha256").update(buf).digest("hex");
if (digest(readFileSync(dest)) !== digest(bytes)) {
  throw new Error("entry.png does not match news.png after copy");
}
console.log(`wrote entry.png (${bytes.length} bytes, 1024x1024 PNG)`);
