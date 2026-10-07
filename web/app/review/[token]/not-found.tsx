import { Link2Off } from "lucide-react";

export default function NotFound() {
  return (
    <div className="bg-app flex min-h-svh items-center justify-center p-6 text-center">
      <div className="max-w-sm">
        <Link2Off className="text-faint mx-auto mb-3 size-6" />
        <h1 className="text-[15px] font-semibold">
          This link isn&apos;t valid
        </h1>
        <p className="text-muted-foreground mt-1 text-[13.5px]">
          It may have been replaced with a new one. Ask the agency for the
          current review link.
        </p>
      </div>
    </div>
  );
}
