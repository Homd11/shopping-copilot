import type {
  Category,
  Product,
  ProductConstraints,
  ShoeConstraints,
} from "./catalogue.js";
import { products } from "./catalogue.js";
import { lineKey, type CartLine } from "./guarded-cart.js";

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
    <link rel="stylesheet" href="/assets/store.css" />
  </head>
  <body>
    <div class="demo-strip">تجربة تسوّق مصرية · مشروع تخرّج · بدون دفع حقيقي</div>
    <header>
      <a class="brand" href="/" aria-label="المتجر التجريبي">المتجر التجريبي</a>
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
    <footer><strong>اختيارات ليومك، على ذوقك.</strong><p>كتالوج خيالي بأسعار بالجنيه المصري. الرسومات توضيحية، ولا تتم أي عملية دفع.</p><span lang="en">SHOPPING COPILOT / LOCAL DEMO</span></footer>
    <div id="cart-feedback" aria-live="polite"></div>
    <form id="undo-form" action="/cart/undo" method="post" data-cart-edit="undo" hidden>
      <span id="undo-description" aria-live="polite"></span>
      <button type="submit" data-testid="undo-cart" aria-describedby="undo-description">تراجع</button>
      <span id="undo-timer" aria-hidden="true"></span>
    </form>
    <script src="/assets/cart.js" defer></script>
    <script type="module" src="/bridge/runtime.js"></script>
  </body>
