import { LoginPage } from "@/modules/auth/pages/LoginPage";

export default function Page({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  return <LoginPage searchParams={searchParams} />;
}
