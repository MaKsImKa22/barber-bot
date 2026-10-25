"""Збирає сайт барбершопу в docs/: головну, сторінки послуг і sitemap.xml.

Усі дані бізнесу (назва, адреса, телефон, графік, ціни) лежать в одному місці — BUSINESS і SERVICES,
тому на всіх сторінках і в розмітці Schema.org вони однакові. Для локального SEO це важливо (NAP).

Запуск: python tools/build_site.py
"""

import json
from html import escape
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
SITE = "https://maksimka22.github.io/barber-bot/"
BOT = "https://t.me/barrrber_bot"

BUSINESS = {
    "name": "Барбершоп «Бритва»",
    "city": "Луцьк",
    "city_loc": "Луцьку",  # місцевий відмінок: «у Луцьку»
    "city_gen": "Луцька",  # родовий відмінок: «у центрі Луцька»
    "region": "Волинська область",
    "street": "вул. Прикладна, 1",
    "postal": "43000",
    "phone": "+380 00 000 00 00",
    "hours_text": "Пн–Сб 10:00–19:00, неділя — вихідний",
    "opens": "10:00",
    "closes": "19:00",
    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
}

SERVICES = [
    {
        "slug": "cholovicha-stryzhka",
        "name": "Чоловіча стрижка",
        "price": 400,
        "minutes": 60,
        "short": "Консультація, стрижка машинкою та ножицями, миття й укладка.",
        "lead": "Класична або сучасна стрижка під форму обличчя й тип волосся. Миття голови й укладка вже в ціні.",
        "includes": [
            "консультація: підбираємо форму під тип волосся й обличчя;",
            "стрижка машинкою та ножицями, плавні переходи (fade) за бажанням;",
            "миття голови до й після стрижки;",
            "укладка й поради, як підтримувати форму вдома.",
        ],
        "for_whom": "Підходить, якщо хочете оновити звичну стрижку або спробувати щось нове. Форму варто освіжати раз на 3–4 тижні.",
        "faq": [
            ("Скільки триває чоловіча стрижка?", "Близько 60 хвилин разом із миттям голови й укладкою."),
            ("Чи можна прийти зі своїм фото-прикладом?", "Так, покажіть фото майстру — він скаже, чи підійде така форма вашому волоссю."),
        ],
    },
    {
        "slug": "stryzhka-borody",
        "name": "Стрижка бороди",
        "price": 250,
        "minutes": 40,
        "short": "Форма, контур небезпечною бритвою, догляд олією.",
        "lead": "Оформлення бороди й вусів: форма під обличчя, чіткий контур небезпечною бритвою, гарячий рушник і олія для догляду.",
        "includes": [
            "підбір форми бороди під тип обличчя;",
            "стрижка машинкою та ножицями;",
            "контур небезпечною бритвою з гарячим рушником;",
            "олія або бальзам для догляду.",
        ],
        "for_whom": "Для тих, хто відрощує бороду або хоче повернути їй акуратну форму. Корекцію радимо раз на 2–3 тижні.",
        "faq": [
            ("Чи можна оформити бороду, якщо вона ще коротка?", "Так, навіть щетину можна оформити: майстер задасть контур, щоб борода росла рівно."),
            ("Чим відрізняється від гоління вдома?", "Майстер підбирає форму під обличчя й робить чистий контур бритвою — вдома так рівно зробити складно."),
        ],
    },
    {
        "slug": "stryzhka-i-boroda",
        "name": "Стрижка + борода",
        "price": 600,
        "minutes": 90,
        "short": "Повний образ: стрижка, моделювання бороди, гарячий рушник.",
        "lead": "Комплекс за півтори години: стрижка та оформлення бороди в одному стилі. Вигідніше, ніж замовляти окремо.",
        "includes": [
            "консультація і підбір образу;",
            "чоловіча стрижка з миттям голови й укладкою;",
            "моделювання бороди, контур небезпечною бритвою;",
            "гарячий рушник і догляд олією.",
        ],
        "for_whom": "Найпопулярніша послуга: підходить перед важливою подією або коли хочеться оновити образ повністю. Економія 50 грн порівняно з окремими послугами.",
        "faq": [
            ("Скільки триває комплекс?", "Близько 90 хвилин."),
            ("Чи можна записатися вдвох?", "Так, оберіть у боті два сусідні вільні слоти або напишіть нам — підберемо час."),
        ],
    },
]

