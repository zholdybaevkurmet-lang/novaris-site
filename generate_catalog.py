#!/usr/bin/env python3
"""Generate static HTML catalog from price (18).xls"""

import pandas as pd
import os
import re
import json
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent
CATALOG_DIR = PROJECT_DIR / "catalog"
PRICE_FILE = PROJECT_DIR / "price (18).xls"
BASE_URL = "https://novaris.kz"

# ── Transliteration ────────────────────────────────────────────────────────────
_TR = {
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh',
    'з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o',
    'п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts',
    'ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',
}

def translit(text: str) -> str:
    return ''.join(_TR.get(c, c) for c in text.lower())

def slugify(name: str) -> str:
    s = translit(name)
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return re.sub(r'-+', '-', s).strip('-')[:80]

_STOP_WORDS = {
    'с', 'для', 'и', 'в', 'из', 'по', 'на', 'а', 'не', 'малой', 'мощности',
    'алюминиевый', 'медный', 'монтажный', 'монтажные', 'неизолированный',
    'неизолированные', 'антивибрационный', 'изолированный', 'оптический',
    'пожарный', 'огнестойкий', 'нефтепогружной', 'греющий', 'лифтовой',
    'микрофонный', 'сигнальный', 'связи', 'силовой', 'судовой',
    'телефонный', 'термостойкий', 'термостойкие', 'термоэлектродный',
    'высоковольтный', 'радиочастотный', 'трибоэлектрический', 'управления',
    'универсальный', 'нpp', 'нпп', 'спэ',
}

def cat_slug(cat_name: str) -> str:
    """Build a unique slug: strip Кабель/Провод prefix, skip stop words,
    prefer the first technical code (all-caps or mixed-caps token)."""
    name = cat_name
    for prefix in ('Кабель ', 'Провод ', 'Эмальпровод '):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break

    # First pass: look for a technical code (contains uppercase letter or digit, len ≥ 2)
    tokens = re.split(r'[\s,.\-:;/()+]+', name)
    # Prefer tokens that look like cable codes (contain uppercase ASCII or Cyrillic caps + digit)
    for tok in tokens:
        t = tok.strip()
        if not t or len(t) < 2:
            continue
        if t.lower() in _STOP_WORDS:
            continue
        # If it starts with an uppercase letter or digit → likely a code
        if re.match(r'[A-ZА-Я0-9]', t):
            return slugify(t)[:40]

    # Second pass: any non-stop word
    for tok in tokens:
        t = tok.strip()
        if t and len(t) >= 2 and t.lower() not in _STOP_WORDS:
            return slugify(t)[:40]

    return slugify(cat_name)[:40]

# ── Parse XLS ──────────────────────────────────────────────────────────────────
def parse_xls():
    df = pd.read_excel(PRICE_FILE, engine='xlrd', header=None)

    categories = {}   # slug -> {name, slug, products:[]}
    cat_order  = []

    def ensure_cat(name):
        slug = cat_slug(name)
        if slug not in categories:
            categories[slug] = {'name': name, 'slug': slug, 'products': []}
            cat_order.append(slug)
        return slug

    def process_panel(nc, uc, sc, default_cat=None):
        cur = default_cat
        for i, row in df.iterrows():
            if i < 9:
                continue
            name  = str(row[nc]).strip() if pd.notna(row[nc]) else ''
            unit  = str(row[uc]).strip() if pd.notna(row[uc]) else ''
            stock = row[sc]

            if not name:
                continue

            # Skip header-repeat rows
            if name in ('Наименование',) or unit in ('Ед.изм',):
                continue

            is_cat = (not unit) and (pd.isna(stock) or str(stock).strip() in ('', 'nan'))

            if is_cat:
                # filter noise
                if (len(name) < 4
                        or 'К А Б Е Л' in name
                        or name.startswith(')')
                        or name.startswith('Х/Б')):
                    continue
                cur = ensure_cat(name)
            elif cur and unit:
                stock_val = 0.0
                try:
                    stock_val = float(stock) if pd.notna(stock) else 0.0
                except (ValueError, TypeError):
                    pass
                categories[cur]['products'].append({
                    'name':     name,
                    'unit':     unit,
                    'stock':    round(stock_val, 3),
                    'in_stock': stock_val > 0,
                    'slug':     slugify(name),
                })

    # Right panel rows 9-129 are АВБбШв/АВБШВ → АВВГ family
    avvg_cat = ensure_cat('Кабель АВВГ, АВВГнг, АВВГнгls')

    process_panel(0, 1, 2, default_cat=None)
    process_panel(4, 5, 6, default_cat=avvg_cat)

    # deduplicate product slugs within each category
    for cat in categories.values():
        seen = {}
        for p in cat['products']:
            base = p['slug']
            if base in seen:
                seen[base] += 1
                p['slug'] = f"{base}-{seen[base]}"
            else:
                seen[base] = 0

    return categories, cat_order


