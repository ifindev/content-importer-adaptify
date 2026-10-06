import Link from "next/link";

export default function AgencyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-full flex-col">
      <nav className="flex gap-4 border-b p-4">
        <Link href="/import">Import</Link>
        <Link href="/articles">Articles</Link>
        <Link href="/report">Report</Link>
      </nav>
      <main className="flex-1">{children}</main>
    </div>
  );
}