HOME_FAQ = [
    (
        f"Скільки коштує чоловіча стрижка в {BUSINESS['city_loc']}?",
        "У «Бритві» чоловіча стрижка коштує 400 грн, стрижка бороди — 250 грн, комплекс «стрижка + борода» — 600 грн. Миття голови й укладка вже входять у ціну.",
    ),
    (
        "Як записатися до барбера?",
        "Через Telegram-бот @barrrber_bot: оберіть послугу, день і вільний час — запис займає близько 30 секунд, підтвердження приходить одразу в чат.",
    ),
    (
        "Де знаходиться барбершоп?",
        f"{BUSINESS['city']}, {BUSINESS['street']}. Графік: {BUSINESS['hours_text']}.",
    ),
    ("Чи можна оплатити карткою?", "Так, приймаємо готівку й картки."),
]


def url(path=""):
    return SITE + path


def jsonld(data):
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def business_schema():
    b = BUSINESS
    return {
        "@type": "HairSalon",
        "@id": url("#barbershop"),
        "name": b["name"],
        "description": f"Барбершоп у {b['city_loc']}: чоловічі стрижки, стрижка бороди, запис онлайн у Telegram.",
        "url": url(),
        "image": url("og.jpg"),
        "telephone": b["phone"].replace(" ", ""),
        "priceRange": f"{min(s['price'] for s in SERVICES)}–{max(s['price'] for s in SERVICES)} грн",
        "currenciesAccepted": "UAH",
        "paymentAccepted": "Готівка, картка",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": b["street"],
            "addressLocality": b["city"],
            "addressRegion": b["region"],
            "postalCode": b["postal"],
            "addressCountry": "UA",
        },
        "areaServed": {"@type": "City", "name": b["city"]},
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": b["days"], "opens": b["opens"], "closes": b["closes"]}
        ],
        "sameAs": [BOT],
        "potentialAction": {"@type": "ReserveAction", "name": "Записатися в Telegram", "target": BOT},
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "Послуги барбершопу",
            "itemListElement": [
                {
                    "@type": "Offer",
                    "price": str(s["price"]),
                    "priceCurrency": "UAH",
                    "itemOffered": {"@type": "Service", "name": s["name"], "url": url(f"posluhy/{s['slug']}/")},
                }
                for s in SERVICES
            ],
        },
    }


def faq_schema(items):
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items
        ],
    }


def faq_html(items):
    return "\n".join(
        f"          <details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>" for q, a in items
    )


ICONS = """  <svg width="0" height="0" style="position:absolute" aria-hidden="true">
    <symbol id="i-tg" viewBox="0 0 24 24"><path fill="currentColor" d="M21.9 4.3 18.7 19.4c-.2 1-.9 1.3-1.7.8l-4.9-3.6-2.4 2.3c-.3.3-.5.5-1 .5l.3-5 9.2-8.3c.4-.4-.1-.6-.6-.2L6.2 13.1l-4.9-1.5c-1-.3-1.1-1 .2-1.5L20.6 2.8c.9-.3 1.6.2 1.3 1.5z"/></symbol>
    <symbol id="i-razor" viewBox="0 0 32 32"><path d="M6 26 26 6M12 6h14v14" stroke="currentColor" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/></symbol>
  </svg>"""

# Шрифти вантажаться без блокування першого відображення: спершу текст системним шрифтом, потім підміна.
FONTS = "https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap"

FAVICON = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%23141210'/%3E%3Cpath d='M9 23 23 9M13 9h10v10' stroke='%23c9a46a' stroke-width='3' fill='none' stroke-linecap='round'/%3E%3C/svg%3E"


