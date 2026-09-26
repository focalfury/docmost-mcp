import StarterKit from "@tiptap/starter-kit";
import Image from "@tiptap/extension-image";
import Link from "@tiptap/extension-link";
import {
  Table,
  TableCell,
  TableHeader,
  TableRow,
} from "@tiptap/extension-table";

// Define extensions compatible with standard Markdown features
// We use the default Tiptap extensions to handle basic content
export const tiptapExtensions = [
  StarterKit.configure({
    // Explicitly enable features that might be disabled in some contexts
    codeBlock: {},
    heading: {},
  }),
  Image.configure({
    inline: true,
  }),
  Link.configure({
    openOnClick: false,
  }),
  // Without a node spec for <table>, generateJSON() flattens the whole
  // table into one paragraph of concatenated cell text. Node names match
  // Docmost's schema: table / tableRow / tableHeader / tableCell.
  Table,
  TableRow,
  TableHeader,
  TableCell,
];
