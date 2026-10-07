"use client";

import { TableKit } from "@tiptap/extension-table";
import {
  EditorContent,
  useEditor,
  useEditorState,
  type Editor,
} from "@tiptap/react";
import { BubbleMenu } from "@tiptap/react/menus";
import StarterKit from "@tiptap/starter-kit";
import {
  Bold,
  ChevronDown,
  Italic,
  Link2,
  List,
  ListOrdered,
  Redo2,
  Undo2,
} from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { PROSE } from "@/components/prose";
import { cn } from "@/lib/utils";

// Only what the server's nh3 allowlist keeps: h2–h4, p, lists, a, strong,
// em, table. Everything else would be stripped on save anyway.
const extensions = [
  StarterKit.configure({
    heading: { levels: [2, 3, 4] },
    blockquote: false,
    code: false,
    codeBlock: false,
    hardBreak: false,
    horizontalRule: false,
    strike: false,
    underline: false,
    link: { openOnClick: false, autolink: true },
  }),
  TableKit,
];

const TEXT_STYLES = [
  { label: "Paragraph", level: 0 },
  { label: "Heading 2", level: 2 },
  { label: "Heading 3", level: 3 },
  { label: "Heading 4", level: 4 },
] as const;

const BODY = "mx-auto w-full max-w-[720px] px-4 pt-6 pb-10 md:px-10 md:pt-9";

/**
 * The article body editor (Tiptap simple-editor layout): a toolbar plus a
 * bubble menu on selection. With `editable={false}` it is a plain reader.
 */
export function ArticleEditor({
  content,
  editable = true,
  onChange,
  label = "Article body",
  header,
  className,
}: {
  content: string;
  /** Rendered between the toolbar and the body, e.g. title and slug fields. */
  header?: React.ReactNode;
  editable?: boolean;
  onChange?: (html: string) => void;
  label?: string;
  className?: string;
}) {
  const editor = useEditor({
    extensions,
    content,
    editable,
    immediatelyRender: false,
    editorProps: {
      attributes: {
        "aria-label": label,
        class: cn("outline-none min-h-48", PROSE),
      },
    },
    onUpdate: ({ editor }) => onChange?.(editor.getHTML()),
  });

  if (!editor) {
    // Server render and first paint: the same HTML, read-only.
    return (
      <div className={className}>
        {editable && <div className="h-[49px] border-b" />}
        <div className={BODY}>
          {header}
          <div
            className={cn("min-h-48", PROSE)}
            dangerouslySetInnerHTML={{ __html: content }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col", className)}>
      {editable && <Toolbar editor={editor} />}
      {editable && <SelectionMenu editor={editor} />}
      <div className={BODY}>
        {header}
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}

function useMarks(editor: Editor) {
  return useEditorState({
    editor,
    selector: ({ editor }) => ({
      bold: editor.isActive("bold"),
      italic: editor.isActive("italic"),
      link: editor.isActive("link"),
      bullet: editor.isActive("bulletList"),
      ordered: editor.isActive("orderedList"),
      level:
        ([2, 3, 4] as const).find((level) =>
          editor.isActive("heading", { level }),
        ) ?? 0,
      canUndo: editor.can().undo(),
      canRedo: editor.can().redo(),
    }),
  });
}

function toggleLink(editor: Editor) {
  if (editor.isActive("link")) {
    editor.chain().focus().unsetLink().run();
    return;
  }
  // ponytail: native prompt; a popover field if editors ask for one.
  const href = window.prompt("Link URL", "https://");
  if (href && href !== "https://") {
    editor.chain().focus().extendMarkRange("link").setLink({ href }).run();
  }
}

function Tool({
  label,
  active,
  className,
  ...props
}: React.ComponentProps<"button"> & { label: string; active?: boolean }) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      aria-pressed={active}
      className={cn(
        "text-foreground/65 hover:bg-muted hover:text-foreground focus-visible:ring-ring/50 disabled:text-foreground/25 inline-flex h-8 min-w-8 items-center justify-center gap-1 rounded-lg px-1.5 text-[13px] font-medium outline-none focus-visible:ring-3 disabled:hover:bg-transparent [&_svg]:size-4",
        active && "bg-muted text-foreground",
        className,
      )}
      {...props}
    />
  );
}

const Sep = () => (
  <span aria-hidden className="bg-border mx-1.5 h-5 w-px shrink-0" />
);

function Toolbar({ editor }: { editor: Editor }) {
  const s = useMarks(editor);
  const chain = () => editor.chain().focus();

  return (
    <div
      role="toolbar"
      aria-label="Formatting"
      className="bg-background sticky top-0 z-10 flex items-center gap-0.5 overflow-x-auto border-b px-3 py-2 md:px-5"
    >
      <Tool
        label="Undo"
        disabled={!s.canUndo}
        onClick={() => chain().undo().run()}
      >
        <Undo2 />
      </Tool>
      <Tool
        label="Redo"
        disabled={!s.canRedo}
        onClick={() => chain().redo().run()}
      >
        <Redo2 />
      </Tool>
      <Sep />
      <DropdownMenu>
        <DropdownMenuTrigger
          render={<Tool label="Text style" className="w-auto px-2" />}
        >
          {TEXT_STYLES.find((t) => t.level === s.level)?.label}
          <ChevronDown className="size-3.5!" />
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-40">
          {TEXT_STYLES.map(({ label, level }) => (
            <DropdownMenuItem
              key={level}
              onClick={() =>
                level === 0
                  ? chain().setParagraph().run()
                  : chain().setHeading({ level }).run()
              }
            >
              {label}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      <Tool
        label="Bulleted list"
        active={s.bullet}
        onClick={() => chain().toggleBulletList().run()}
      >
        <List />
      </Tool>
      <Tool
        label="Numbered list"
        active={s.ordered}
        onClick={() => chain().toggleOrderedList().run()}
      >
        <ListOrdered />
      </Tool>
      <Sep />
      <Tool
        label="Bold"
        active={s.bold}
        onClick={() => chain().toggleBold().run()}
      >
        <Bold />
      </Tool>
      <Tool
        label="Italic"
        active={s.italic}
        onClick={() => chain().toggleItalic().run()}
      >
        <Italic />
      </Tool>
      <Tool label="Link" active={s.link} onClick={() => toggleLink(editor)}>
        <Link2 />
      </Tool>
    </div>
  );
}

function SelectionMenu({ editor }: { editor: Editor }) {
  const s = useMarks(editor);
  return (
    <BubbleMenu
      editor={editor}
      className="bg-background flex items-center gap-0.5 rounded-[10px] border p-1 shadow-[0_8px_24px_-6px_oklch(0_0_0/0.16),0_2px_4px_oklch(0_0_0/0.04)]"
    >
      <Tool
        label="Bold"
        active={s.bold}
        className="h-7 min-w-7"
        onClick={() => editor.chain().focus().toggleBold().run()}
      >
        <Bold />
      </Tool>
      <Tool
        label="Italic"
        active={s.italic}
        className="h-7 min-w-7"
        onClick={() => editor.chain().focus().toggleItalic().run()}
      >
        <Italic />
      </Tool>
      <Sep />
      <Tool
        label="Link"
        active={s.link}
        className="h-7 min-w-7"
        onClick={() => toggleLink(editor)}
      >
        <Link2 />
      </Tool>
    </BubbleMenu>
  );
}