def tg_button(text="Записатися в Telegram", cls="btn btn-primary"):
    return (
        f'<a class="{cls}" href="{BOT}" target="_blank" rel="noopener">\n'
        f'            <svg aria-hidden="true"><use href="#i-tg"/></svg>\n'
        f"            {escape(text)}\n"
        f"          </a>"
    )


def page(*, path, title, description, root, schema, body):
    canonical = url(path)
    return f"""<!doctype html>
<html lang="uk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="uk_UA">
  <meta property="og:site_name" content="{escape(BUSINESS['name'])}">
  <meta property="og:title" content="{escape(title)}">
  <meta property="og:description" content="{escape(description)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{url('og.jpg')}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="{FAVICON}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preload" as="style" href="{FONTS}" onload="this.onload=null;this.rel='stylesheet'">
  <noscript><link rel="stylesheet" href="{FONTS}"></noscript>
  <link rel="stylesheet" href="{root}style.css">
  {jsonld({"@context": "https://schema.org", "@graph": schema})}
</head>
<body>

{ICONS}

  <header class="header">
    <div class="wrap">
      <a class="logo" href="{root}" aria-label="{escape(BUSINESS['name'])}, головна">
        <svg aria-hidden="true"><use href="#i-razor" style="color: var(--accent)"/></svg>
        БРИТВА
      </a>
      <nav class="nav" aria-label="Розділи">
        <a href="{root}#services">Послуги</a>
        <a href="{root}#faq">Питання</a>
        <a href="{root}#contacts">Контакти</a>
      </nav>
      <a class="btn btn-primary" href="{BOT}" target="_blank" rel="noopener">Записатися</a>
    </div>
  </header>

  <main id="top">
{body}
  </main>

  <footer class="footer">
    <div class="wrap">
      <span>© {escape(BUSINESS['name'])} · {escape(BUSINESS['city'])}, {escape(BUSINESS['street'])} · {escape(BUSINESS['phone'])}</span>
      <span>Демо-проєкт для портфоліо · сайт + Telegram-бот</span>
    </div>
  </footer>

  <div class="mobile-cta">
    {tg_button()}
  </div>

</body>
</html>
"""


