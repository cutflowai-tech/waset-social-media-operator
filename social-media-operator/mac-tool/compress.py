#!/usr/bin/env python3
"""Local batch compression. No uploads, source edits or automatic trimming."""
import argparse, csv, html, json, math, os, shutil, subprocess, sys, tempfile
from datetime import datetime
from fractions import Fraction
from pathlib import Path

LIMIT = 300_000_000
TARGET = 290_000_000
PROFILES = {'post': (LIMIT, TARGET), 'story': (100_000_000, 95_000_000)}
EXTENSIONS = {'.mp4', '.mov', '.m4v', '.mkv', '.avi', '.webm', '.mxf'}

def run(args):
    p = subprocess.run([str(a) for a in args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-2500:].strip() or 'Command failed')
    return p.stdout

def probe(path):
    raw = json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', path]))
    videos = [s for s in raw['streams'] if s.get('codec_type') == 'video' and not s.get('disposition', {}).get('attached_pic')]
    if len(videos) != 1:
        raise ValueError('محتاج فيديو بمسار صورة واحد؛ راجع الملف.')
    v = videos[0]
    duration = float(v.get('duration') or raw['format'].get('duration') or 0)
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('مدة الفيديو غير صالحة.')
    rotation = float(next((s['rotation'] for s in v.get('side_data_list', []) if 'rotation' in s), v.get('tags', {}).get('rotate', 0))) % 360
    if rotation not in (0, 90, 180, 270):
        raise ValueError('زاوية دوران غير معتادة؛ محتاج مراجعة.')
    w, h = int(v['width']), int(v['height'])
    if rotation in (90, 270):
        w, h = h, w
    fps = float(Fraction(v.get('avg_frame_rate', '0/1')))
    if not fps or not math.isfinite(fps):
        raise ValueError('معدل الإطارات غير معروف.')
    audio = [s for s in raw['streams'] if s.get('codec_type') == 'audio']
    return dict(duration=duration, width=w, height=h, fps=fps, audio=len(audio),
                hdr=v.get('color_transfer') in ('smpte2084', 'arib-std-b67'), index=v['index'])

def decode(path):
    run(['ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-i', path, '-map', '0:v:0', '-map', '0:a?', '-f', 'null', '-'])

def bitrate(info, target):
    rate = int(target * 8 * .98 / info['duration'] - 128000 * info['audio'])
    if rate < 250000:
        raise ValueError('الفيديو طويل جدًا للضغط الآمن بهذا الحد؛ ارجع للمدير.')
    return min(rate, 24_000_000)

def encode(source, output, info, rate, log):
    common = ['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-xerror', '-y', '-i', source,
              '-map', f"0:{info['index']}", '-c:v', 'libx264', '-preset', 'medium', '-threads', '2',
              '-b:v', str(rate), '-maxrate', '25M', '-bufsize', '25M', '-pix_fmt', 'yuv420p', '-fps_mode', 'passthrough',
              '-passlogfile', log]
    run(common + ['-pass', '1', '-an', '-f', 'null', os.devnull])
    run(common + ['-map', '0:a?', '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-pass', '2',
                  '-movflags', '+faststart', '-use_editlist', '0', '-metadata:s:v:0', 'rotate=0', output])

def verify(source_info, output, limit):
    if output.stat().st_size >= limit:
        return False
    actual = probe(output)
    if (actual['width'], actual['height']) != (source_info['width'], source_info['height']):
        raise ValueError('فشل التحقق من أبعاد/اتجاه الناتج.')
    if abs(actual['duration'] - source_info['duration']) > max(.15, 2 / source_info['fps']):
        raise ValueError('مدة الناتج مختلفة؛ الملف محتاج مراجعة.')
    if abs(actual['fps'] - source_info['fps']) > max(.02, source_info['fps'] * .01):
        raise ValueError('معدل الإطارات مختلف؛ الملف محتاج مراجعة.')
    if actual['audio'] != source_info['audio']:
        raise ValueError('عدد مسارات الصوت مختلف.')
    decode(output)
    return True

def process(source, destination, limit=LIMIT, target=TARGET):
    row = dict(file=source.name, status='failed', before_bytes=source.stat().st_size,
               after_bytes='', duration_seconds='', dimensions='', fps='', output='', note='')
    try:
        original = (source.stat().st_size, source.stat().st_mtime_ns)
        info = probe(source)
        row.update(duration_seconds=round(info['duration'], 3), dimensions=f"{info['width']}×{info['height']}", fps=round(info['fps'], 5))
        if row['before_bytes'] < limit:
            decode(source)
            row.update(status='already_under_limit', after_bytes=row['before_bytes'], output=str(source), note='الأصل أقل من الحد ولم يتغير؛ راجع الجودة و1080 والمدة قبل النشر.')
            return row
        if info['hdr']:
            raise ValueError('ملف HDR؛ ارجع للمدير لتصدير SDR مناسب بدل تغيير الألوان تلقائيًا.')
        if info['width'] % 2 or info['height'] % 2:
            raise ValueError('الأبعاد فردية؛ صدّر من Topaz بالأبعاد المطلوبة بدل قص الصورة تلقائيًا.')
        if shutil.disk_usage(destination).free < target * 3:
            raise ValueError('المساحة غير كافية؛ وفر مساحة ثم حاول مرة أخرى.')
        rate = bitrate(info, target)
        with tempfile.TemporaryDirectory(prefix='.working-', dir=destination) as tmp:
            tmp = Path(tmp)
            output = tmp / 'video.mp4'
            for attempt in range(2):
                print(f'  ترميز على مرحلتين — محاولة {attempt + 1}', flush=True)
                encode(source, output, info, rate, tmp / 'pass')
                if verify(info, output, limit):
                    break
                if attempt == 1:
                    raise ValueError('الناتج ما زال فوق الحد بعد محاولتين؛ محتاج تدخل.')
                rate = int(rate * target / output.stat().st_size * .95)
                if rate < 250000:
                    raise ValueError('الضغط الإضافي يحتاج معدل بيانات منخفض جدًا؛ راجع المدير.')
            if (source.stat().st_size, source.stat().st_mtime_ns) != original:
                raise ValueError('الملف الأصلي اتغير أثناء التشغيل؛ أعد المحاولة على نسخة ثابتة.')
            name = source.name + '.social.mp4'
            final = destination / name
            number = 2
            while final.exists():
                final = destination / f'{source.name}.{number}.social.mp4'
                number += 1
            output.rename(final)
            row.update(status='compressed', after_bytes=final.stat().st_size, output=str(final), note='نجح الفحص الفني؛ شاهد الفيديو كاملًا قبل النشر.')
    except Exception as error:
        row['note'] = str(error)
    return row

