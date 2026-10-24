#!/bin/sh
# Runs both Next.js apps from one container: website on 3000, backoffice on 3001.
set -e

(cd /app/website && npx next dev -H 0.0.0.0 -p 3000) &
WEBSITE_PID=$!
(cd /app/backoffice && npx next dev -H 0.0.0.0 -p 3001) &
BACKOFFICE_PID=$!

trap 'kill $WEBSITE_PID $BACKOFFICE_PID 2>/dev/null' INT TERM

# Exit as soon as either app dies so Compose can surface the failure.
while kill -0 $WEBSITE_PID 2>/dev/null && kill -0 $BACKOFFICE_PID 2>/dev/null; do
  sleep 2
done
kill $WEBSITE_PID $BACKOFFICE_PID 2>/dev/null
exit 1
