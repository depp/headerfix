#!/bin/sh
dir=`dirname "$0"`
PYTHONPATH="$dir/lib:$PYTHONPATH" exec python -m header.tool "$@"
