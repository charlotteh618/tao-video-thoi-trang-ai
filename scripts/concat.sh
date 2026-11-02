#!/bin/bash
# Ghép các đoạn video thành một video, giữ nguyên thứ tự đưa vào.
# Cách dùng: ./scripts/concat.sh output/video-30s.mp4 clip1.mp4 clip2.mp4 clip3.mp4
set -euo pipefail

if [ "$#" -lt 3 ]; then
  echo "Cách dùng: $0 <output.mp4> <clip1.mp4> <clip2.mp4> [clip3.mp4 ...]"
  exit 1
fi

output="$1"
shift

list_file="$(mktemp)"
trap 'rm -f "$list_file"' EXIT

for clip in "$@"; do
  printf "file '%s'\n" "$(realpath "$clip")" >> "$list_file"
done

mkdir -p "$(dirname "$output")"

ffmpeg -y -f concat -safe 0 -i "$list_file" \
  -c:v libx264 -pix_fmt yuv420p -r 30 "$output"

echo "Đã ghép xong: $output"
