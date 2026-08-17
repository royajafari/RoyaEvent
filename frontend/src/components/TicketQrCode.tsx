"use client";

import { useEffect, useState } from "react";
import QRCode from "qrcode";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export function TicketQrCode({ ticketCode }: { ticketCode: string }) {
  const [open, setOpen] = useState(false);
  const [dataUrl, setDataUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    QRCode.toDataURL(ticketCode, { margin: 1, width: 240 })
      .then((url) => {
        if (!cancelled) setDataUrl(url);
      })
      .catch(() => {
        if (!cancelled) setDataUrl(null);
      });
    return () => {
      cancelled = true;
    };
  }, [open, ticketCode]);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button size="sm" variant="outline" />}>نمایش QR</DialogTrigger>
      <DialogContent className="text-right">
        <DialogHeader>
          <DialogTitle>QR بلیط</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col items-center gap-3 py-2">
          {dataUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={dataUrl} alt={`QR بلیط ${ticketCode}`} className="h-60 w-60" />
          ) : (
            <p className="text-muted-foreground text-sm">در حال ساخت QR...</p>
          )}
          <p dir="ltr" className="text-muted-foreground text-sm">
            {ticketCode}
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
