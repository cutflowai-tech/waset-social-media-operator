#!/bin/bash
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if ! command -v brew >/dev/null; then
  echo 'يلزم Homebrew. افتح الموقع الرسمي وثبته ثم شغّل الملف ده مرة تانية:'
  echo 'https://brew.sh/'
  open 'https://brew.sh/'
else
  echo 'سيتم تثبيت Python وFFmpeg من Homebrew. اضغط Enter للبدء، أو Ctrl+C للإلغاء.'
  read -r
  brew install python ffmpeg
  if command -v python3 >/dev/null && command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null; then
    echo 'جاهز. افتح Compress.command لبدء تجهيز الفيديوهات.'
  else
    echo 'التثبيت لم يكتمل. احتفظ برسالة الخطأ واطلب المساعدة.'
  fi
fi
printf '\nاضغط Enter لإغلاق النافذة.'
read -r
