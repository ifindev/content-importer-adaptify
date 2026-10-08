import { LoginForm } from "@/modules/auth/components/LoginForm";

export async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; expired?: string }>;
}) {
  // `expired` comes only from apiServer's 401 redirect: a session cookie was
  // sent and rejected. proxy.ts's redirect (no cookie at all) leaves it off.
  const { next, expired } = await searchParams;

  return (
    <div className="bg-app flex min-h-full flex-1 items-center justify-center p-6">
      <LoginForm next={next ?? null} sessionExpired={expired === "1"} />
    </div>
  );
}
