#!/usr/bin/env python3
"""Read product JSON-LD; fail closed on uncertain prices/stock; notify on meaningful transitions."""
import json, os, re, sys, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents
CONFIG = ROOT/'products.json'
OUT = ROOT/'site'/'radar.json'
STATE = ROOT/'data'/'state.json'
UA = 'PokeRadarPersonalMonitor/1.0 (+respectful scheduled product tracking)'

class JSONLD(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_script=False; self.buf=''; self.objects=[]
    def handle_starttag(self, tag, attrs):
        if tag=='script':
            d=dict(attrs); self.in_script=d.get('type','').lower()=='application/ld+json'; self.buf=''
    def handle_data(self, data):
        if self.in_script: self.buf+=data
    def handle_endtag(self, tag):
        if tag=='script' and self.in_script:
            try: self.objects.append(json.loads(self.buf.strip()))
            except (ValueError, TypeError): pass
            self.in_script=False

def walk(obj):
    if isinstance(obj,list):
        for value in obj: yield from walk(value)
    elif isinstance(obj,dict):
        yield obj
        for key in ('@graph','mainEntity','itemListElement'):
            if key in obj: yield from walk(obj[key])

def offers(obj):
    if isinstance(obj,list):
        for x in obj: yield from offers(x)
    elif isinstance(obj,dict):
        if obj.get('@type') in ('Offer','AggregateOffer') or 'availability' in obj and 'price' in obj: yield obj
        for x in obj.get('offers',[]) if isinstance(obj.get('offers'),list) else [obj.get('offers')]:
            if x: yield from offers(x)

def normalize_price(raw):
    if raw is None: return None
    s=str(raw).strip().replace('€','').replace(' ','')
    if ',' in s and '.' in s:
        s=s.replace('.','').replace(',','.') if s.rfind(',')>s.rfind('.') else s.replace(',','')
    elif ',' in s: s=s.replace(',','.')
    try:
        val=round(float(s),2)
        return val if 0 < val < 100000 else None
    except ValueError: return None

def parse_page(html):
    p=JSONLD();p.feed(html)
    products=[o for root in p.objects for o in walk(root) if 'Product' in str(o.get('@type',''))]
    candidates=[]
    for product in products:
        for offer in offers(product.get('offers')):
            currency=str(offer.get('priceCurrency','')).upper()
            price=normalize_price(offer.get('price', (offer.get('priceSpecification') or {}).get('price') if isinstance(offer.get('priceSpecification'),dict) else None))
            if currency!='EUR' or price is None: continue
            status=str(offer.get('availability','')).lower().split('/')[-1]
            stock='in_stock' if status in ('instock','limitedavailability') else 'out_of_stock' if status in ('outofstock','soldout','discontinued') else 'preorder' if status=='preorder' else 'unknown'
            candidates.append((price,stock))
    if not candidates: return {'status':'unverifiable','price':None,'stock':'unknown','reason':'Geen eenduidige EUR Product/Offer JSON-LD'}
    # Do not treat an aggregate's lowPrice as a confirmed offer
    price,stock=min(candidates, key=lambda t:t[0])
    return {'status':'ok','price':price,'stock':stock,'reason':None}

def fetch(url):
    parsed=urlparse(url)
    if parsed.scheme!='https' or not parsed.hostname: raise ValueError('Alleen HTTPS product-URLs')
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml'})
    with urllib.request.urlopen(req,timeout=18) as resp:
        if urlparse(resp.geturl()).scheme!='https': raise ValueError('Redirect naar onveilige URL')
        if 'html' not in resp.headers.get('Content-Type','').lower(): raise ValueError('Geen HTML-response')
        raw=resp.read(2_000_001)
        if len(raw)>2_000_000: raise ValueError('HTML groter dan 2 MB')
        return raw.decode('utf-8','replace')

def telegram(message):
    token=os.getenv('TELEGRAM_BOT_TOKEN');chat=os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat: return False
    from urllib.parse import urlencode
    data=urlencode({'chat_id':chat,'text':message,'disable_web_page_preview':'true'}).encode()
    req=urllib.request.Request('https://api.telegram.org/bot'+token+'/sendMessage',data=data,method='POST')
    try:
        with urllib.request.urlopen(req,timeout=15): pass
        return True
    except Exception as e:
        print('Telegram failed:',str(e)[:120],file=sys.stderr); return False

def main():
    cfg=json.loads(CONFIG.read_text());previous=json.loads(STATE.read_text()) if STATE.exists() else {}
    prev=previous.get('products',{}); now=datetime.now(timezone.utc).isoformat(timespec='seconds')
    current={}; notifications=[]
    for prod in cfg['products']:
        pid=prod['id']; old=prev.get(pid,{}); limit=prod.get('max_price'); record={**prod,'checked_at':now}
        try:
            result=parse_page(fetch(prod['url']))
            record.update(result)
        except Exception as e:
            record.update(status='unverifiable',price=None,stock='unknown',reason=str(e)[:130])
        if record['status']=='ok':
            if old.get('status')=='ok':
                fresh=old.get('stock')!='in_stock' and record['stock']=='in_stock'
                drop=old.get('price') is not None and record['price'] < old['price']
                crossed=limit is not None and (old.get('price') is None or old['price']>limit) and record['price']<=limit
                if fresh or drop or crossed:
                    tags=[]
                    if fresh: tags.append('weer op voorraad')
                    if drop: tags.append(f"prijsdaling €{old['price']:.2f} → €{record['price']:.2f}")
                    if crossed: tags.append('onder jouw kooplimiet')
                    notifications.append(f"🎴 {prod['name']} ({prod['store']}): {', '.join(tags)}. €{record['price']:.2f}\n{prod['url']}")
            # New products only alert if enabled, not just on initial batch
            elif old.get('status')=='unverifiable' and record['stock']=='in_stock' and limit is not None and record['price']<=limit:
                notifications.append(f"🎴 Controle hersteld: {prod['name']} bij {prod['store']} nu €{record['price']:.2f} op voorraad.\n{prod['url']}")
        current[pid]=record
        print(pid,record['status'],record.get('price'),record.get('stock'),record.get('reason'))
    # notify, but only commit state on successful send, to ensure alerts can retry
    if notifications:
        ok=telegram('\n\n'.join(notifications)[:3900]);print('Telegram notifications:',len(notifications),'sent:',ok)
        if not ok and os.getenv('TELEGRAM_BOT_TOKEN') and os.getenv('TELEGRAM_CHAT_ID'):
            # retry on next scheduled check: preserve prior values for changed records
            for nprod in cfg['products']:
                pid=nprod['id']
                if pid in prev and (prev[pid].get('price')!=current[pid].get('price') or prev[pid].get('stock')!=current[pid].get('stock')):
                    current[pid]['_notify_retry']=prev[pid]
    # Keep alert comparison baseline independent from previous failure, future retry
    compare={pid:dict(record) for pid,record in current.items()}
    for pid,r in compare.items():
        if '_notify_retry' in r:
            compare[pid]=r.pop('_notify_retry')
    output={'updated_at':now,'products':list(current.values()),'notifications_configured':bool(os.getenv('TELEGRAM_BOT_TOKEN') and os.getenv('TELEGRAM_CHAT_ID'))}
    OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps({'products':compare},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__': main()
