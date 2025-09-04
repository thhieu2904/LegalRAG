"""
Test script for QR Scanner improvements
Tests the new preprocessing pipeline and optimized detection stages
"""

import base64
import cv2
import numpy as np
import time
import json
from pathlib import Path
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.qr_scanner import QRCodeScanner
from app.services.image_preprocessor import ImagePreprocessor

def load_test_images(test_dir: str = "test_images"):
    """Load test images from directory"""
    test_images = []
    
    if not os.path.exists(test_dir):
        print(f"Test directory '{test_dir}' not found. Creating sample data...")
        return []
    
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    
    for file_path in Path(test_dir).glob("*"):
        if file_path.suffix.lower() in image_extensions:
            image = cv2.imread(str(file_path))
            if image is not None:
                # Convert to base64 for testing
                _, buffer = cv2.imencode('.jpg', image)
                b64_string = base64.b64encode(buffer.tobytes()).decode()
                
                test_images.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'data': b64_string,
                    'original_image': image
                })
    
    return test_images

def test_image_preprocessor():
    """Test the image preprocessor functionality"""
    print("=" * 60)
    print("TESTING IMAGE PREPROCESSOR")
    print("=" * 60)
    
    preprocessor = ImagePreprocessor()
    print(f"Configuration: {preprocessor.get_preprocessing_info()}")
    print()
    
    # Create test images with different characteristics
    test_cases = [
        ("Very Large", np.random.randint(0, 255, (3000, 4000, 3), dtype=np.uint8)),
        ("Small", np.random.randint(0, 255, (300, 400, 3), dtype=np.uint8)),
        ("Target Size", np.random.randint(0, 255, (800, 1200, 3), dtype=np.uint8)),
        ("Noisy", np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)),
    ]
    
    for name, test_image in test_cases:
        print(f"Testing {name} Image:")
        print(f"  Original: {test_image.shape[1]}x{test_image.shape[0]}")
        
        # Add noise to the noisy image
        if name == "Noisy":
            noise = np.random.normal(0, 25, test_image.shape)
            test_image = np.clip(test_image.astype(np.float64) + noise, 0, 255).astype(np.uint8)
        
        # Analyze original properties
        original_props = ImagePreprocessor.analyze_image_properties(test_image)
        print(f"  Original quality metrics:")
        print(f"    Brightness: {original_props['quality']['mean_brightness']:.1f}")
        print(f"    Contrast: {original_props['quality']['contrast_rms']:.1f}")
        print(f"    Noise level: {original_props['estimated_noise_level']:.1f}")
        
        # Process image
        start_time = time.time()
        processed = preprocessor.preprocess_image(test_image)
        process_time = time.time() - start_time
        
        # Analyze processed properties
        processed_props = ImagePreprocessor.analyze_image_properties(processed)
        print(f"  Processed: {processed.shape[1]}x{processed.shape[0]} "
              f"({process_time:.3f}s)")
        print(f"  Processed quality metrics:")
        print(f"    Brightness: {processed_props['quality']['mean_brightness']:.1f}")
        print(f"    Contrast: {processed_props['quality']['contrast_rms']:.1f}")
        print(f"    Noise level: {processed_props['estimated_noise_level']:.1f}")
        print()

def test_qr_scanner_performance(test_images):
    """Test QR scanner performance with different images"""
    print("=" * 60)
    print("TESTING QR SCANNER PERFORMANCE")
    print("=" * 60)
    
    scanner = QRCodeScanner()
    results = []
    
    if not test_images:
        print("No test images found. Creating synthetic test...")
        # Create a simple synthetic QR code for testing
        test_images = create_synthetic_qr_test()
    
    for i, test_image in enumerate(test_images):
        print(f"Testing image {i+1}/{len(test_images)}: {test_image['name']}")
        
        start_time = time.time()
        response = scanner.scan_qr_from_base64(test_image['data'])
        total_time = time.time() - start_time
        
        result = {
            'image_name': test_image['name'],
            'success': response.success,
            'processing_time': response.processing_time if hasattr(response, 'processing_time') else total_time,
            'total_time': total_time,
            'message': response.message,
            'confidence': response.confidence if hasattr(response, 'confidence') else 0.0
        }
        
        if response.success and response.data:
            result['data_found'] = True
            result['parsed_fields'] = len(response.data.__dict__) if response.data else 0
        else:
            result['data_found'] = False
            result['parsed_fields'] = 0
        
        results.append(result)
        
        print(f"  Result: {'✓ SUCCESS' if response.success else '✗ FAILED'}")
        print(f"  Time: {total_time:.3f}s")
        print(f"  Message: {response.message}")
        if response.success and hasattr(response, 'confidence'):
            print(f"  Confidence: {response.confidence:.2f}")
        print()
    
    return results

def create_synthetic_qr_test():
    """Create synthetic QR code for testing when no real images available"""
    print("Creating synthetic QR test data...")
    
    # Create a simple image with text (simulating a QR code scenario)
    test_image = np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    # Add some noise and patterns
    cv2.rectangle(test_image, (100, 100), (300, 300), (0, 0, 0), 2)
    cv2.rectangle(test_image, (500, 200), (700, 400), (128, 128, 128), -1)
    
    # Convert to base64
    _, buffer = cv2.imencode('.jpg', test_image)
    b64_string = base64.b64encode(buffer.tobytes()).decode()
    
    return [{
        'name': 'synthetic_test.jpg',
        'path': 'synthetic',
        'data': b64_string,
        'original_image': test_image
    }]

def generate_performance_report(results):
    """Generate a performance report"""
    print("=" * 60)
    print("PERFORMANCE REPORT")
    print("=" * 60)
    
    if not results:
        print("No results to analyze.")
        return
    
    total_images = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total_images - successful
    
    success_rate = (successful / total_images) * 100
    avg_time = sum(r['total_time'] for r in results) / total_images
    
    print(f"Total Images Tested: {total_images}")
    print(f"Successful Scans: {successful}")
    print(f"Failed Scans: {failed}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Average Processing Time: {avg_time:.3f}s")
    print()
    
    if successful > 0:
        successful_results = [r for r in results if r['success']]
        avg_success_time = sum(r['total_time'] for r in successful_results) / len(successful_results)
        print(f"Average Time for Successful Scans: {avg_success_time:.3f}s")
        print()
    
    print("Individual Results:")
    print("-" * 40)
    for result in results:
        status = "✓" if result['success'] else "✗"
        print(f"{status} {result['image_name']:<25} {result['total_time']:.3f}s")
        if not result['success']:
            print(f"  Error: {result['message']}")
    
    # Save detailed results
    report_file = "qr_scanner_test_report.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print()
    print(f"Detailed report saved to: {report_file}")

def main():
    """Main test function"""
    print("QR SCANNER IMPROVEMENT TESTING")
    print("=" * 60)
    print()
    
    # Test 1: Image Preprocessor
    print("Starting Image Preprocessor tests...")
    test_image_preprocessor()
    
    # Test 2: Load test images
    print("Loading test images...")
    test_images = load_test_images()
    print(f"Loaded {len(test_images)} test images")
    print()
    
    # Test 3: QR Scanner Performance
    print("Starting QR Scanner performance tests...")
    results = test_qr_scanner_performance(test_images)
    
    # Test 4: Generate Report
    generate_performance_report(results)
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    main()
