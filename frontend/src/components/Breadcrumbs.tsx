import Link from "next/link";

export type BreadcrumbItem = { label: string; href?: string };

export function Breadcrumbs({ items }: { items: BreadcrumbItem[] }) {
  const trail: BreadcrumbItem[] = [{ label: "خانه", href: "/" }, ...items];

  return (
    <nav aria-label="مسیر صفحه" className="text-muted-foreground flex flex-wrap items-center gap-1.5 text-sm">
      {trail.map((item, index) => {
        const isLast = index === trail.length - 1;
        return (
          <span key={index} className="flex items-center gap-1.5">
            {item.href && !isLast ? (
              <Link href={item.href} className="hover:text-foreground hover:underline">
                {item.label}
              </Link>
            ) : (
              <span className={isLast ? "text-foreground font-medium" : undefined}>{item.label}</span>
            )}
            {!isLast && <span aria-hidden="true">/</span>}
          </span>
        );
      })}
    </nav>
  );
}

export default Breadcrumbs;
