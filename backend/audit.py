#!/usr/bin/env python3
"""内容质量巡检脚本 — 图片有效性 · 链接 · 文案 · SEO"""

import sys, os, json, urllib.request
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
IMAGES = os.path.join(os.path.dirname(BASE), 'frontend', 'public', 'images')
sys.path.insert(0, BASE)
from models import create_db_engine, create_session_factory, Trip

def check_all():
    engine = create_db_engine(f'sqlite:///{BASE}/trips.db')
    s = create_session_factory(engine)()
    trips = s.query(Trip).all()
    issues = []
    fixes = []

    for t in trips:
        tid = t.id
        title = t.title or '(no title)'

        # 1. 图片检查
        if t.cover_image:
            if t.cover_image.startswith('/images/'):
                fname = os.path.basename(t.cover_image)
                fpath = os.path.join(IMAGES, fname)
                if not os.path.exists(fpath):
                    issues.append({'trip_id': tid, 'type': 'image_missing', 'detail': fpath, 'severity': 'warning'})
                else:
                    size_kb = os.path.getsize(fpath) // 1024
                    if size_kb < 10:
                        issues.append({'trip_id': tid, 'type': 'image_too_small', 'detail': f'{size_kb}KB', 'severity': 'info'})
            else:
                issues.append({'trip_id': tid, 'type': 'image_not_local', 'detail': t.cover_image, 'severity': 'info'})
        else:
            issues.append({'trip_id': tid, 'type': 'image_missing', 'detail': 'no cover_image', 'severity': 'critical'})

        # 2. 文案检查
        content_len = len(t.content or '')
        if content_len < 100:
            issues.append({'trip_id': tid, 'type': 'content_too_short', 'detail': f'{content_len}chars', 'severity': 'warning'})
        if not t.story:
            issues.append({'trip_id': tid, 'type': 'story_missing', 'detail': '', 'severity': 'warning'})
        if not t.subtitle:
            issues.append({'trip_id': tid, 'type': 'subtitle_missing', 'detail': '', 'severity': 'info'})
        if t.subtitle and t.subtitle == t.title:
            issues.append({'trip_id': tid, 'type': 'subtitle_duplicate_title', 'detail': '', 'severity': 'warning'})

        # 3. SEO 检查
        title_len = len(t.title or '')
        if title_len < 10 or title_len > 60:
            issues.append({'trip_id': tid, 'type': 'title_length', 'detail': f'{title_len}chars', 'severity': 'info'})
        if '##' not in (t.content or ''):
            issues.append({'trip_id': tid, 'type': 'no_h2_structure', 'detail': '', 'severity': 'info'})

        # 4. 来源检查
        if not t.image_source:
            issues.append({'trip_id': tid, 'type': 'no_image_source', 'detail': '', 'severity': 'info'})

    # 汇总
    critical = [i for i in issues if i['severity'] == 'critical']
    warnings = [i for i in issues if i['severity'] == 'warning']
    infos = [i for i in issues if i['severity'] == 'info']

    report = {
        'timestamp': datetime.now().isoformat(),
        'total_trips': len(trips),
        'summary': {'critical': len(critical), 'warning': len(warnings), 'info': len(infos)},
        'issues': issues,
        'auto_fixes': fixes,
    }

    s.close()
    return report

if __name__ == '__main__':
    report = check_all()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # Save
    datadir = os.path.join(os.path.dirname(BASE), 'data')
    os.makedirs(datadir, exist_ok=True)
    with open(os.path.join(datadir, 'audit-report.json'), 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f'\nReport saved to data/audit-report.json')
    print(f'Summary: {report["summary"]["critical"]} critical, {report["summary"]["warning"]} warnings, {report["summary"]["info"]} info')
