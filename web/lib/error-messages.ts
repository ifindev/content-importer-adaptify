const MESSAGES: Record<string, string> = {
  empty_content: "The article is empty. Add some text first.",
  payload_too_large: "That's too large to import. The limit is 2 MB.",
  no_files: "Choose at least one .docx file.",
  too_many_files: "Upload at most 10 files at a time.",
  unsupported_file_type: "Only .docx files can be imported.",
  unreadable_file: "This file couldn't be read. It may be damaged.",
  file_too_large: "This file is over 10 MB.",
  not_found: "This article no longer exists.",
  not_editable:
    "This article can't be edited in its current status. Reload to see the latest version.",
  empty_update: "Nothing changed.",
  not_deletable:
    "Only Draft and Changes requested articles can be deleted. Pull it back first if it's waiting for the client.",
  not_sendable: "This article can't be sent for review right now.",
  not_awaiting_approval: "This article is no longer waiting for approval.",
  not_schedulable: "Only approved articles can be scheduled.",
  publish_at_in_past: "Pick a date and time in the future.",
  not_failed: "This article isn't in Failed any more.",
  wordpress_error: "WordPress returned an error. Try again in a moment.",
  wp_connection_failed:
    "Couldn't connect to WordPress with these details. Check the URL and app password.",
  site_not_found: "This site no longer exists.",
  insecure_url: "The WordPress URL must start with https://.",
  article_changed:
    "The agency changed this article while you were reading. Reload to see the latest version.",
  rate_limited: "Too many requests. Try again in a minute.",
  validation_error:
    "Some details aren't valid. Check the form: slugs use only lowercase letters, numbers and hyphens.",
};

/** The user-facing sentence for an API error code, with a generic fallback. */
export function messageFor(code: string): string {
  return MESSAGES[code] ?? "Something went wrong. Try again.";
}
