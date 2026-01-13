#!/usr/bin/env python3
import os
import re
import json
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("Warning: Pillow not installed. EXIF reading disabled.")

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC_AVAILABLE = True
except ImportError:
    HEIC_AVAILABLE = False

BASE_DIR = Path(__file__).parent
IMAGES_DIR = BASE_DIR / "images"
DATA_DIR = BASE_DIR / "data"
OUTPUT_FILE = DATA_DIR / "artworks.json"

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
if HEIC_AVAILABLE:
    SUPPORTED_EXTENSIONS.update({'.heic', '.heif'})

def get_exif_datetime(image_path):
    if not PILLOW_AVAILABLE:
        return None, None
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if not exif_data:
                return None, None
            exif = {TAGS.get(k, k): v for k, v in exif_data.items()}
            for tag in ['DateTimeOriginal', 'DateTime', 'DateTimeDigitized']:
                if tag in exif:
                    dt_str = exif[tag]
                    try:
                        dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                        return dt, "EXIF_DATETIME"
                    except ValueError:
                        continue
            return None, None
    except Exception:
        return None, None

def parse_filename_timestamp(filename):
    name = Path(filename).stem
    if name.startswith('mmexport'):
        match = re.search(r'mmexport(\d{13})', name)
        if match:
            ts = int(match.group(1))
            try:
                dt = datetime.fromtimestamp(ts / 1000)
                return dt, "FILENAME_TIMESTAMP"
            except (ValueError, OSError):
                pass
    match = re.search(r'IMG_(\d{8})_(\d{6})', name)
    if match:
        try:
            dt = datetime.strptime(match.group(1) + match.group(2), "%Y%m%d%H%M%S")
            return dt, "FILENAME_PATTERN"
        except ValueError:
            pass
    match = re.search(r'Screenshot[_-](\d{4})[_-](\d{2})[_-](\d{2})', name)
    if match:
        try:
            dt = datetime.strptime(f"{match.group(1)}{match.group(2)}{match.group(3)}", "%Y%m%d")
            return dt, "FILENAME_PATTERN"
        except ValueError:
            pass
    match = re.search(r'(\d{4})[_-]?(\d{2})[_-]?(\d{2})', name)
    if match:
        try:
            dt = datetime.strptime(f"{match.group(1)}{match.group(2)}{match.group(3)}", "%Y%m%d")
            if 2020 <= dt.year <= 2030:
                return dt, "FILENAME_PATTERN"
        except ValueError:
            pass
    return None, None

def get_file_mtime(image_path):
    try:
        mtime = os.path.getmtime(image_path)
        dt = datetime.fromtimestamp(mtime)
        return dt, "FILE_MTIME"
    except Exception:
        return datetime.now(), "FALLBACK"

def get_confidence(time_source):
    confidence_map = {
        "EXIF_DATETIME": "HIGH",
        "FILENAME_TIMESTAMP": "MEDIUM",
        "FILENAME_PATTERN": "MEDIUM",
        "FILE_MTIME": "LOW",
        "FALLBACK": "LOW"
    }
    return confidence_map.get(time_source, "LOW")

def validate_datetime(dt):
    now = datetime.now()
    issues = []
    if dt > now:
        issues.append("FUTURE_TIME")
    if dt.year < 2020:
        issues.append("EARLY_TIME")
    return issues

def format_date_display(dt):
    return f"{dt.year}年{dt.month:02d}月{dt.day:02d}日"

def scan_images():
    if not IMAGES_DIR.exists():
        print(f"Error: Images directory not found: {IMAGES_DIR}")
        return []
    images = []
    for f in IMAGES_DIR.iterdir():
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
            images.append(f)
    return images

def process_images():
    images = scan_images()
    if not images:
        print("No images found in images/ directory.")
        return None
    artworks = []
    warnings = []
    for idx, img_path in enumerate(images, 1):
        dt, source = get_exif_datetime(img_path)
        if dt is None:
            dt, source = parse_filename_timestamp(img_path.name)
            if dt is None:
                warnings.append({
                    "file": img_path.name,
                    "issue": "NO_EXIF",
                    "fallback": "FILE_MTIME"
                })
            else:
                warnings.append({
                    "file": img_path.name,
                    "issue": "NO_EXIF",
                    "fallback": source
                })
        if dt is None:
            dt, source = get_file_mtime(img_path)
        issues = validate_datetime(dt)
        for issue in issues:
            warnings.append({
                "file": img_path.name,
                "issue": issue,
                "fallback": None
            })
        artwork = {
            "id": f"artwork_{idx:03d}",
            "filename": img_path.name,
            "path": f"images/{img_path.name}",
            "timestamp": int(dt.timestamp() * 1000),
            "date_display": format_date_display(dt),
            "time_source": source,
            "confidence": get_confidence(source),
            "issues": issues if issues else None
        }
        artworks.append(artwork)
    artworks.sort(key=lambda x: x["timestamp"], reverse=True)
    for idx, artwork in enumerate(artworks, 1):
        artwork["id"] = f"artwork_{idx:03d}"
    return {
        "generated_at": datetime.now().isoformat(),
        "total_count": len(artworks),
        "warnings": warnings,
        "artworks": artworks
    }

def print_report(data):
    print("\n" + "=" * 60)
    print("  凯晗书画作品集 - 数据生成报告")
    print("=" * 60)
    print(f"\n✅ 成功处理: {data['total_count']} 张图片")
    print(f"📁 输出文件: {OUTPUT_FILE}")
    source_counts = {}
    for artwork in data['artworks']:
        src = artwork['time_source']
        source_counts[src] = source_counts.get(src, 0) + 1
    print("\n⏱️ 时间来源统计:")
    source_labels = {
        "EXIF_DATETIME": "EXIF原始时间 (HIGH)",
        "FILENAME_TIMESTAMP": "文件名时间戳 (MEDIUM)",
        "FILENAME_PATTERN": "文件名日期模式 (MEDIUM)",
        "FILE_MTIME": "文件修改时间 (LOW)",
        "FALLBACK": "默认时间 (LOW)"
    }
    for src, count in source_counts.items():
        label = source_labels.get(src, src)
        print(f"   • {label}: {count} 张")
    if data['warnings']:
        print(f"\n⚠️ 警告 ({len(data['warnings'])}项):")
        shown = 0
        for w in data['warnings']:
            if shown >= 5:
                remaining = len(data['warnings']) - 5
                print(f"   ... 还有 {remaining} 项警告")
                break
            fallback_info = f" -> 使用{w['fallback']}" if w['fallback'] else ""
            print(f"   • {w['file']} - {w['issue']}{fallback_info}")
            shown += 1
    else:
        print("\n✅ 无警告")
    if data['artworks']:
        dates = [a['date_display'] for a in data['artworks']]
        print(f"\n📅 作品时间范围: {dates[-1]} ~ {dates[0]}")
    print("\n" + "=" * 60)

def main():
    print("正在扫描书法作品...")
    DATA_DIR.mkdir(exist_ok=True)
    data = process_images()
    if data is None:
        return
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print_report(data)
    print("\n✅ 数据生成完成！请在浏览器中打开 index.html 查看作品集。\n")

if __name__ == "__main__":
    main()