def home():
    b = BUSINESS
    cards = []
    for s in SERVICES:
        featured = s["slug"] == "stryzhka-i-boroda"
        cards.append(
            f"""          <article class="price{' featured' if featured else ''}">
            {'<span class="price-tag">Найпопулярніше</span>' if featured else ''}
            <h3><a href="posluhy/{s['slug']}/">{escape(s['name'])}</a></h3>
            <p>{escape(s['short'])}</p>
            <div class="price-row"><b>{s['price']} грн</b><span>~ {s['minutes']} хв</span></div>
            <a class="price-more" href="posluhy/{s['slug']}/">Що входить і ціна →</a>
            {tg_button('Записатися', 'btn btn-primary' if featured else 'btn btn-ghost')}
          </article>"""
        )

    body = f"""    <section class="hero">
      <div class="wrap">
        <div>
          <span class="eyebrow">Барбершоп · {escape(b['city'])}</span>
          <h1>Барбершоп у {escape(b['city_loc'])}: стрижка, після якої <em>хочеться повернутися</em></h1>
          <p class="hero-lead">Класичні та сучасні чоловічі стрижки й оформлення бороди в центрі {escape(b['city_gen'])}. Без черг і дзвінків: обирай зручний час прямо в Telegram.</p>
          <div class="hero-actions">
            {tg_button()}
            <a class="btn btn-ghost" href="#services">Подивитися ціни</a>
          </div>
          <p class="hero-note">Запис за 30 секунд · Підтвердження одразу в чаті</p>
        </div>

        <div class="pole" aria-hidden="true">
          <svg class="pole-mark"><use href="#i-razor"/></svg>
          <div class="pole-card">
            <div><b>Пн–Сб</b><span>робочі дні</span></div>
            <div><b>10–19</b><span>години роботи</span></div>
            <div><b>30 с</b><span>на запис</span></div>
          </div>
        </div>
      </div>
    </section>

    <section class="section" id="how">
      <div class="wrap">
        <div class="section-head">
          <span class="eyebrow">Як записатися</span>
          <h2>Три кроки в Telegram</h2>
          <p>Наш бот показує тільки вільний час, тож двічі на одне місце записатися неможливо.</p>
        </div>
        <div class="steps">
          <div class="step">
            <h3>Обери послугу</h3>
            <p>Стрижка, борода або комплекс — ціни видно одразу.</p>
          </div>
          <div class="step">
            <h3>Обери день і час</h3>
            <p>Бот покаже вільні вікна на тиждень уперед.</p>
          </div>
          <div class="step">
            <h3>Підтверди запис</h3>
            <p>Залиш номер однією кнопкою. Скасувати можна будь-коли в боті.</p>
          </div>
        </div>
      </div>
    </section>

    <section class="section services" id="services">
      <div class="wrap">
        <div class="section-head">
          <span class="eyebrow">Послуги та ціни</span>
          <h2>Ціни на стрижку в барбершопі</h2>
          <p>Миття голови, укладка та гарячий рушник входять у вартість. Без прихованих доплат.</p>
        </div>
        <div class="price-list">
{chr(10).join(cards)}
        </div>
      </div>
    </section>

    <section class="section" id="why">
      <div class="wrap">
        <div class="section-head">
          <span class="eyebrow">Чому ми</span>
          <h2>Приходять раз — лишаються надовго</h2>
        </div>
        <div class="features">
          <div class="feature">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>
            <h3>Без очікування</h3>
            <p>Приходиш у свій час — крісло вже чекає.</p>
          </div>
          <div class="feature">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.4 6.8 19.1l1-5.8L3.5 9.2l5.9-.9z"/></svg>
            <h3>Досвідчені майстри</h3>
            <p>Кожен барбер має від 3 років практики.</p>
          </div>
          <div class="feature">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3c3 3.5 5 6.3 5 9a5 5 0 0 1-10 0c0-2.7 2-5.5 5-9z"/></svg>
            <h3>Чисто й стерильно</h3>
            <p>Інструменти проходять обробку після кожного клієнта.</p>
          </div>
          <div class="feature">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l4 4L19 6"/></svg>
            <h3>Чесні ціни</h3>
            <p>Ціна з прайсу — це ціна, яку ти заплатиш.</p>
          </div>
        </div>
      </div>
    </section>

    <section class="section services" id="faq">
      <div class="wrap">
        <div class="section-head">
          <span class="eyebrow">Питання</span>
          <h2>Часті питання</h2>
        </div>
        <div class="faq">
{faq_html(HOME_FAQ)}
        </div>
      </div>
    </section>

    <section class="section" id="contacts">
      <div class="wrap">
        <div class="section-head">
          <span class="eyebrow">Контакти</span>
          <h2>Барбершоп «Бритва» у {escape(b['city_loc'])}</h2>
        </div>
        <div class="contact-grid">
          <div class="panel">
            <h3>Графік роботи</h3>
            <ul class="hours">
              <li><span>Понеділок – П'ятниця</span><span>10:00 – 19:00</span></li>
              <li><span>Субота</span><span>10:00 – 19:00</span></li>
              <li class="off"><span>Неділя</span><span>вихідний</span></li>
            </ul>
          </div>
          <div class="panel">
            <h3>Як нас знайти</h3>
            <div class="contacts">
              <div><span>Адреса</span>{escape(b['city'])}, {escape(b['street'])}</div>
              <div><span>Телефон</span><a href="tel:{b['phone'].replace(' ', '')}">{escape(b['phone'])}</a></div>
              <div><span>Telegram</span><a href="{BOT}" target="_blank" rel="noopener">@barrrber_bot</a></div>
              <div><span>Оплата</span>Готівка або картка</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="cta">
      <div class="wrap">
        <span class="eyebrow">Готовий оновити образ?</span>
        <h2>Вільні місця на цей тиждень ще є</h2>
        <p>Обери зручний час у Telegram — це займе менше хвилини.</p>
        {tg_button()}
      </div>
    </section>"""

    return page(
        path="",
        title=f"Барбершоп у {b['city_loc']} «Бритва» — стрижка від 400 грн, запис онлайн",
        description=f"Барбершоп «Бритва» у {b['city_loc']}: чоловіча стрижка 400 грн, борода 250 грн, комплекс 600 грн. Запис за 30 секунд у Telegram. Пн–Сб 10:00–19:00.",
        root="",
        schema=[business_schema(), faq_schema(HOME_FAQ)],
        body=body,
    )


