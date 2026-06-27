import sys
import os


def install_and_import(package):
    import importlib

    try:
        importlib.import_module(package)
    except ImportError:
        import subprocess

        print(f"[*] Installing {package}...")
        # Try installing using standard pip
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except Exception as e:
            print(f"[!] Error installing {package}: {e}")
            raise


def main():
    if len(sys.argv) < 3:
        print("Usage: python html_to_md.py <input_html_path> <output_md_path>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    if not os.path.exists(input_path):
        print(f"Error: input file {input_path} does not exist.")
        sys.exit(1)

    try:
        install_and_import("html2text")
    except Exception:
        print("[!] Failed to load html2text library.")
        sys.exit(1)

    # pyrefly: ignore [missing-import]
    import html2text

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
