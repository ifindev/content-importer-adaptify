import type { Status } from "@/components/status-badge";

export const LINKS = {
  demo: "/login",
  signIn: "/login",
  github: "https://github.com/ifindev/content-importer-adaptify",
  apiDocs: "https://importer-api.aiwitharifin.com/docs",
} as const;

export const STATS = [
  { value: "0", label: "Accounts your clients need" },
  { value: "1 tap", label: "To approve, on any phone" },
] as const;

export const TODAY = [
  "Articles scattered across Google Docs, Word files and email",
  "Approvals buried in long email threads",
  "Every article copy-pasted into WordPress by hand",
  "Last-minute edits go live without the client seeing them",
] as const;

export const WITH_US = [
  "Every article in one list, with its status",
  "Clients approve from one private link",
  "Approved posts are scheduled on WordPress for you",
  "Any edit after approval goes back to the client",
] as const;

export const STEPS = [
  {
    title: "Import your articles",
    text: "Paste from Google Docs, Word or any web page, or upload several .docx files at once. Formatting is cleaned and headings are kept.",
  },
  {
    title: "Get client approval",
    text: "Send one private link. Your client reads each article on any device and approves or asks for changes, without an account.",
  },
  {
    title: "Schedule to WordPress",
    text: "Pick a date for each approved article. It's queued on WordPress, and nothing goes out before approval.",
  },
  {
    title: "Publish and report",
    text: "WordPress publishes on the date. Your report shows live URLs, time to approval and change rounds.",
  },
] as const;

export type SampleRow = {
  title: string;
  status: Status;
  date?: string;
  /** Flips to Approved in a loop, to show the review flow. */
  flips?: boolean;
};

export const SAMPLE_ROWS: SampleRow[] = [
  { title: "10 marathon training mistakes", status: "approved" },
  {
    title: "How to pick a running shoe",
    status: "awaiting_approval",
    flips: true,
  },
  { title: "Hill repeats for flat-landers", status: "changes_requested" },
  {
    title: "Recovery runs, explained",
    status: "scheduled",
    date: "Oct 16, 09:00",
  },
  {
    title: "Carb loading for beginners",
    status: "published",
    date: "Oct 2, 09:00",
  },
  { title: "Best trail running shoes 2026", status: "draft" },
];

export const FAQ = [
  {
    q: "Do my clients need an account?",
    a: "No. Each client site gets one private review link. Your client opens it on any device, reads what's waiting and approves or asks for changes. Their name is logged with every decision.",
  },
  {
    q: "Where can I import articles from?",
    a: "Paste from Google Docs, Word or any web page: headings, lists, links, bold and italic are kept, and stray fonts and colors are cleaned away. Or upload several .docx files at once; each one becomes its own draft.",
  },
  {
    q: "Which website platforms are supported?",
    a: "WordPress. You connect each client site with a WordPress application password, which the site owner can revoke at any time. The connection is tested before the site is saved, and the password is stored encrypted.",
  },
  {
    q: "What if someone edits the post in WordPress?",
    a: "The app notices and flags the article as Late, Changed in WordPress or Missing in WordPress, so its status stays accurate.",
  },
  {
    q: "Can anything go live before the client approves?",
    a: "No. Only approved articles can be scheduled, and any edit after approval sends the article back to Draft for another review.",
  },
] as const;

export const NAV = [
  { href: "#how", label: "How it works" },
  { href: "#features", label: "Features" },
  { href: "#faq", label: "FAQ" },
] as const;

/** The landing's primary button: black, not the app's blue. */
export const DARK_BUTTON =
  "bg-foreground text-background hover:bg-foreground/85 focus-visible:ring-foreground/30";
