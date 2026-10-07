import "server-only";

import type { Schemas } from "@/lib/api/types";

/**
 * Fixture-only (T-033): seed data shared by every module's fixtures, so the
 * report and the review page reflect what the agency screens change.
 *
 * ponytail: in-memory per dev server process, reset on restart. Deleted with
 * the fixtures during wiring (T-032, T-028, T-029).
 */

type Article = Schemas["ArticleDetail"];

export type FixtureSite = Schemas["SiteOut"] & {
  // Fixture-only extension (T-031 design follow-ups): no API fields yet.
  wp_username: string;
  connection_ok: boolean;
  connection_checked_at: string;
};

const day = 24 * 60 * 60 * 1000;
const at = (days: number, hour = 9) => {
  const d = new Date(Date.now() + days * day);
  d.setUTCHours(hour, 0, 0, 0);
  return d.toISOString();
};

const BODY = `<h2>Why it matters</h2>
<p>Choosing the right gear makes every run more comfortable. This guide walks through what to look for, what to skip, and how to test before you buy.</p>
<h3>What to look for</h3>
<ul><li><strong>Fit:</strong> a thumb's width of space at the toe.</li><li><strong>Support:</strong> match the shoe to your arch.</li><li><strong>Cushioning:</strong> more for long runs, less for speed work.</li></ul>
<p>Read our <a href="https://acme-running.com/fit-guide">fit guide</a> for the full checklist.</p>
<table><tbody><tr><th>Arch</th><th>Shoe type</th></tr><tr><td>Flat</td><td>Stability</td></tr><tr><td>High</td><td>Neutral, cushioned</td></tr></tbody></table>
<p>Whatever you choose, break new shoes in over two weeks of short runs.</p>`;

let nextId = 100;
export const newId = () => `a${nextId++}`;

function article(
  title: string,
  status: Article["status"],
  extra: Partial<Article> = {},
): Article {
  const slug = title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  return {
    id: newId(),
    title,
    slug,
    body_html: BODY,
    status,
    version: 1,
    source: "paste",
    warnings: [],
    events: [
      {
        id: `e${nextId}`,
        type: "imported",
        actor: "agency@example.test",
        at: at(-12),
      },
    ],
    created_at: at(-12),
    updated_at: at(-2),
    ...extra,
  };
}

function seed() {
  const sites: FixtureSite[] = [
    {
      id: "acme",
      name: "Acme Running",
      wp_base_url: "https://acme-running.com",
      wp_username: "acme-admin",
      connection_ok: true,
      connection_checked_at: at(0),
    },
    {
      id: "brightsmile",
      name: "BrightSmile Dental",
      wp_base_url: "https://brightsmile-dental.com",
      wp_username: "brightsmile-admin",
      connection_ok: true,
      connection_checked_at: at(0),
    },
    {
      id: "northpeak",
      name: "Northpeak Outdoors",
      wp_base_url: "https://northpeak-outdoors.com",
      wp_username: "northpeak-admin",
      connection_ok: false,
      connection_checked_at: at(-2),
    },
    {
      id: "lumen",
      name: "Lumen Yoga Studio",
      wp_base_url: "https://lumen-yoga.studio",
      wp_username: "lumen-admin",
      connection_ok: true,
      connection_checked_at: at(0),
    },
  ];

  const acme: Article[] = [
    article("10 Best Running Shoes for Flat Feet", "draft", {
      source: "docx",
      source_filename: "flat-feet.docx",
      warnings: ["This document had 3 images. Images are not imported."],
    }),
    article("How to Choose a Treadmill for Home Use", "awaiting_approval", {
      version: 2,
    }),
    article("5 Stretches Every Runner Should Do", "awaiting_approval"),
    article("Beginner's Guide to Marathon Training", "changes_requested", {
      client_comment:
        "Please mention our Saturday group runs in the intro, and soften the claim about injury prevention.",
      events: [
        { id: "e-m1", type: "imported", actor: "Sarah", at: at(-4, 9) },
        { id: "e-m2", type: "sent_for_review", actor: "Sarah", at: at(-3, 10) },
        {
          id: "e-m3",
          type: "changes_requested",
          actor: "Jordan",
          at: at(-1, 14),
        },
      ],
    }),
    article("The Benefits of Trail Running", "approved", {
      approved_version: 1,
    }),
    article("Running Shoe Maintenance 101", "scheduled", {
      approved_version: 1,
      publish_at_utc: at(-1),
      sync_warning: "late",
      wp_post_id: 412,
    }),
    article("Hydration Tips for Hot-Weather Runs", "scheduled", {
      approved_version: 1,
      publish_at_utc: at(5),
      wp_post_id: 418,
    }),
    article("Why Compression Socks Work", "published", {
      approved_version: 1,
      publish_at_utc: at(-6),
      published_url: "https://acme-running.com/compression-socks",
      wp_post_id: 377,
    }),
    article("Couch to 5K in Eight Weeks", "published", {
      approved_version: 1,
      publish_at_utc: at(-15),
      published_url: "https://acme-running.com/couch-to-5k",
      wp_post_id: 360,
      sync_warning: "changed_in_wordpress",
    }),
    article("Top 5 Marathons in Southeast Asia", "failed", {
      approved_version: 1,
      last_error: "WordPress returned 403 Forbidden",
    }),
  ];

  return {
    sites,
    articles: {
      acme,
      brightsmile: [
        article("How Often Should You Replace Your Toothbrush?", "draft"),
        article("Whitening at Home: What Works", "published", {
          published_url: "https://brightsmile-dental.com/whitening",
          publish_at_utc: at(-3),
        }),
      ],
      northpeak: [article("Choosing a Three-Season Tent", "draft")],
      lumen: [],
    } as Record<string, Article[]>,
    reviewTokens: { demo: "acme", "demo-empty": "lumen" } as Record<
      string,
      string
    >,
    reviewLinkCreatedAt: at(-30),
  };
}

const g = globalThis as unknown as { __fixtures?: ReturnType<typeof seed> };

/** Survives HMR so dev edits don't reset the state mid-session. */
export const db = (g.__fixtures ??= seed());

export const now = () => new Date().toISOString();
