#!/bin/sh
set -e

python3 -m bot.recreate_database
exec python3 -m bot