"""
Webora Asset Optimization Script
Converts image assets in assets/ and assets/projects/ to high-quality WebP,
resizes oversized screenshots, and losslessly compresses the favicon.
"""

import os
import sys
from PIL import Image

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(WORKSPACE_DIR, "assets")
PROJECTS_DIR = os.path.join(ASSETS_DIR, "projects")

# Configuration
CONFIG = {
    "photos": {
        "files": ["abdurrahman-aiman.jpg", "fahru-rizal.jpg"],
        "dir": ASSETS_DIR,
        "format": "WEBP",
        "quality": 82,
        "method": 6,
        "max_width": None,
    },
    "projects": {
        "dir": PROJECTS_DIR,
        "format": "WEBP",
        "quality": 85,
        "method": 6,
        "max_width": 1600,
    },
    "favicon": {
        "file": "favicon.png",
        "dir": ASSETS_DIR,
        "optimize_png": True,
        "generate_webp": True,
        "quality": 95,
        "method": 6,
    }
}


def optimize_image(src_path, dest_path, quality, method=6, max_width=None):
    """
    Open an image, optionally resize it preserving aspect ratio,
    and save as WebP with the specified quality and compression method.
    """
    with Image.open(src_path) as img:
        orig_size = img.size
        orig_mode = img.mode
        w, h = orig_size
        
        # Resize if width exceeds max_width
        if max_width and w > max_width:
            new_w = max_width
            new_h = round(h * (max_width / w))
            resample_filter = getattr(Image.Resampling, 'LANCZOS', Image.LANCZOS)
            processed_img = img.resize((new_w, new_h), resample=resample_filter)
        else:
            processed_img = img.copy()

        # Save to WebP
        processed_img.save(
            dest_path,
            format="WEBP",
            quality=quality,
            method=method
        )
        
        # Verify output
        with Image.open(dest_path) as verify_img:
            verify_img.verify()

        return orig_size, processed_img.size, orig_mode


def optimize_favicon(src_path):
    """
    Losslessly optimize favicon.png preserving 100% pixel equality and format.
    Also generate favicon.webp for modern browser support.
    """
    with Image.open(src_path) as img:
        orig_size = img.size
        orig_mode = img.mode
        
        # Lossless PNG optimization
        tmp_png = src_path + ".tmp.png"
        img.save(tmp_png, format="PNG", optimize=True)
        
        # Replace original with optimized PNG
        os.replace(tmp_png, src_path)
        
        # Also create WebP version
        webp_dest = os.path.splitext(src_path)[0] + ".webp"
        img.save(webp_dest, format="WEBP", quality=95, method=6)
        
        return orig_size, orig_mode


def main():
    print(f"Starting asset optimization in: {ASSETS_DIR}")
    results = []

    # 1. Process Photos
    photo_cfg = CONFIG["photos"]
    for filename in photo_cfg["files"]:
        src_path = os.path.join(photo_cfg["dir"], filename)
        if not os.path.exists(src_path):
            print(f"Warning: Photo not found: {src_path}", file=sys.stderr)
            continue
        
        dest_filename = os.path.splitext(filename)[0] + ".webp"
        dest_path = os.path.join(photo_cfg["dir"], dest_filename)
        orig_bytes = os.path.getsize(src_path)
        
        orig_dims, new_dims, mode = optimize_image(
            src_path=src_path,
            dest_path=dest_path,
            quality=photo_cfg["quality"],
            method=photo_cfg["method"],
            max_width=photo_cfg["max_width"]
        )
        new_bytes = os.path.getsize(dest_path)
        results.append({
            "category": "Photo",
            "original_file": os.path.relpath(src_path, WORKSPACE_DIR),
            "new_file": os.path.relpath(dest_path, WORKSPACE_DIR),
            "orig_bytes": orig_bytes,
            "new_bytes": new_bytes,
            "orig_dims": orig_dims,
            "new_dims": new_dims,
            "mode": mode,
        })

    # 2. Process Project UI Screenshots
    proj_cfg = CONFIG["projects"]
    for filename in sorted(os.listdir(proj_cfg["dir"])):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".png", ".jpg", ".jpeg"]:
            continue
        # Avoid processing already generated .webp files
        src_path = os.path.join(proj_cfg["dir"], filename)
        dest_filename = os.path.splitext(filename)[0] + ".webp"
        dest_path = os.path.join(proj_cfg["dir"], dest_filename)
        orig_bytes = os.path.getsize(src_path)
        
        orig_dims, new_dims, mode = optimize_image(
            src_path=src_path,
            dest_path=dest_path,
            quality=proj_cfg["quality"],
            method=proj_cfg["method"],
            max_width=proj_cfg["max_width"]
        )
        new_bytes = os.path.getsize(dest_path)
        results.append({
            "category": "Project UI",
            "original_file": os.path.relpath(src_path, WORKSPACE_DIR),
            "new_file": os.path.relpath(dest_path, WORKSPACE_DIR),
            "orig_bytes": orig_bytes,
            "new_bytes": new_bytes,
            "orig_dims": orig_dims,
            "new_dims": new_dims,
            "mode": mode,
        })

    # 3. Process Favicon
    fav_cfg = CONFIG["favicon"]
    fav_path = os.path.join(fav_cfg["dir"], fav_cfg["file"])
    if os.path.exists(fav_path):
        fav_orig_bytes = os.path.getsize(fav_path)
        fav_dims, fav_mode = optimize_favicon(fav_path)
        fav_new_bytes = os.path.getsize(fav_path)
        results.append({
            "category": "Favicon (PNG Lossless)",
            "original_file": os.path.relpath(fav_path, WORKSPACE_DIR),
            "new_file": os.path.relpath(fav_path, WORKSPACE_DIR),
            "orig_bytes": fav_orig_bytes,
            "new_bytes": fav_new_bytes,
            "orig_dims": fav_dims,
            "new_dims": fav_dims,
            "mode": fav_mode,
        })

    # Summary Output
    print("\n" + "=" * 95)
    print(f"{'Original File':<35} | {'Optimized File':<30} | {'Orig Size':<10} | {'New Size':<10} | {'Diff':<8}")
    print("=" * 95)
    
    total_orig = sum(r["orig_bytes"] for r in results)
    total_new = sum(r["new_bytes"] for r in results)
    
    for r in results:
        orig_str = f"{r['orig_bytes']:,} B"
        new_str = f"{r['new_bytes']:,} B"
        diff_pct = ((r['new_bytes'] - r['orig_bytes']) / r['orig_bytes']) * 100
        print(f"{r['original_file']:<35} | {r['new_file']:<30} | {orig_str:>10} | {new_str:>10} | {diff_pct:>7.1f}%")
        
    print("=" * 95)
    print(f"Total Original:  {total_orig:,} bytes ({total_orig / (1024 * 1024):.2f} MB)")
    print(f"Total Optimized: {total_new:,} bytes ({total_new / (1024 * 1024):.2f} MB)")
    savings_bytes = total_orig - total_new
    savings_pct = (savings_bytes / total_orig) * 100
    print(f"Net Savings:     {savings_bytes:,} bytes ({savings_bytes / (1024 * 1024):.2f} MB) -> {savings_pct:.2f}% reduction")
    print("=" * 95)


if __name__ == "__main__":
    main()
