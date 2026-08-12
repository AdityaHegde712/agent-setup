# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "html2text",
# ]
# ///
"""Convert an HTML file to Markdown using html2text.

Run via uv so the `html2text` dependency is resolved from the inline PEP 723
metadata above (no runtime `pip install` required):

    uv run --script scripts/html_to_md.py <input_html_path> <output_md_path>
"""

import os
import sys

import html2text


def main():
    if len(sys.argv) < 3:
        print("Usage: python html_to_md.py <input_html_path> <output_md_path>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    if not os.path.exists(input_path):
        print(f"Error: input file {input_path} does not exist.")
        sys.exit(1)

    print(f"[*] Converting {input_path} to {output_path}...")
    try:
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()

        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0  # Do not wrap lines

        md_content = h.handle(html_content)

        # Ensure target directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"[+] Successfully converted HTML to Markdown at '{output_path}'.")
    except Exception as e:
        print(f"[!] Error during conversion: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
