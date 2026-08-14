"use client";

import { useEffect, useState } from "react";
import { ArrowUp } from "lucide-react";

import { Button } from "@/components/ui/button";

const SCROLL_THRESHOLD = 400;

export function BackToTopButton() {
  const [visible, setVisible] = useState(
    () => typeof window !== "undefined" && window.scrollY > SCROLL_THRESHOLD,
  );

  useEffect(() => {
    function onScroll() {
      setVisible(window.scrollY > SCROLL_THRESHOLD);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  if (!visible) return null;

  return (
    <Button
      variant="outline"
      size="icon"
      aria-label="برو به بالای صفحه"
      title="برو به بالای صفحه"
      onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
      className="bg-background fixed bottom-24 left-4 z-40 rounded-full shadow-md"
    >
      <ArrowUp />
    </Button>
  );
}

export default BackToTopButton;
