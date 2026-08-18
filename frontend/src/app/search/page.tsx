import Link from "next/link";
import type { Metadata } from "next";

import { EventCard } from "@/components/EventCard";
import { SearchQueryTracker } from "@/components/SearchQueryTracker";
import { searchServer } from "@/lib/search-server";

type Props = { searchParams: Promise<{ q?: string }> };

export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const { q } = await searchParams;
  return { title: q ? `جستجوی «${q}» | رویا ایونت` : "جستجو | رویا ایونت" };
}

export default async function SearchPage({ searchParams }: Props) {
  const { q } = await searchParams;

  if (!q?.trim()) {
    return (
      <div className="mx-auto max-w-xl px-4 py-10 text-center">
        <p className="text-muted-foreground">برای جستجو، عبارتی رو تو نوار بالا وارد کنید.</p>
      </div>
    );
  }

  const result = await searchServer.search(q);
  const isEmpty = result.people.length === 0 && result.events.length === 0;

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-8">
      <SearchQueryTracker query={q} resultCount={result.events.length} />
      <h1 className="text-2xl font-bold">نتایج جستجو برای «{q}»</h1>

      {isEmpty && (
        <p className="text-muted-foreground">چیزی برای «{q}» پیدا نشد — عبارت دیگه‌ای امتحان کنید.</p>
      )}

      {result.people.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-semibold">افراد</h2>
          <div className="flex flex-wrap gap-3">
            {result.people.map((person) =>
              person.type === "instructor" ? (
                <Link
                  key={`instructor-${person.id}`}
                  href={`/instructors/${person.id}`}
                  className="hover:bg-muted flex items-center gap-2 rounded-full border px-3 py-2 transition-colors"
                >
                  <div className="bg-muted flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-full">
                    {person.avatar_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={person.avatar_url}
                        alt={person.name}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <span className="text-muted-foreground text-xs">{person.name.charAt(0)}</span>
                    )}
                  </div>
                  <span className="text-sm font-medium">{person.name}</span>
                  <span className="text-muted-foreground text-xs">مدرس</span>
                </Link>
              ) : (
                <div
                  key={`organizer-${person.id}`}
                  className="flex items-center gap-2 rounded-full border px-3 py-2"
                >
                  <span className="text-sm font-medium">{person.name}</span>
                  <span className="text-muted-foreground text-xs">برگزارکننده</span>
                </div>
              ),
            )}
          </div>
        </section>
      )}

      {result.events.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-semibold">رویدادها</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
            {result.events.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