</html>`;
}

export function renderHome(): string {
  return layout(
    "المتجر التجريبي",
    `<section class="hero"><div class="hero-copy"><p class="eyebrow">على ذوقك · لكل يوم</p><h1>تسوّق بسهولة</h1>
    <p class="hero-description">من أول مشوار الصبح لآخر خروجة بالليل.<br>اختيارات بسيطة، وتفاصيل تفرق.</p>
    <a class="primary-link" href="/c/shoes">اكتشف الأحذية <span aria-hidden="true">←</span></a>
    <p class="hero-note">اسأل مساعد التسوّق عن اللي بتدور عليه.</p></div>
    <div class="hero-art"><span class="edition" aria-hidden="true">EVERYDAY / 01</span><img src="/assets/shoes.svg" alt="" width="640" height="480"><span class="art-caption">راحة تبدأ من أول خطوة</span></div></section>
    <div class="section-heading"><div><p class="eyebrow">ابدأ من هنا</p><h2>إيه اللي بتدور عليه؟</h2></div><span>٤ أقسام ليومك</span></div>
    <nav class="category-tiles" aria-label="الأقسام">
      ${Object.entries(categoryNames)
        .map(
          ([category, name]) =>
            `<a href="/c/${category}"><img src="/assets/${category}.svg" width="320" height="220" alt=""><span>${name.ar} <span lang="en">${name.en}</span></span></a>`,
        )
        .join("\n")}
    </nav><section class="shop-note"><p class="eyebrow">مساعدك في الاختيار</p><h2>قول لنا محتاج إيه.<br>وخد وقتك في الاختيار.</h2><p>قارن المنتجات، اختار المقاس واللون، وعدّل سلتك براحتك.<br>أي تعديل عادي تقدر تتراجع عنه خلال ١٠ ثوانٍ.</p></section>`,
  );
}

export function renderCart(
  lines: CartLine[] = [],
  revision = 0,
  error?: string,
): string {
  return layout(
    "السلة",
    `<h1>السلة</h1>
    ${error ? `<p role="alert">${escapeHtml(error)}</p>` : ""}
    <div id="cart-contents">${renderCartContents(lines, revision)}</div>
    <a href="/checkout">إتمام الشراء</a>`,
  );
}

export function renderCartContents(
  lines: CartLine[],
  revision: number,
): string {
  return lines.length === 0
    ? '<p role="status">السلة فارغة</p>'
    : `<p role="status">السلة فيها ${lines.length} منتج</p>
    <ul class="cart-lines">${lines
      .map((line) => {
        const product = products.find((item) => item.id === line.product_id);
        const name = escapeHtml(product?.nameAr ?? line.product_id);
        const fields = `<input type="hidden" name="product_id" value="${escapeHtml(line.product_id)}">
          <input type="hidden" name="size" value="${escapeHtml(line.size ?? "")}">
          <input type="hidden" name="color" value="${escapeHtml(line.color ?? "")}">`;
        return `<li data-unit-price="${product?.price.amount ?? "0"}" data-cart-line="${escapeHtml(lineKey(line))}"><img class="cart-image" src="/assets/${product?.category ?? "shoes"}.svg" width="120" height="100" alt=""><a href="/p/${line.product_id}">${name}</a>
          <p>${escapeHtml(line.size ?? "—")} / ${escapeHtml(line.color ?? "—")} · ${product?.price.amount ?? "0"} EGP</p>
          <form action="/cart/quantity" method="post" data-cart-edit="quantity">${fields}
            <label for="qty-${escapeHtml(lineKey(line))}">الكمية — ${name}</label>
            <input id="qty-${escapeHtml(lineKey(line))}" name="quantity" type="number" min="1" max="99" value="${line.quantity}" required>
            <button type="submit" data-reversible-mutation="quantity">تحديث الكمية — ${name}</button>
          </form>
          <form action="/cart/remove" method="post" data-cart-edit="remove">${fields}
            <button type="submit" data-reversible-mutation="remove">حذف المنتج — ${name}</button>
          </form></li>`;
      })
      .join(
        "",
      )}</ul><div class="cart-total"><span>الإجمالي</span><strong>${cartTotal(lines)} EGP</strong></div><p class="muted">تقدر تتراجع عن آخر تعديل خلال ١٠ ثوانٍ.</p>
    <form action="/cart/clear" method="post">
      <input type="hidden" name="cart_revision" value="${revision}" />
      <input type="hidden" name="copilot_confirmation" value="" />
      <button type="submit" data-testid="empty-cart" data-guarded-mutation="clear_cart" data-cart-revision="${revision}">إفراغ السلة</button>
    </form>`;
}

function cartTotal(lines: CartLine[]): string {
  const total = lines.reduce((sum, line) => {
    const price =
      products.find((product) => product.id === line.product_id)?.price
        .amount ?? "0";
    const [whole, fraction = ""] = price.split(".");
    return (
      sum +
      (BigInt(whole) * 100n + BigInt(fraction.padEnd(2, "0"))) *
        BigInt(line.quantity)
    );
  }, 0n);
  return `${total / 100n}.${String(total % 100n).padStart(2, "0")}`;
}

export function renderCheckout(
  lines: CartLine[] = [],
  revision = 0,
  error?: string,
): string {
  return layout(
    "إتمام الشراء",
    `<h1>إتمام الشراء</h1>
    ${error ? `<p role="alert">${escapeHtml(error)}</p>` : ""}
    <p class="checkout-notice">هذه تجربة شراء خيالية. لا تدخل بطاقة حقيقية؛ استخدم <bdi>0000 0000 0000 0000</bdi>، و<bdi>01/30</bdi>، و<bdi>000</bdi> فقط. لا تتم عملية دفع.</p>
    <div class="cart-total"><span>إجمالي الطلب الخيالي</span><strong>${cartTotal(lines)} EGP</strong></div>
    <p role="status">${lines.length === 0 ? "السلة فارغة" : `السلة فيها ${lines.length} منتج`}</p>
    <form action="/checkout/submit" method="post">
    <input type="hidden" name="cart_revision" value="${revision}" />
    <input type="hidden" name="copilot_confirmation" value="" />
    <fieldset>
      <legend>بيانات الدفع التجريبية</legend>
      <label for="card-number">رقم البطاقة</label>
      <input id="card-number" name="card_number" autocomplete="cc-number" inputmode="numeric" required />
      <label for="card-expiry">تاريخ الانتهاء</label>
      <input id="card-expiry" name="card_expiry" autocomplete="cc-exp" required />
      <label for="card-security-code">رمز الأمان</label>
      <input id="card-security-code" name="card_security_code" autocomplete="cc-csc" required />
    </fieldset>
    <button type="submit" data-testid="place-order" data-guarded-mutation="submit_checkout" data-cart-revision="${revision}" ${lines.length === 0 ? "disabled" : ""}>إتمام الطلب الخيالي</button>
    </form>`,
  );
}

export function renderOrderComplete(orderId: string): string {
  return layout(
    "تم الطلب الخيالي",
    `<h1>تم تسجيل طلب خيالي</h1><p data-testid="fictional-order-id">${escapeHtml(orderId)}</p><p>لم تتم أي عملية دفع.</p>`,
  );
}

export function renderAccount(): string {
  return layout(
    "الحساب",
    `<h1>الحساب</h1>
    <p>حساب تجريبي للتصفح المحلي.</p>
    <a href="/account/orders">الطلبات</a>`,
  );
}

export function renderLogin(nextPath: string): string {
  return layout(
    "تسجيل الدخول",
    `<h1>تسجيل الدخول</h1>
    <p>أدخل بيانات تجريبية بنفسك للمتابعة إلى الطلبات.</p>
    <form action="/login" method="post">
      <input type="hidden" name="next" value="${escapeHtml(nextPath)}" />
      <label for="username">البريد الإلكتروني</label>
      <input id="username" name="username" type="email" autocomplete="username" required />
      <label for="password">كلمة المرور</label>
      <input id="password" name="password" type="password" autocomplete="current-password" required />
      <button type="submit">متابعة</button>
    </form>`,
  );
}

export function renderOrders(): string {
  return layout(
    "الطلبات",
    `<h1>الطلبات</h1>
    <ol aria-label="سجل الطلبات">
      <li id="order-1003">
        <a href="#order-1003">أحدث طلب</a>
        <span>رقم الطلب 1003 · ٢٣ سبتمبر ٢٠٢٦</span>
      </li>
      <li id="order-1002">رقم الطلب 1002</li>
    </ol>`,
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
    <a class="product-picture" href="/p/${encodeURIComponent(product.id)}" tabindex="-1" aria-hidden="true"><img src="/assets/${product.category}.svg" width="400" height="300" loading="lazy" alt=""></a>
    <h2><a href="/p/${encodeURIComponent(product.id)}">${escapeHtml(product.nameAr)}</a></h2>
    <p lang="en">${escapeHtml(product.nameEn)}</p>
    <p class="price">${product.price.amount} ${product.price.currency}</p>
    <p class="stock ${product.available ? "available" : "unavailable"}">${product.available ? "متاح" : "غير متاح"}</p>
    <p>المقاسات: ${product.sizes.map(escapeHtml).join("، ")}</p>
    <p>الألوان: ${product.colors.map(escapeHtml).join("، ")}</p>
  </article>`;
}

