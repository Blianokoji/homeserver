#!/bin/sh
set -e

echo "[Patch] Applying TMDB host fix..."
sed -i 's/api.themoviedb.org/api.tmdb.org/g' /app/dist/api/themoviedb/index.js 2>/dev/null || true

echo "[Patch] Installing patched routes for Delete Requested..."
cp /app/config/routes-request.js /app/dist/routes/request.js
cp /app/config/routes-media.js /app/dist/routes/media.js

echo "[Patch] Updating UI buttons to Delete Requested..."
node -e '
const fs = require("fs");
const filesToPatch = [
    "/app/.next/server/chunks/40532.js",
    "/app/.next/server/chunks/6409.js",
    "/app/.next/static/chunks/13216-db46debce08c8d6a.js",
    "/app/.next/static/chunks/6364-fe7f9a6005dd5bf1.js"
];

for (const file of filesToPatch) {
    if (fs.existsSync(file)) {
        let content = fs.readFileSync(file, "utf8");
        let modified = false;
        if (content.includes("deleterequest:\"Delete Request\"")) {
            content = content.replace(/deleterequest:"Delete Request"/g, "deleterequest:\"Delete Requested\"");
            modified = true;
        }
        if (content.includes("deleterequest:\x27Delete Request\x27")) {
            content = content.replace(/deleterequest:\x27Delete Request\x27/g, "deleterequest:\x27Delete Requested\x27");
            modified = true;
        }
        if (modified) {
            fs.writeFileSync(file, content);
            console.log("Patched UI strings in:", file);
        }
    }
}
'

echo "[Patch] Verifying route syntax..."
node -c /app/dist/routes/request.js
node -c /app/dist/routes/media.js
echo "[Patch] Ready to start Jellyseerr."
