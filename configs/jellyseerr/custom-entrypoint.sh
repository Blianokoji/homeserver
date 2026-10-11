#!/bin/sh
/app/config/apply-patches.sh || true
exec /sbin/tini -- pnpm start