# ── HTML components ────────────────────────────────────────────────────────────
TAILWIND_HEAD = """<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script id="tailwind-config">
tailwind.config = {
  darkMode:"class",
  theme:{extend:{colors:{"surface-container":"#1c2027","border-subtle":"rgba(255,255,255,0.1)","background":"#10131b","surface-container-lowest":"#0b0e15","surface-bright":"#363941","primary":"#4be277","surface-container-highest":"#31353d","surface":"#10131b","primary-container":"#22c55e","on-surface-variant":"#bccbb9","on-background":"#e0e2ed","surface-container-low":"#181c23","text-secondary":"rgba(255,255,255,0.55)","inverse-surface":"#e0e2ed","secondary":"#c3c6cf","secondary-container":"#454950","on-surface":"#e0e2ed","surface-dim":"#10131b","outline":"#869585","on-primary":"#003915","surface-container-high":"#272a32","outline-variant":"#3d4a3d","on-secondary":"#2d3137"},
  borderRadius:{"DEFAULT":"0.125rem","lg":"0.25rem","xl":"0.5rem","full":"0.75rem"},
  spacing:{"md":"24px","lg":"48px","xl":"80px","margin-desktop":"64px","sm":"16px","base":"4px","xs":"8px","margin-mobile":"16px","gutter":"24px"},
  fontFamily:{"body-md":["Space Grotesk"],"display-lg":["Space Grotesk"],"headline-md":["Space Grotesk"],"headline-lg":["Space Grotesk"],"body-lg":["Space Grotesk"],"label-sm":["Space Grotesk"]},
  fontSize:{"body-md":["16px",{"lineHeight":"1.6","fontWeight":"400"}],"display-lg":["48px",{"lineHeight":"1.1","letterSpacing":"-0.02em","fontWeight":"700"}],"headline-md":["24px",{"lineHeight":"1.3","fontWeight":"500"}],"headline-lg":["32px",{"lineHeight":"1.2","fontWeight":"600"}],"headline-lg-mobile":["24px",{"lineHeight":"1.2","fontWeight":"600"}],"body-lg":["18px",{"lineHeight":"1.6","fontWeight":"400"}],"label-sm":["12px",{"lineHeight":"1","letterSpacing":"0.05em","fontWeight":"600"}]}}}
}
</script>
<style>
body{background-color:#10131b;color:#e0e2ed;overflow-x:hidden;font-family:'Space Grotesk',sans-serif}
.glass-panel{background:rgba(13,17,23,0.7);backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,0.1)}
.glow-hover:hover{box-shadow:0 0 20px rgba(34,197,94,0.3);border-color:#4be277;transform:translateY(-2px)}
</style>"""


def nav_html(root: str) -> str:
    return f"""<nav class="fixed top-0 w-full z-50 bg-background/80 backdrop-blur-xl border-b border-subtle shadow-sm h-20 flex justify-between items-center px-margin-desktop max-w-[1440px] mx-auto left-0 right-0">
  <a href="{root}index.html" class="flex items-center gap-2 text-headline-md font-bold text-on-surface">
    <span class="material-symbols-outlined text-primary">bolt</span>
    <span class="tracking-tight uppercase">Novaris</span>
  </a>
  <div class="hidden md:flex items-center gap-lg">
    <a class="text-on-surface-variant hover:text-primary transition-colors" href="{root}catalog/index.html">Каталог</a>
    <a class="text-on-surface-variant hover:text-primary transition-colors" href="{root}about.html">О компании</a>
    <a class="text-on-surface-variant hover:text-primary transition-colors" href="{root}certificates.html">Сертификаты</a>
    <a class="text-on-surface-variant hover:text-primary transition-colors" href="{root}delivery.html">Доставка</a>
    <a class="text-on-surface-variant hover:text-primary transition-colors" href="{root}contacts.html">Контакты</a>
  </div>
  <a class="hidden lg:block px-4 py-2 border border-primary text-primary font-bold hover:bg-primary hover:text-on-primary transition-all" href="tel:+77473534241">+7 (747) 353 42 41</a>
</nav>"""