export function renderProduct(product: Product): string {
  return layout(
    product.nameAr,
    `<article class="product-detail" data-product-id="${escapeHtml(product.id)}" data-product-type="${escapeHtml(product.type)}" data-product-category="${product.category}">
      <div class="product-visual"><img src="/assets/${product.category}.svg" width="640" height="480" alt=""><span>رسم توضيحي · منتج تجريبي</span></div><div class="product-info">
      <h1>${escapeHtml(product.nameAr)}</h1>
      <p lang="en">${escapeHtml(product.nameEn)}</p>
      <p class="price">${escapeHtml(product.price.amount)} ${product.price.currency}</p>
      <p class="stock ${product.available ? "available" : "unavailable"}">${product.available ? "متاح" : "غير متاح"}</p>
      <p>المقاسات: ${product.sizes.map(escapeHtml).join("، ")}</p>
      <p>الألوان: ${product.colors.map(escapeHtml).join("، ")}</p>
      ${
        product.available
          ? `<form action="/cart/items" method="post" data-cart-edit="add">
        <input type="hidden" name="product_id" value="${product.id}">
        <label for="product-size">المقاس</label><select id="product-size" name="size" required><option value="">اختر المقاس</option>${product.sizes.map((size) => `<option>${escapeHtml(size)}</option>`).join("")}</select>
        <label for="product-color">اللون</label><select id="product-color" name="color" required><option value="">اختر اللون</option>${product.colors.map((color) => `<option>${escapeHtml(color)}</option>`).join("")}</select>
        <label for="product-quantity">الكمية</label><input id="product-quantity" name="quantity" type="number" min="1" max="99" value="1" required>
        <button type="submit" data-testid="add-to-cart" data-reversible-mutation="add">أضف إلى السلة</button>
      </form>`
          : '<button type="button" data-testid="add-to-cart" disabled>غير متاح للإضافة إلى السلة</button>'
      }
      <a href="/c/${product.category}">رجوع إلى القسم</a>
    </div></article>`,
  );
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
