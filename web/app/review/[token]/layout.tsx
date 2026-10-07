import type { Metadata } from "next";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
};

export default function ReviewLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-full flex-col">
      <header className="border-b p-4 text-sm font-semibold">
        Content Importer
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}