def footer_html(root: str) -> str:
    return f"""<footer class="w-full py-xl border-t border-subtle bg-surface-container-lowest">
  <div class="grid grid-cols-1 md:grid-cols-3 gap-lg px-margin-desktop max-w-[1440px] mx-auto">
    <div>
      <div class="font-bold text-primary mb-md uppercase tracking-tight text-headline-md">ТОО «Novaris LLP»</div>
      <p class="text-on-surface-variant text-body-md mb-md">Официальный дилер АО КабельПром. Поставки электрокабеля по Казахстану и СНГ.</p>
    </div>
    <div class="grid grid-cols-2 gap-md">
      <div class="flex flex-col gap-sm">
        <span class="text-label-sm uppercase text-primary mb-xs">Продукция</span>
        <a class="text-on-surface-variant hover:text-primary transition-colors" href="{root}catalog/index.html">Каталог</a>
        <a class="text-on-surface-variant hover:text-primary transition-colors" href="{root}catalog/index.html">Прайс-лист</a>
      </div>
      <div class="flex flex-col gap-sm">
        <span class="text-label-sm uppercase text-primary mb-xs">Компания</span>
        <a class="text-on-surface-variant hover:text-primary transition-colors" href="{root}about.html">О нас</a>
        <a class="text-on-surface-variant hover:text-primary transition-colors" href="{root}contacts.html">Контакты</a>
        <a class="text-on-surface-variant hover:text-primary transition-colors" href="{root}delivery.html">Доставка</a>
      </div>
    </div>
    <div>
      <span class="text-label-sm uppercase text-primary mb-md block">Контакты</span>
      <p class="text-on-surface mb-xs">+7 (747) 353 42 41</p>
      <p class="text-on-surface mb-md">info@novaris.kz</p>
      <p class="text-on-surface-variant">Республика Казахстан, г. Костанай,<br>ул. Карбышева 8/1</p>
    </div>
  </div>
  <div class="max-w-[1440px] mx-auto px-margin-desktop mt-xl pt-md border-t border-subtle flex flex-col md:flex-row justify-between text-label-sm text-on-surface-variant uppercase opacity-60">
    <span>© 2026 ТОО Novaris LLP · БИН 260540011719</span>
    <div class="flex gap-lg mt-md md:mt-0">
      <a class="hover:text-primary" href="{root}contacts.html">Политика конфиденциальности</a>
    </div>
  </div>
</footer>"""


def page_wrap(title: str, description: str, canonical: str, root: str,
              body: str, schema: dict | None = None) -> str:
    schema_tag = ""
    if schema:
        schema_tag = f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, indent=2)}</script>'
    return f"""<!DOCTYPE html>
<html class="dark" lang="ru">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-F2YHC6QKQC"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-F2YHC6QKQC');
</script>
<!-- Yandex.Metrika counter -->
<script type="text/javascript">
   (function(m,e,t,r,i,k,a){{m[i]=m[i]||function(){{(m[i].a=m[i].a||[]).push(arguments)}};
   m[i].l=1*new Date();
   for (var j = 0; j < document.scripts.length; j++) {{if (document.scripts[j].src === r) {{ return; }}}}
   k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)}})
   (window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");

   ym(110138463, "init", {{
        ssr:true,
        webvisor:true,
        clickmap:true,
        ecommerce:"dataLayer",
        accurateTrackBounce:true,
        trackLinks:true
   }});
</script>
<noscript><div><img src="https://mc.yandex.ru/watch/110138463" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
<!-- /Yandex.Metrika counter -->
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title}</title>
<meta name="description" content="{description}"/>
<meta name="robots" content="index, follow"/>
<link rel="canonical" href="{canonical}"/>
<meta property="og:type" content="website"/>
<meta property="og:title" content="{title}"/>
<meta property="og:description" content="{description}"/>
{schema_tag}
{TAILWIND_HEAD}
</head>
<body class="dark selection:bg-primary selection:text-on-primary">
{nav_html(root)}
<main class="relative z-10 pt-24 pb-xl">
{body}
</main>
{footer_html(root)}
</body>
</html>"""


