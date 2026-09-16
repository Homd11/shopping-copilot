export interface Product {
  id: string;
  nameAr: string;
  nameEn: string;
  type: "running" | "casual" | "football";
  price: number;
  available: boolean;
}

export const shoes: readonly Product[] = [
  {
    id: "shoe-01",
    nameAr: "عدّاء النيل",
    nameEn: "Nile Runner",
    type: "running",
    price: 1450,
    available: true,
  },
  {
    id: "shoe-02",
    nameAr: "خطوة سريعة",
    nameEn: "Quick Step",
    type: "running",
    price: 1750,
    available: true,
  },
  {
    id: "shoe-03",
    nameAr: "نسمة الصباح",
    nameEn: "Morning Breeze",
    type: "running",
    price: 2000,
    available: true,
  },
  {
    id: "shoe-04",
    nameAr: "ماراثون القاهرة",
    nameEn: "Cairo Marathon",
    type: "running",
    price: 2450,
    available: true,
  },
  {
    id: "shoe-05",
    nameAr: "جري الصحراء",
    nameEn: "Desert Run",
    type: "running",
    price: 2800,
    available: false,
  },
  {
    id: "shoe-06",
    nameAr: "مشوار وسط البلد",
    nameEn: "Downtown Walk",
    type: "casual",
    price: 1200,
    available: true,
  },
  {
    id: "shoe-07",
    nameAr: "راحة يومية",
    nameEn: "Daily Comfort",
    type: "casual",
    price: 1350,
    available: true,
  },
  {
    id: "shoe-08",
    nameAr: "كلاسيك إسكندرية",
    nameEn: "Alex Classic",
    type: "casual",
    price: 1550,
    available: true,
  },
  {
    id: "shoe-09",
    nameAr: "ممشى النيل",
    nameEn: "Nile Walk",
    type: "casual",
    price: 1850,
    available: true,
  },
  {
    id: "shoe-10",
    nameAr: "ويك إند",
    nameEn: "Weekend",
    type: "casual",
    price: 2200,
    available: true,
  },
  {
    id: "shoe-11",
    nameAr: "هداف",
    nameEn: "Striker",
    type: "football",
    price: 1650,
    available: true,
  },
  {
    id: "shoe-12",
    nameAr: "ملعب النجوم",
    nameEn: "Star Pitch",
    type: "football",
    price: 1950,
    available: true,
  },
  {
    id: "shoe-13",
    nameAr: "صانع اللعب",
    nameEn: "Playmaker",
    type: "football",
    price: 2300,
    available: true,
  },
  {
    id: "shoe-14",
    nameAr: "حارس",
    nameEn: "Keeper",
    type: "football",
    price: 2600,
    available: true,
  },
  {
    id: "shoe-15",
    nameAr: "بطولة",
    nameEn: "Championship",
    type: "football",
    price: 3100,
    available: false,
  },
];

export interface ShoeConstraints {
  type?: Product["type"];
  minPrice?: number;
  maxPrice?: number;
}

export function filterShoes(constraints: ShoeConstraints): Product[] {
  return shoes.filter((product) => {
    if (constraints.type !== undefined && product.type !== constraints.type)
      return false;
    if (
      constraints.minPrice !== undefined &&
      product.price < constraints.minPrice
    )
      return false;
    if (
      constraints.maxPrice !== undefined &&
      product.price > constraints.maxPrice
    )
      return false;
    return true;
  });
}
