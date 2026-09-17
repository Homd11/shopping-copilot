import type {
  Category,
  Product,
  ProductConstraints,
  ShoeConstraints,
} from "./catalogue.js";

const categoryNames: Record<Category, { ar: string; en: string }> = {
  shoes: { ar: "الأحذية", en: "Shoes" },
  clothing: { ar: "الملابس", en: "Clothing" },
  bags: { ar: "الشنط", en: "Bags" },
  electronics: { ar: "الإلكترونيات", en: "Electronics" },
};

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
      ${Object.entries(categoryNames)
        .map(
          ([category, name]) =>
            `<a href="/c/${category}">${name.ar} <span lang="en">${name.en}</span></a>`,
        )
        .join("\n")}
    </nav>`,
  );
}

function checked(active: boolean): string {
  return active ? " checked" : "";
}

function selected(active: boolean): string {
  return active ? " selected" : "";
}

function productCard(product: Product): string {
  return `<article data-product-id="${product.id}" data-product-type="${escapeHtml(product.type)}" data-product-category="${product.category}">
    <h2>${escapeHtml(product.nameAr)}</h2>
    <p lang="en">${escapeHtml(product.nameEn)}</p>
    <p>${product.price.amount} ${product.price.currency}</p>
    <p>${product.available ? "متاح" : "غير متاح"}</p>
    <p>المقاسات: ${product.sizes.map(escapeHtml).join("، ")}</p>
    <p>الألوان: ${product.colors.map(escapeHtml).join("، ")}</p>
  </article>`;
}

function emptyState(constraints: ProductConstraints): string {
  const relaxation =
    constraints.color !== undefined
      ? "اللون"
      : constraints.size !== undefined
        ? "المقاس"
        : constraints.maxPrice !== undefined ||
            constraints.minPrice !== undefined
          ? "السعر"
          : constraints.type !== undefined
            ? "النوع"
            : constraints.query !== undefined
              ? "البحث"
              : "التوفر";
  return `<p role="status">لا توجد منتجات مطابقة. جرّب إزالة فلتر ${relaxation}.</p>`;
}

function shoeTypeControls(constraints: ProductConstraints): string {
  if (constraints.category !== "shoes") {
    return `<label for="product-type">النوع</label>
      <input id="product-type" name="type" value="${escapeHtml(constraints.type ?? "")}" />`;
  }
  return `<fieldset>
        <legend>نوع الحذاء</legend>
        <label><input type="radio" name="type" value="running"${checked(constraints.type === "running")} /> جري</label>
        <label><input type="radio" name="type" value="casual"${checked(constraints.type === "casual")} /> كاجوال</label>
        <label><input type="radio" name="type" value="football"${checked(constraints.type === "football")} /> كرة قدم</label>
      </fieldset>`;
}

export function renderCategory(
  matchingProducts: readonly Product[],
  constraints: ProductConstraints,
): string {
  const name = categoryNames[constraints.category];
  const query = escapeHtml(constraints.query ?? "");
  const minPrice = constraints.minPrice?.amount ?? "";
  const maxPrice = constraints.maxPrice?.amount ?? "";
  const size = escapeHtml(constraints.size ?? "");
  const color = escapeHtml(constraints.color ?? "");
  return layout(
    name.ar,
    `<h1>${name.ar} <span lang="en">${name.en}</span></h1>
    <form aria-label="فلترة ${name.ar}" action="/c/${constraints.category}" method="get">
      <label for="category-search">بحث</label>
      <input id="category-search" name="q" type="search" value="${query}" />
      ${shoeTypeControls(constraints)}
      <label for="min-price">أقل سعر</label>
      <input id="min-price" name="min_price" inputmode="decimal" value="${minPrice}" />
      <label for="max-price">أقصى سعر</label>
      <input id="max-price" name="max_price" inputmode="decimal" value="${maxPrice}" />
      <label for="size">المقاس</label>
      <input id="size" name="size" value="${size}" />
      <label for="color">اللون</label>
      <input id="color" name="color" value="${color}" />
      <label for="availability">التوفر</label>
      <select id="availability" name="availability">
        <option value="">الكل</option>
        <option value="available"${selected(constraints.availability === true)}>متاح</option>
        <option value="unavailable"${selected(constraints.availability === false)}>غير متاح</option>
      </select>
      <label for="sort">الترتيب</label>
      <select id="sort" name="sort">
        <option value="">الافتراضي</option>
        <option value="cheapest"${selected(constraints.sort === "cheapest")}>الأرخص</option>
        <option value="newest"${selected(constraints.sort === "newest")}>الأحدث</option>
      </select>
      <button type="submit">تطبيق الفلاتر</button>
    </form>
    <section aria-labelledby="results-heading">
      <h2 id="results-heading">${matchingProducts.length} منتجات</h2>
      ${matchingProducts.length === 0 ? emptyState(constraints) : matchingProducts.map(productCard).join("\n")}
    </section>`,
  );
}

export function renderShoes(
  matchingProducts: readonly Product[],
  constraints: ShoeConstraints,
): string {
  return renderCategory(matchingProducts, {
    category: "shoes",
    ...constraints,
  });
}
