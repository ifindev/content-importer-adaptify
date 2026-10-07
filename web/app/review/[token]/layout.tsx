import type { Metadata } from "next";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
};

export default function ReviewLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      {children}
      <Toaster />
    </>
  );
}