# ── Page generators ────────────────────────────────────────────────────────────
def build_catalog_index(categories: dict, cat_order: list):
    cards = []
    for slug in cat_order:
        cat = categories[slug]
        n = len(cat['products'])
        in_stock = sum(1 for p in cat['products'] if p['in_stock'])
        cards.append(f"""<a href="{slug}/index.html" class="glass-panel p-lg glow-hover transition-all duration-300 block group">
  <div class="flex justify-between items-start mb-md">
    <h2 class="font-headline-md text-headline-md text-on-surface group-hover:text-primary transition-colors">{cat['name']}</h2>
    <span class="text-label-sm text-primary border border-primary px-2 py-1 ml-2 shrink-0">{n} поз.</span>
  </div>
  <span class="text-primary font-bold flex items-center gap-1 group-hover:gap-2 transition-all">
    Смотреть <span class="material-symbols-outlined text-sm">chevron_right</span>
  </span>
</a>""")

    total_products = sum(len(c['products']) for c in categories.values())
    search_form = """<form method="GET" action="search.html" class="flex gap-sm max-w-xl mb-xl">
  <input name="q" type="text" placeholder="Поиск по каталогу (напр. ВВГ 3х2.5)…"
    class="flex-1 bg-background border border-subtle focus:border-primary outline-none px-4 py-3 text-on-surface"/>
  <button type="submit" class="bg-primary text-on-primary px-lg py-3 font-bold uppercase tracking-wider hover:opacity-90 transition-all">
    Найти
  </button>
</form>"""

    body = f"""<div class="max-w-[1440px] mx-auto px-margin-desktop">
  <div class="mb-xl">
    <p class="text-label-sm text-on-surface-variant uppercase mb-xs">
      <a href="../index.html" class="hover:text-primary">Главная</a> / Каталог
    </p>
    <h1 class="font-display-lg text-display-lg mb-md">Каталог кабельной продукции</h1>
    <p class="text-on-surface-variant text-body-lg mb-lg">
      {len(cat_order)} категорий · {total_products} наименований · Официальный дилер АО КабельПром
    </p>
    {search_form}
  </div>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-md">
    {''.join(cards)}
  </div>
</div>"""

    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "Каталог кабельной продукции Novaris",
        "description": f"Каталог кабельной продукции: {len(cat_order)} категорий, {total_products} наименований.",
        "url": f"{BASE_URL}/catalog/",
        "publisher": {"@type": "Organization", "name": "ТОО Novaris LLP", "url": BASE_URL}
    }

    return page_wrap(
        title="Каталог кабельной продукции — купить в Казахстане | Новарис",
        description=f"Каталог электрокабеля: {total_products} наименований, {len(cat_order)} категорий. ТОО Novaris LLP, официальный дилер АО КабельПром. Костанай.",
        canonical=f"{BASE_URL}/catalog/",
        root="../",
        body=body,
        schema=schema,
    )


