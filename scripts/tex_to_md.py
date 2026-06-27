import sys
import os
import re
import shutil
import tarfile
import zipfile
import tempfile

def extract_archive(archive_path, dest_dir):
    """Extracts tar.gz or zip files into dest_dir."""
    print(f"[*] Extracting archive {archive_path} to {dest_dir}...")
    try:
        if archive_path.endswith(".tar.gz") or archive_path.endswith(".tgz") or tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path, "r:gz") as tar:
                # Resolve members safely to prevent path traversal
                for member in tar.getmembers():
                    member_path = os.path.join(dest_dir, member.name)
                    if not os.path.abspath(member_path).startswith(os.path.abspath(dest_dir)):
                        continue
                    tar.extract(member, dest_dir)
            return True
        elif archive_path.endswith(".zip") or zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(dest_dir)
            return True
        else:
            print(f"[!] Warning: '{archive_path}' is not a recognized archive format.")
            return False
    except Exception as e:
        print(f"[!] Archive extraction failed: {e}")
        return False

def find_root_tex_file(extract_dir):
    """Finds the root LaTeX file (containing \\documentclass and \\begin{document})."""
    tex_files = []
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.endswith(".tex"):
                tex_files.append(os.path.join(root, file))
                
    if not tex_files:
        return None
        
    # Look for \documentclass AND \begin{document}
    for f in tex_files:
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
                if "\\documentclass" in content and "\\begin{document}" in content:
                    return f
        except Exception:
            continue
            
    # Look for just \begin{document}
    for f in tex_files:
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
                if "\\begin{document}" in content:
                    return f
        except Exception:
            continue
            
    # Fallback to the largest .tex file
    tex_files.sort(key=lambda x: os.path.getsize(x), reverse=True)
    return tex_files[0]

def resolve_and_inline(file_path, base_dir, visited=None):
    """Recursively inlines \\input{} and \\include{} files into a single LaTeX document."""
    if visited is None:
        visited = set()
        
    canonical_path = os.path.normpath(file_path)
    if canonical_path in visited:
        return f"\n% Cycle detected: {file_path} already included\n"
    visited.add(canonical_path)
    
    actual_path = file_path
    if not os.path.exists(actual_path):
        if not actual_path.endswith(".tex"):
            actual_path += ".tex"
        if not os.path.exists(actual_path):
            return f"\n% File not found: {file_path}\n"
            
    try:
        with open(actual_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        return f"\n% Error reading {file_path}: {e}\n"
        
    # Regex to match \input{file} or \include{file} or \input file
    pattern = re.compile(r'\\(input|include)\s*(?:\{([^}]+)\}|([a-zA-Z0-9_\-\./]+))')
    
    def replace_func(match):
        filename = match.group(2) or match.group(3)
        filename = filename.strip()
        
        current_dir = os.path.dirname(actual_path)
        target_path = os.path.join(current_dir, filename)
        
        # If relative file doesn't exist, search in base_dir
        if not os.path.exists(target_path) and not os.path.exists(target_path + ".tex"):
            target_path = os.path.join(base_dir, filename)
            
        return resolve_and_inline(target_path, base_dir, visited)
        
    return pattern.sub(replace_func, content)

def basic_fallback_tex_to_md(tex_content, md_path):
    """Crude fallback regex-based LaTeX parser to extract text if Pandoc is missing."""
    try:
        # Remove comments
        body = re.sub(r'(?<!\\)%.*$', '', tex_content, flags=re.MULTILINE)
        
        # Try to isolate document content
        doc_match = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', body, re.DOTALL)
        if doc_match:
            body = doc_match.group(1)
            
        # Sections
        body = re.sub(r'\\section\*?\{([^}]+)\}', r'# \1', body)
        body = re.sub(r'\\subsection\*?\{([^}]+)\}', r'## \1', body)
        body = re.sub(r'\\subsubsection\*?\{([^}]+)\}', r'### \1', body)
        
        # Formats
        body = re.sub(r'\\textbf\{([^}]+)\}', r'**\1**', body)
        body = re.sub(r'\\textit\{([^}]+)\}', r'*\1*', body)
        body = re.sub(r'\\emph\{([^}]+)\}', r'*\1*', body)
        body = re.sub(r'\\texttt\{([^}]+)\}', r'`\1`', body)
        
        # Unescape symbols
        body = body.replace('\\_', '_').replace('\\%', '%').replace('\\&', '&').replace('\\$', '$').replace('~', ' ')
        
        # Remove common macros
        body = re.sub(r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?', '', body)
        
        # Clean up excessive newlines
        body = re.sub(r'\n{3,}', '\n\n', body)
        
        os.makedirs(os.path.dirname(os.path.abspath(md_path)), exist_ok=True)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(body.strip())
            
        print(f"[+] Basic fallback conversion completed at '{md_path}'.")
        return True
    except Exception as e:
        print(f"[!] Fallback parser failed: {e}")
        return False

def convert_tex_to_md(tex_content, md_path):
    """Converts LaTeX content to Markdown using Pandoc if available, otherwise falling back."""
    pandoc_path = shutil.which("pandoc")
    
    # Create temp tex file
    fd, temp_tex = tempfile.mkstemp(suffix=".tex")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as tmp:
            tmp.write(tex_content)
            
        if not pandoc_path:
            print("[!] Warning: 'pandoc' was not found on PATH. Using fallback parser...")
            return basic_fallback_tex_to_md(tex_content, md_path)
            
        print(f"[*] Running pandoc to convert to {md_path}...")
        try:
            import subprocess
            subprocess.run([
                "pandoc",
                "-f", "latex",
                "-t", "markdown",
                "--wrap=none",
                "-o", md_path,
                temp_tex
            ], check=True)
            print(f"[+] Successfully converted TeX to Markdown at '{md_path}'.")
            return True
        except Exception as e:
            print(f"[!] Pandoc run failed: {e}. Falling back...")
            return basic_fallback_tex_to_md(tex_content, md_path)
    finally:
        try:
            os.remove(temp_tex)
        except OSError:
            pass

def main():
    if len(sys.argv) < 3:
        print("Usage: python tex_to_md.py <archive_path> <output_md_path>")
        sys.exit(1)
        
    archive_path = sys.argv[1]
    output_path = sys.argv[2]
    
    if not os.path.exists(archive_path):
        print(f"Error: Archive {archive_path} does not exist.")
        sys.exit(1)
        
    # Create a temporary directory for extraction
    temp_dir = tempfile.mkdtemp(prefix="opencode_tex_extract_")
    try:
        success = extract_archive(archive_path, temp_dir)
        if not success:
            # If not an archive, check if it is already a single .tex file
            if archive_path.endswith(".tex"):
                print("[*] Input is already a .tex file. Resolving inputs and reading...")
                inlined_latex = resolve_and_inline(archive_path, os.path.dirname(os.path.abspath(archive_path)))
                convert_tex_to_md(inlined_latex, output_path)
                return
            else:
                print(f"[!] Input file '{archive_path}' is not a recognized archive or .tex file.")
                sys.exit(1)
                
        root_tex = find_root_tex_file(temp_dir)
        if not root_tex:
            print("[!] Error: Could not find any root .tex file in the extracted archive.")
            sys.exit(1)
            
        print(f"[+] Found root LaTeX file: {os.path.basename(root_tex)}")
        
        # Recursively inline files
        inlined_latex = resolve_and_inline(root_tex, temp_dir)
        
        # Convert to markdown
        convert_tex_to_md(inlined_latex, output_path)
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
