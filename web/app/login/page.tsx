import { LoginPage } from "@/modules/auth/pages/LoginPage";

export default function Page({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; expired?: string }>;
}) {
  return <LoginPage searchParams={searchParams} />;
}