def build_category_page(cat: dict, root_prefix: str = "../../") -> str:
    slug = cat['slug']
    products = cat['products']

    rows = []
    for p in products:
        rows.append(f"""<a href="{p['slug']}.html" class="flex items-center justify-between border border-subtle hover:border-primary hover:bg-surface-container-high transition-all px-md py-sm group">
  <span class="font-body-md text-on-surface group-hover:text-primary transition-colors">{p['name']}</span>
  <span class="material-symbols-outlined text-on-surface-variant group-hover:text-primary text-sm shrink-0 ml-md">chevron_right</span>
</a>""")

    in_stock = sum(1 for p in products if p['in_stock'])
    body = f"""<div class="max-w-[1440px] mx-auto px-margin-desktop">
  <p class="text-label-sm text-on-surface-variant uppercase mb-xs">
    <a href="../../index.html" class="hover:text-primary">Главная</a> /
    <a href="../index.html" class="hover:text-primary">Каталог</a> /
    {cat['name']}
  </p>
  <div class="flex flex-col md:flex-row justify-between items-start md:items-end mb-xl gap-md">
    <div>
      <h1 class="font-display-lg text-display-lg mb-sm">{cat['name']}</h1>
      <p class="text-on-surface-variant">{len(products)} наименований</p>
    </div>
    <a href="../../contacts.html" class="border border-primary text-primary px-lg py-3 font-bold uppercase hover:bg-primary hover:text-on-primary transition-all shrink-0">
      Запросить КП
    </a>
  </div>
  <div class="flex flex-col gap-xs">
    {''.join(rows)}
  </div>
</div>"""

    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": cat['name'],
        "description": f"Поставки {cat['name']} по Казахстану. {len(products)} наименований. ТОО Novaris LLP.",
        "url": f"{BASE_URL}/catalog/{slug}/",
        "publisher": {"@type": "Organization", "name": "ТОО Novaris LLP", "url": BASE_URL}
    }

    return page_wrap(
        title=f"{cat['name']} — купить в Казахстане | Новарис",
        description=f"Поставки {cat['name']} по Казахстану. ТОО Novaris LLP, официальный дилер. Костанай. {len(products)} наименований.",
        canonical=f"{BASE_URL}/catalog/{slug}/",
        root="../../",
        body=body,
        schema=schema,
    )


def build_product_page(product: dict, cat: dict) -> str:
    cat_slug = cat['slug']
    p_slug = product['slug']
    name = product['name']
    unit = product['unit']
    stock = product['stock']
    in_stock = product['in_stock']

    availability = "InStock" if in_stock else "PreOrder"
    stock_label = "В наличии" if in_stock else "Под заказ"
    stock_class = "text-primary" if in_stock else "text-on-surface-variant"

    # Related products (3 others from same category, excluding self)
    others = [p for p in cat['products'] if p['slug'] != p_slug][:3]
    related_html = ""
    if others:
        cards = ''.join(f"""<a href="{p['slug']}.html" class="glass-panel p-md hover:border-primary transition-all block">
  <div class="font-body-md text-on-surface hover:text-primary">{p['name']}</div>
  <div class="text-label-sm text-on-surface-variant mt-xs">{p['unit']} · {'В наличии' if p['in_stock'] else 'Под заказ'}</div>
</a>""" for p in others)
        related_html = f"""<div class="mt-xl">
  <h2 class="font-headline-md text-headline-md mb-md">Похожие марки</h2>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-md">{cards}</div>
</div>"""

    body = f"""<div class="max-w-[1440px] mx-auto px-margin-desktop">
  <p class="text-label-sm text-on-surface-variant uppercase mb-xs">
    <a href="../../index.html" class="hover:text-primary">Главная</a> /
    <a href="../index.html" class="hover:text-primary">Каталог</a> /
    <a href="index.html" class="hover:text-primary">{cat['name']}</a> /
    {name}
  </p>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-lg mt-lg">
    <div class="lg:col-span-2">
      <h1 class="font-display-lg text-display-lg mb-md">{name}</h1>
      <p class="text-on-surface-variant text-body-lg mb-lg">
        Кабельно-проводниковая продукция категории «{cat['name']}».
        Поставка по всему Казахстану. Сертификаты ГОСТ.
      </p>

      <div class="glass-panel p-lg mb-lg">
        <h2 class="font-headline-md text-headline-md mb-md">Характеристики</h2>
        <table class="w-full text-body-md">
          <tbody>
            <tr class="border-b border-subtle">
              <td class="py-sm text-on-surface-variant w-1/2">Марка</td>
              <td class="py-sm font-bold text-on-surface">{name}</td>
            </tr>
            <tr class="border-b border-subtle">
              <td class="py-sm text-on-surface-variant">Категория</td>
              <td class="py-sm text-on-surface">{cat['name']}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="flex flex-col gap-md">
      <div class="glass-panel p-lg">
        <div class="text-label-sm text-on-surface-variant uppercase mb-xs">Статус</div>
        <div class="font-bold text-headline-md {stock_class} mb-md">{stock_label}</div>
        <a href="../../contacts.html" class="block w-full bg-primary text-on-primary text-center py-4 font-bold uppercase tracking-wider hover:opacity-90 transition-all mb-sm">
          Запросить КП
        </a>
        <a href="tel:+77473534241" class="block w-full border border-primary text-primary text-center py-4 font-bold uppercase tracking-wider hover:bg-primary hover:text-on-primary transition-all">
          +7 (747) 353 42 41
        </a>
      </div>
      <div class="glass-panel p-lg text-body-md text-on-surface-variant">
        <span class="material-symbols-outlined text-primary align-middle mr-xs">verified</span>
        Сертификаты ГОСТ. Официальный дилер АО КабельПром.
      </div>
    </div>
  </div>

  {related_html}
</div>"""

    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": name,
        "description": f"Кабель {name}. Категория: {cat['name']}. Поставка по Казахстану. ТОО Novaris LLP.",
        "url": f"{BASE_URL}/catalog/{cat_slug}/{p_slug}.html",
        "brand": {"@type": "Brand", "name": "КабельПром"},
        "offers": {
            "@type": "Offer",
            "availability": f"https://schema.org/{availability}",
            "priceCurrency": "KZT",
            "seller": {"@type": "Organization", "name": "ТОО Novaris LLP", "url": BASE_URL}
        }
    }

    return page_wrap(
        title=f"{name} купить в Казахстане, цена | Новарис",
        description=f"{name} — купить в Казахстане. Поставки {cat['name']} от официального дилера АО КабельПром. ТОО Novaris LLP, Костанай.",
        canonical=f"{BASE_URL}/catalog/{cat_slug}/{p_slug}.html",
        root="../../",
        body=body,
        schema=schema,
    )


