import type { paths } from "@/lib/api/schema";

export type ApiResponse<
  Path extends keyof paths,
  Method extends keyof paths[Path],
> = paths[Path][Method] extends {
  responses: { 200: { content: { "application/json": infer T } } };
}
  ? T
  : never;
