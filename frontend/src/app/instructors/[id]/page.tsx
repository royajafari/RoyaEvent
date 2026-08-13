import { notFound } from "next/navigation";
import type { Metadata } from "next";

import { EventCard } from "@/components/EventCard";
import { FollowInstructorButton } from "@/components/FollowInstructorButton";
import { Separator } from "@/components/ui/separator";
import { instructorsServer } from "@/lib/instructors-server";

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const instructor = await instructorsServer.getById(Number(id));
  if (!instructor) return { title: "مدرس یافت نشد" };
  return { title: `${instructor.name} | رویا ایونت` };
}

export default async function InstructorDetailPage({ params }: Props) {
  const { id } = await params;
  const instructor = await instructorsServer.getById(Number(id));
  if (!instructor) notFound();

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 px-4 py-8">
      <div className="flex flex-wrap items-center gap-4">
        <div className="bg-muted flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-full">
          {instructor.avatar_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={instructor.avatar_url}
              alt={instructor.name}
              className="h-full w-full object-cover"
            />
          ) : (
            <span className="text-muted-foreground text-2xl">{instructor.name.charAt(0)}</span>
          )}
        </div>
        <div className="flex min-w-0 flex-col gap-1">
          <h1 className="text-2xl font-bold sm:text-3xl">{instructor.name}</h1>
          <span className="text-muted-foreground text-sm">
            {instructor.follower_count.toLocaleString("fa-IR")} دنبال‌کننده
          </span>
        </div>
        <div className="sm:mr-auto">
          <FollowInstructorButton instructorId={instructor.id} />
        </div>
      </div>

      {instructor.bio && (
        <>
          <Separator />
          <p className="leading-relaxed whitespace-pre-wrap">{instructor.bio}</p>
        </>
      )}

      <Separator />

      <section className="flex flex-col gap-4">
        <h2 className="text-lg font-semibold">رویدادهای این مدرس</h2>
        {instructor.events.length === 0 ? (
          <p className="text-muted-foreground text-sm">فعلاً رویداد منتشرشده‌ای از این مدرس نیست.</p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
            {instructor.events.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
