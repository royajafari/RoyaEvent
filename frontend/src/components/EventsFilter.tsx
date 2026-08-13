"use client";

import { useRouter, useSearchParams } from "next/navigation";

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { CategoryOut } from "@/lib/events-api";

const FORMAT_LABELS: Record<string, string> = {
  online: "آنلاین",
  in_person: "حضوری",
  hybrid: "ترکیبی",
};

function groupCategories(categories: CategoryOut[]) {
  const parents = categories.filter((c) => c.parent_id === null);
  return parents.map((parent) => ({
    parent,
    children: categories.filter((c) => c.parent_id === parent.id),
  }));
}

export function EventsFilter({ categories }: { categories: CategoryOut[] }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const categoryId = searchParams.get("category") ?? "";
  const format = searchParams.get("format") ?? "";

  function updateParam(key: string, value: string | null) {
    const params = new URLSearchParams(searchParams.toString());
    if (value && value !== "all") params.set(key, value);
    else params.delete(key);
    router.push(`/events${params.toString() ? `?${params.toString()}` : ""}`);
  }

  const categoryLabels: Record<string, string> = {};
  for (const c of categories) categoryLabels[String(c.id)] = c.name;

  return (
    <div className="flex flex-wrap gap-2">
      <Select value={categoryId} onValueChange={(v) => updateParam("category", v)}>
        <SelectTrigger className="w-44">
          <SelectValue placeholder="همه‌ی دسته‌بندی‌ها">
            {(value: string | null) => (value ? (categoryLabels[value] ?? value) : "همه‌ی دسته‌بندی‌ها")}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">همه‌ی دسته‌بندی‌ها</SelectItem>
          {groupCategories(categories).map(({ parent, children }) => (
            <SelectGroup key={parent.id}>
              <SelectLabel>{parent.name}</SelectLabel>
              {children.map((child) => (
                <SelectItem key={child.id} value={String(child.id)}>
                  {child.name}
                </SelectItem>
              ))}
            </SelectGroup>
          ))}
        </SelectContent>
      </Select>

      <Select value={format} onValueChange={(v) => updateParam("format", v)}>
        <SelectTrigger className="w-36">
          <SelectValue placeholder="همه‌ی نوع‌ها">
            {(value: string | null) => (value ? (FORMAT_LABELS[value] ?? value) : "همه‌ی نوع‌ها")}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">همه‌ی نوع‌ها</SelectItem>
          <SelectItem value="online">آنلاین</SelectItem>
          <SelectItem value="in_person">حضوری</SelectItem>
          <SelectItem value="hybrid">ترکیبی</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}

export default EventsFilter;
