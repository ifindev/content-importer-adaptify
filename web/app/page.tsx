import type { Metadata } from "next";

export { default } from "@/modules/landing/pages/LandingPage";

export const metadata: Metadata = {
  title: "Content Importer: client-approved articles, published on schedule",
  description:
    "Import articles from Google Docs or Word, get client approval from one private link, and publish to WordPress on schedule.",
  openGraph: {
    title: "Content Importer",
    description:
      "Import articles, get client approval from one private link, and publish to WordPress on schedule.",
  },
};