def service_page(s):
    b = BUSINESS
    path = f"posluhy/{s['slug']}/"
    others = "\n".join(
        f'              <li><a href="../{o["slug"]}/">{escape(o["name"])} — {o["price"]} грн</a></li>' for o in SERVICES if o is not s
    )
    includes = "\n".join(f"              <li>{escape(i)}</li>" for i in s["includes"])
    schema = [
        {
            "@type": "Service",
            "name": s["name"],
            "serviceType": s["name"],
            "url": url(path),
            "provider": {"@id": url("#barbershop")},
            "areaServed": {"@type": "City", "name": b["city"]},
            "offers": {"@type": "Offer", "price": str(s["price"]), "priceCurrency": "UAH"},
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Головна", "item": url()},
                {"@type": "ListItem", "position": 2, "name": "Послуги", "item": url("#services")},
                {"@type": "ListItem", "position": 3, "name": s["name"], "item": url(path)},
            ],
        },
        faq_schema(s["faq"]),
    ]
    body = f"""    <section class="page-hero">
      <div class="wrap">
        <nav class="breadcrumbs" aria-label="Хлібні крихти"><a href="../../">Головна</a> / <a href="../../#services">Послуги</a> / <span aria-current="page">{escape(s['name'])}</span></nav>
        <span class="eyebrow">Барбершоп «Бритва» · {escape(b['city'])}</span>
        <h1>{escape(s['name'])} в {escape(b['city_loc'])}</h1>
        <p class="hero-lead">{escape(s['lead'])}</p>
      </div>
    </section>

    <div class="wrap page-layout">
      <article class="content">
        <h2>Що входить</h2>
        <ul>
{includes}
        </ul>

        <h2>Кому підходить</h2>
        <p>{escape(s['for_whom'])}</p>

        <h2>Питання про послугу</h2>
        <div class="faq">
{faq_html(s['faq'])}
        </div>

        <h2>Інші послуги</h2>
        <ul class="other-services">
{others}
        </ul>
      </article>

      <aside class="aside price">
        <span class="eyebrow">Вартість</span>
        <div class="price-row"><b>{s['price']} грн</b><span>~ {s['minutes']} хв</span></div>
        {tg_button()}
        <p class="aside-note">{escape(b['city'])}, {escape(b['street'])}<br>{escape(b['hours_text'])}</p>
      </aside>
    </div>"""
    return page(
        path=path,
        title=f"{s['name']} в {b['city_loc']} — {s['price']} грн | {b['name']}",
        description=f"{s['name']} в барбершопі «Бритва», {b['city']}: {s['price']} грн, близько {s['minutes']} хв. {s['short']} Запис онлайн у Telegram.",
        root="../../",
        schema=[business_schema(), *schema],
        body=body,
    )


def sitemap():
    urls = [url()] + [url(f"posluhy/{s['slug']}/") for s in SERVICES]
    items = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}\n</urlset>\n'


def main():
    (DOCS / "index.html").write_text(home(), encoding="utf-8")
    for s in SERVICES:
        target = DOCS / "posluhy" / s["slug"] / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(service_page(s), encoding="utf-8")
    (DOCS / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    print("Готово:", 1 + len(SERVICES), "сторінки + sitemap.xml")


if __name__ == "__main__":
    main()