# ── Sitemap ────────────────────────────────────────────────────────────────────
def build_sitemap(categories: dict, cat_order: list) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    urls = [
        f"  <url><loc>{BASE_URL}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>",
        f"  <url><loc>{BASE_URL}/catalog/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.9</priority></url>",
    ]
    for slug in cat_order:
        cat = categories[slug]
        urls.append(f"  <url><loc>{BASE_URL}/catalog/{slug}/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>")
        for p in cat['products']:
            urls.append(f"  <url><loc>{BASE_URL}/catalog/{slug}/{p['slug']}.html</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>")

    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(urls) + '\n</urlset>\n'


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("Parsing price.xls …")
    categories, cat_order = parse_xls()

    total = sum(len(c['products']) for c in categories.values())
    print(f"  {len(cat_order)} categories, {total} products")

    CATALOG_DIR.mkdir(exist_ok=True)

    # catalog/index.html
    print("Building catalog/index.html …")
    (CATALOG_DIR / "index.html").write_text(
        build_catalog_index(categories, cat_order), encoding="utf-8")

    # category and product pages
    for i, slug in enumerate(cat_order, 1):
        cat = categories[slug]
        cat_dir = CATALOG_DIR / slug
        cat_dir.mkdir(exist_ok=True)

        # category index
        (cat_dir / "index.html").write_text(
            build_category_page(cat), encoding="utf-8")

        # product pages
        for p in cat['products']:
            (cat_dir / f"{p['slug']}.html").write_text(
                build_product_page(p, cat), encoding="utf-8")

        print(f"  [{i}/{len(cat_order)}] {slug}: {len(cat['products'])} products")

    # sitemap.xml
    print("Building sitemap.xml …")
    (PROJECT_DIR / "sitemap.xml").write_text(
        build_sitemap(categories, cat_order), encoding="utf-8")

    print("\nDone.")
    print(f"  catalog/  → {sum(1 for _ in CATALOG_DIR.rglob('*.html'))} HTML files")
    print(f"  sitemap.xml → {sum(1 for _ in (PROJECT_DIR/'sitemap.xml').read_text().split('<url>')) - 1} URLs")


if __name__ == "__main__":
    main()
