#!/usr/bin/env python3
"""Audit a full Saturday-Friday draft; never reads/writes remote services."""
import json, sys
from collections import Counter
from datetime import date, timedelta
from zoneinfo import ZoneInfo
from datetime import datetime

PROTECTED = ('format', 'status', 'code', 'ready_file', 'caption', 'publish_at')

def audit(plan, current):
    start=date.fromisoformat(plan['week_start'])
    counts=Counter();post_days=set();assets=set();items=set();errors=[];conflicts=[]
    records={str(x['item_id']):x for x in current}
    published=set(plan.get('published_assets',[]))
    for slot in plan['slots']:
        item=str(slot['item_id']);asset=slot.get('asset_id')
        when=datetime.fromisoformat(slot['publish_at'])
        if when.tzinfo is None:
            errors.append(f'{item}: missing explicit UTC offset');continue
        local=when.astimezone(ZoneInfo('Africa/Cairo'));day=local.date()
        if not start<=day<start+timedelta(days=7):errors.append(f'{item}: outside week')
        if item in items or not asset or asset in assets or asset in published:errors.append(f'{item}: duplicate, published or unidentified asset')
        items.add(item);assets.add(asset)
        fmt=slot['snapshot']['format']
        if fmt not in ('Post','Story'):errors.append(f'{item}: unknown format');continue
        counts[(day,fmt)]+=1
        if fmt=='Post':post_days.add(day)
        if slot['snapshot']['status'] in ('Published','Cancelled','Blocked'):errors.append(f'{item}: unavailable status')
        now=records.get(item)
        if now is None or any(now.get(k)!=slot['snapshot'].get(k) for k in PROTECTED):conflicts.append(item)
    shortages=[]
    for i in range(7):
        day=start+timedelta(days=i);count=counts[(day,'Story')]
        if count<3:shortages.append({'date':str(day),'format':'Story','missing':3-count})
        if count>3:errors.append(f'{day}: more than 3 Stories')
    posts=sum(n for (day,fmt),n in counts.items() if fmt=='Post')
    if posts<4:shortages.append({'format':'Post','missing':4-posts})
    if posts>4 or len(post_days)!=posts:errors.append('Posts must occupy four distinct days at most')
    return {'structurally_valid':not errors,'complete':not errors and not shortages,'safe_snapshot':not conflicts,
            'errors':errors,'shortages':shortages,'conflicting_item_ids':conflicts}

if __name__=='__main__':
    with open(sys.argv[1],encoding='utf-8') as f:data=json.load(f)
    result=audit(data['plan'],data['current_items']);print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(0 if result['complete'] and result['safe_snapshot'] else 1)
