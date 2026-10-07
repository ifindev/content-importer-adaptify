import { LoginForm } from "@/modules/auth/components/LoginForm";

export async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const { next } = await searchParams;

  return (
    <div className="flex min-h-full flex-1 items-center justify-center p-4">
      <LoginForm next={next ?? null} sessionExpired={Boolean(next)} />
    </div>
  );
}
