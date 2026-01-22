import sys
import os
import json
import traceback
import logging

# Setup a debug log file in the same directory as this script
debug_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cli_debug.log")

# Configure logging
logging.basicConfig(
    filename=debug_log_path,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

def log_debug(msg):
    logging.debug(msg)

log_debug(f"--- CLI Started: {sys.argv} ---")
log_debug(f"CWD: {os.getcwd()}")
log_debug(f"PYTHONPATH: {sys.path}")

# Add current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Global result wrapper
def print_json(data):
    print(json.dumps(data))

try:
    from utils.encrypt_epub import run as encrypt_run
    from utils.decrypt_epub import run as decrypt_run
    from utils.reformat_epub import run as reformat_run
    from utils.encrypt_font import run_epub_font_encrypt
    from utils.webp_to_img import run as run_webp_to_img
    from utils.img_to_webp import run as run_img_to_webp
    from utils.img_compress import run as run_img_compress
    from utils.font_subset import run_epub_font_subset
    from utils.chinese_convert import run_s2t, run_t2s
    from utils.pinyin_annotate import run_add_pinyin
    from utils.yuewei_to_duokan import run as run_yuewei_to_duokan
    log_debug("Imports successful")
except ImportError as e:
    err_msg = f"ImportError: {str(e)}\n{traceback.format_exc()}"
    log_debug(err_msg)
    print_json({"status": "error", "message": f"Python Environment Error: {str(e)}"})
    sys.exit(1)
except Exception as e:
    err_msg = f"Startup Error: {str(e)}\n{traceback.format_exc()}"
    log_debug(err_msg)
    print_json({"status": "error", "message": f"Startup Error: {str(e)}"})
    sys.exit(1)

def main():
    # Manual argument parsing
    argv = sys.argv[1:]
    
    if not argv:
        print_json({"status": "error", "message": "No command provided"})
        return

    cmd = argv[0]
    input_path = None
    output_dir = None
    extra_str = "{}"
    
    # Simple parser
    i = 1
    positional = []
    while i < len(argv):
        arg = argv[i]
        if arg == "--input":
            if i + 1 < len(argv):
                input_path = argv[i+1]
                i += 1
        elif arg == "--output":
            if i + 1 < len(argv):
                output_dir = argv[i+1]
                i += 1
        elif arg == "--extra":
            if i + 1 < len(argv):
                extra_str = argv[i+1]
                i += 1
        elif arg.startswith("--"):
            pass
        else:
            positional.append(arg)
        i += 1
        
    if not input_path and len(positional) > 0:
        input_path = positional[0]
    if not output_dir and len(positional) > 1:
        output_dir = positional[1]

    log_debug(f"Parsed: cmd={cmd}, input={input_path}, output={output_dir}")

    if not input_path:
         print_json({"status": "error", "message": "No input file provided"})
         return

    try:
        extra = json.loads(extra_str)
    except:
        extra = {}

    result = 0
    try:
        if cmd == "encrypt":
            result = encrypt_run(input_path, output_dir)
        elif cmd == "decrypt":
            result = decrypt_run(input_path, output_dir)
        elif cmd == "reformat":
            result = reformat_run(input_path, output_dir)
        elif cmd == "font_encrypt":
            result = run_epub_font_encrypt(input_path, output_dir)
        elif cmd == "font_subset":
            result = run_epub_font_subset(input_path, output_dir)
        elif cmd == "img_to_webp":
            result = run_img_to_webp(input_path, output_dir)
        elif cmd == "img_compress":
            result = run_img_compress(input_path, output_dir)
        elif cmd == "webp_to_img":
            result = run_webp_to_img(input_path, output_dir)
        elif cmd == "s2t":
            result = run_s2t(input_path, output_dir)
        elif cmd == "t2s":
            result = run_t2s(input_path, output_dir)
        elif cmd == "add_pinyin":
            result = run_add_pinyin(input_path, output_dir)
        elif cmd == "yuewei_to_duokan":
            result = run_yuewei_to_duokan(input_path, output_dir)
        else:
            print_json({"status": "error", "message": f"Unknown command: {cmd}"})
            return

        # Handle special return value (tuple) for any command
        if isinstance(result, tuple):
            status_code, message = result
            if status_code == 0:
                # Success - message contains output path
                print_json({"status": "success", "file": input_path, "output_path": message})
            else:
                # Error - message contains error message
                print_json({"status": "error", "message": message, "file": input_path})
        elif result == 0:
             print_json({"status": "success", "file": input_path})
        elif result == "skip":
             print_json({"status": "skip", "file": input_path})
        else:
             print_json({"status": "error", "message": str(result), "file": input_path})

    except Exception as e:
        err_msg = f"Runtime Error: {str(e)}\n{traceback.format_exc()}"
        log_debug(err_msg)
        print_json({"status": "error", "message": str(e), "file": input_path})

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_debug(f"Fatal Error: {traceback.format_exc()}")
        print_json({"status": "error", "message": str(e)})
        sys.exit(1)