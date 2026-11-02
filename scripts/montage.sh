#!/bin/bash
# Ghép montage ngầu: cắt mỗi đoạn còn 4 giây, bắt đầu từ giây thứ 1,
# rồi ghép lại thành video khoảng 20 giây với 5 đoạn.
# Cách dùng: ./scripts/montage.sh output/video-20s.mp4 clip1.mp4 clip2.mp4 clip3.mp4 clip4.mp4 clip5.mp4
set -euo pipefail

if [ "$#" -lt 3 ]; then
  echo "Cách dùng: $0 <output.mp4> <clip1.mp4> <clip2.mp4> [clip3.mp4 ...]"
  exit 1
fi

output="$1"
shift

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

list_file="$tmp_dir/list.txt"
i=1

for clip in "$@"; do
  part="$tmp_dir/part$i.mp4"
  ffmpeg -y -ss 1 -t 4 -i "$clip" -c:v libx264 -pix_fmt yuv420p -r 30 "$part"
  printf "file '%s'\n" "$part" >> "$list_file"
  i=$((i + 1))
done

mkdir -p "$(dirname "$output")"

ffmpeg -y -f concat -safe 0 -i "$list_file" \
  -c:v libx264 -pix_fmt yuv420p -r 30 "$output"

echo "Đã ghép xong: $output"