def reports(rows, destination):
    headers = ['file', 'status', 'before_bytes', 'after_bytes', 'duration_seconds', 'dimensions', 'fps', 'output', 'note']
    (destination / 'report.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    with (destination / 'report.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers); writer.writeheader()
        for row in rows:
            writer.writerow({k: ("'" + str(v) if isinstance(v, str) and v.startswith(('=', '+', '-', '@')) else v) for k, v in row.items()})
    labels = ['الملف', 'النتيجة', 'الحجم الأصلي بالبايت', 'حجم الناتج بالبايت', 'المدة بالثواني', 'الأبعاد', 'FPS', 'مكان الملف', 'ملاحظات']
    table = '<tr>' + ''.join('<th>'+html.escape(t)+'</th>' for t in labels) + '</tr>'
    for row in rows:
        table += '<tr>' + ''.join('<td>'+html.escape(str(row.get(k,'')))+'</td>' for k in headers) + '</tr>'
    (destination / 'report.html').write_text('<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><title>تقرير تجهيز الفيديوهات</title><style>body{font:16px system-ui;margin:28px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;padding:10px;overflow-wrap:anywhere}th{background:#eee}</style><h1>تقرير تجهيز الفيديوهات</h1><p>compressed = تم الضغط • already_under_limit = الأصل أقل من الحد • failed = يحتاج تدخل. 1 MB = 1,000,000 بايت. الفحص الفني لا يغني عن مشاهدة الفيديو.</p><table>'+table+'</table></html>', encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description='ضغط مجموعة فيديوهات لأقل من 300 MB مع الحفاظ على الأصل')
    parser.add_argument('folder', nargs='?', type=Path)
    parser.add_argument('--choose', action='store_true')
    parser.add_argument('--profile', choices=PROFILES)
    args = parser.parse_args()
    for binary in ('ffmpeg', 'ffprobe'):
        if not shutil.which(binary):
            raise SystemExit('شغّل Setup.command أولًا لتثبيت FFmpeg.')
    if args.choose and not args.profile:
        selected = subprocess.run(['osascript', '-e', 'choose from list {"Post — 290 MB", "Story — 95 MB"} with prompt "اختار نوع الفيديوهات في الفولدر" default items {"Post — 290 MB"}'], capture_output=True, text=True)
        if selected.returncode or selected.stdout.strip() == 'false': return 0
        args.profile = 'story' if selected.stdout.startswith('Story') else 'post'
    limit, target = PROFILES[args.profile or 'post']
    print(f"Profile: {args.profile or 'post'}; limit < {limit:,} bytes; target {target:,} bytes")
    if args.choose:
        p = subprocess.run(['osascript', '-e', 'POSIX path of (choose folder with prompt "اختار فولدر الفيديوهات بعد Topaz")'], capture_output=True, text=True)
        if p.returncode: return 0
        args.folder = Path(p.stdout.strip())
    if not args.folder or not args.folder.is_dir():
        parser.error('اختار فولدر موجود.')
    folder = args.folder.resolve()
    sources = sorted(p for p in folder.iterdir() if p.is_file() and not p.is_symlink() and p.suffix.lower() in EXTENSIONS)
    if not sources:
        print('الفولدر مفيهوش ملفات فيديو مدعومة. الأداة بتقرأ الملفات الموجودة فيه مباشرة، مش الفولدرات الداخلية.')
        return 0
    destination = Path(tempfile.mkdtemp(prefix='Social Ready '+datetime.now().strftime('%Y-%m-%d %H-%M-%S')+' ', dir=folder))
    rows=[]
    try:
        for index, source in enumerate(sources, 1):
            print(f'[{index}/{len(sources)}] {source.name}', flush=True)
            row = process(source, destination, limit=limit, target=target)
            row['note'] = f"{args.profile or 'post'}: target {target:,}, limit < {limit:,}. " + row['note']
            rows.append(row)
            reports(rows, destination)
            print(rows[-1]['status'], flush=True)
    except KeyboardInterrupt:
        print('تم إيقاف التشغيل. نتائج الملفات المكتملة محفوظة.')
        reports(rows, destination)
        return 130
    print(f'التقرير والنسخ الجديدة: {destination}', flush=True)
    if sys.platform == 'darwin': subprocess.run(['open', str(destination / 'report.html')], check=False)
    return 1 if any(r['status']=='failed' for r in rows) else 0

if __name__ == '__main__':
    sys.exit(main())
