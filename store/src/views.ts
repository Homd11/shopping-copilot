import type { Product, ShoeConstraints } from "./catalogue.js";

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function layout(title: string, content: string): string {
  return `<!doctype html>
<html lang="ar" dir="rtl">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(title)}</title>
  </head>
  <body>
    <header>
      <a href="/">المتجر التجريبي</a>
      <form role="search" action="/c/shoes" method="get">
        <label for="store-search">بحث المنتجات</label>
        <input id="store-search" name="q" type="search" />
      </form>
      <nav aria-label="التنقل الرئيسي">
        <a href="/cart">السلة (0)</a>
        <a href="/account">الحساب</a>
      </nav>
    </header>
    <main>${content}</main>
    <script type="module" src="/bridge/runtime.js"></script>
  </body>
</html>`;
}

export function renderHome(): string {
  return layout(
    "المتجر التجريبي",
    `<h1>تسوّق بسهولة</h1>
    <nav aria-label="الأقسام">
      <a href="/c/shoes">الأحذية</a>
    </nav>`,
  );
}

function checked(active: boolean): string {
  return active ? " checked" : "";
}

function productCard(product: Product): string {
  return `<article data-product-id="${product.id}" data-product-type="${product.type}">
    <h2>${escapeHtml(product.nameAr)}</h2>
    <p lang="en">${escapeHtml(product.nameEn)}</p>
    <p>${product.price} EGP</p>
    <p>${product.available ? "متاح" : "غير متاح"}</p>
  </article>`;
}

export function renderShoes(
  products: readonly Product[],
  constraints: ShoeConstraints,
): string {
  const minPrice = constraints.minPrice?.toString() ?? "";
  const maxPrice = constraints.maxPrice?.toString() ?? "";
  return layout(
    "الأحذية",
    `<h1>الأحذية</h1>
    <form aria-label="فلترة الأحذية" action="/c/shoes" method="get">
      <fieldset>
        <legend>نوع الحذاء</legend>
        <label><input type="radio" name="type" value="running"${checked(constraints.type === "running")} /> جري</label>
        <label><input type="radio" name="type" value="casual"${checked(constraints.type === "casual")} /> كاجوال</label>
        <label><input type="radio" name="type" value="football"${checked(constraints.type === "football")} /> كرة قدم</label>
      </fieldset>
      <label for="min-price">أقل سعر</label>
      <input id="min-price" name="min_price" inputmode="numeric" value="${minPrice}" />
      <label for="max-price">أقصى سعر</label>
      <input id="max-price" name="max_price" inputmode="numeric" value="${maxPrice}" />
      <button type="submit">تطبيق الفلاتر</button>
    </form>
    <section aria-labelledby="results-heading">
      <h2 id="results-heading">${products.length} منتجات</h2>
      ${products.map(productCard).join("\n")}
    </section>`,
  );
}
