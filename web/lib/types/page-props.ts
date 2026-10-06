export type PageProps<Params = Record<string, never>> = {
  params: Promise<Params>;
};
