"use client";

import { useRef } from "react";
import Link from "next/link";
import {
  Briefcase,
  ChevronLeft,
  ChevronRight,
  Cpu,
  GraduationCap,
  HandHeart,
  HeartPulse,
  Landmark,
  Palette,
  Plane,
  Sparkles,
  Tag,
  Wrench,
} from "lucide-react";

import type { CategoryOut } from "@/lib/events-api";

const SCROLL_AMOUNT = 200;

// بر اساس slug ثابت هر دسته‌ی والد (backend/app/db/seed_categories.py) نه
// نام فارسی‌اش — تا با تغییر متن اسم دسته از هم نپاشه. هر دسته‌ی جدیدی که
// بعداً اضافه بشه و اینجا نباشه، آیکون پیش‌فرض Tag می‌گیره.
const CATEGORY_ICONS: Record<string, typeof Tag> = {
  business: Briefcase,
  technology: Cpu,
  "self-development": Sparkles,
  health: HeartPulse,
  finance: Landmark,
  "art-culture": Palette,
  education: GraduationCap,
  engineering: Wrench,
  "travel-entertainment": Plane,
  "religious-social": HandHeart,
};

export function CategoryCarousel({ categories }: { categories: CategoryOut[] }) {
  const scrollerRef = useRef<HTMLDivElement | null>(null);

  if (categories.length === 0) return null;

  return (
    <section id="tour-categories" className="flex w-full max-w-5xl flex-col gap-4 px-4">
      <h2 className="flex items-center gap-2 text-lg font-semibold">
        <span className="bg-primary h-5 w-1 rounded-full" />
        دسته‌بندی‌ها
      </h2>
      <div className="relative">
        <div
          ref={scrollerRef}
          className="flex gap-6 overflow-x-auto scroll-smooth pb-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        >
          {categories.map((category) => {
            const Icon = CATEGORY_ICONS[category.slug] ?? Tag;
            return (
              <Link
                key={category.id}
                href={`/events?category=${category.id}`}
                className="flex w-24 shrink-0 flex-col items-center gap-2 text-center"
              >
                <div className="bg-muted flex h-20 w-20 items-center justify-center overflow-hidden rounded-full transition-opacity hover:opacity-80">
                  <Icon className="text-muted-foreground h-8 w-8" />
                </div>
                <span className="line-clamp-2 text-sm font-medium">{category.name}</span>
              </Link>
            );
          })}
        </div>
        <button
          type="button"
          aria-label="نمایش دسته‌بندی‌های قبلی"
          onClick={() => scrollerRef.current?.scrollBy({ left: SCROLL_AMOUNT, behavior: "smooth" })}
          className="bg-background hover:bg-muted absolute top-1/2 right-0 z-10 -translate-y-1/2 translate-x-1/2 rounded-full border p-1.5 shadow-md"
        >
          <ChevronRight className="size-4" />
        </button>
        <button
          type="button"
          aria-label="نمایش دسته‌بندی‌های بعدی"
          onClick={() => scrollerRef.current?.scrollBy({ left: -SCROLL_AMOUNT, behavior: "smooth" })}
          className="bg-background hover:bg-muted absolute top-1/2 left-0 z-10 -translate-y-1/2 -translate-x-1/2 rounded-full border p-1.5 shadow-md"
        >
          <ChevronLeft className="size-4" />
        </button>
      </div>
    </section>
  );
}

export default CategoryCarousel;
