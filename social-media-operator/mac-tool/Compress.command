#!/bin/bash
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
cd -- "$(dirname -- "$0")" || exit 1
if ! command -v python3 >/dev/null || ! command -v ffmpeg >/dev/null || ! command -v ffprobe >/dev/null; then
  echo 'شغّل Setup.command أولًا.'
else
  python3 compress.py --choose
fi
printf '\nاضغط Enter لإغلاق النافذة.'
read -r
