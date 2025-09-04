#!/usr/bin/env python
"""
Run script to test WeChat QRCode scanner performance
This script is for quickly testing the scanner without needing to run the full FastAPI server
"""

import os
import sys
import base64
import cv2
import numpy as np
from pathlib import Path
import time
import argparse
import json

# Add app directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Import QR scanner
from app.services.qr_scanner import QRCodeScanner


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Test QR code scanner performance')
    parser.add_argument('--image', '-i', 
                        help='Path to an image to scan')
    parser.add_argument('--dir', '-d', default='test_images',
                        help='Directory of test images (default: test_images)')
    parser.add_argument('--report', '-r', action='store_true',
                        help='Generate performance report')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed output')
    
    return parser.parse_args()


def test_single_image(image_path, scanner, verbose=False):
    """Test QR scanner with a single image"""
    # Read image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"Error: Cannot read image {image_path}")
        return {
            "success": False,
            "image": str(image_path),
            "error": "Cannot read image"
        }
    
    # Convert to base64
    _, buffer = cv2.imencode('.jpg', image)
    base64_string = base64.b64encode(buffer.tobytes()).decode('utf-8')
    
    # Scan QR code
    start_time = time.time()
    result = scanner.scan_qr_from_base64(base64_string)
    elapsed_time = time.time() - start_time
    
    # Process result
    if result.success:
        print(f"✅ {image_path.name}: QR detected in {elapsed_time:.2f}s")
        if verbose and hasattr(result, 'data'):
            print(f"   Data: {result.data}")
    else:
        print(f"❌ {image_path.name}: Failed - {result.message} ({elapsed_time:.2f}s)")
    
    # Return result data
    result_data = {
        "success": result.success,
        "image": str(image_path),
        "time": elapsed_time,
        "message": result.message
    }
    
    if result.success and hasattr(result, 'data'):
        result_data["data"] = result.data.__dict__ if hasattr(result.data, '__dict__') else str(result.data)
    
    return result_data


def test_directory(dir_path, scanner, verbose=False):
    """Test QR scanner with all images in a directory"""
    # Find image files
    image_files = []
    for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
        image_files.extend(list(Path(dir_path).glob(f"*{ext}")))
    
    if not image_files:
        print(f"No images found in {dir_path}")
        return []
    
    # Process each image
    results = []
    print(f"Testing {len(image_files)} images from {dir_path}...")
    
    for image_path in image_files:
        result = test_single_image(image_path, scanner, verbose)
        results.append(result)
    
    return results


def generate_report(results):
    """Generate a performance report"""
    if not results:
        print("No results to report")
        return
    
    # Calculate statistics
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    
    success_rate = (successful / total) * 100 if total > 0 else 0
    avg_time = sum(r["time"] for r in results) / total if total > 0 else 0
    
    # Print report
    print("\n" + "=" * 60)
    print("PERFORMANCE REPORT")
    print("=" * 60)
    print(f"Total images: {total}")
    print(f"Successful: {successful} ({success_rate:.1f}%)")
    print(f"Failed: {failed}")
    print(f"Average time: {avg_time:.3f}s")
    
    # Save report
    report_file = "qr_scanner_report.json"
    with open(report_file, 'w') as f:
        json.dump({
            "summary": {
                "total": total,
                "successful": successful,
                "failed": failed,
                "success_rate": success_rate,
                "average_time": avg_time
            },
            "results": results
        }, f, indent=2)
    
    print(f"Detailed report saved to {report_file}")


def main():
    """Main function"""
    args = parse_args()
    
    # Initialize scanner
    print("Initializing QR scanner...")
    scanner = QRCodeScanner()
    
    # Run tests
    results = []
    
    if args.image:
        # Test single image
        image_path = Path(args.image)
        if not image_path.exists():
            print(f"Error: Image {args.image} not found")
            return
        
        results = [test_single_image(image_path, scanner, args.verbose)]
    else:
        # Test directory
        dir_path = args.dir
        if not os.path.exists(dir_path):
            print(f"Error: Directory {dir_path} not found")
            return
        
        results = test_directory(dir_path, scanner, args.verbose)
    
    # Generate report if requested
    if args.report:
        generate_report(results)


if __name__ == "__main__":
    main()
