#!/bin/sh
dir=`dirname "$0"`
PYTHONPATH="$dir:$PYTHONPATH" exec python -m header.tool "$@"
