# QR Scanner Improvement Plan - TODO List Chi Tiết

## Phase 1: Chuẩn hóa ảnh đầu vào (Image Normalization)

### ✅ Bước 1.1: Thêm Image Preprocessing Pipeline

- [ ] Tạo class `ImagePreprocessor` trong `app/services/`
- [ ] Implement resize chuẩn (width=1200px, keep aspect ratio)
- [ ] Implement noise reduction (medianBlur, bilateralFilter)
- [ ] Integrate vào QRScanner constructor
- [ ] Test với các ảnh sample khác nhau

### ✅ Bước 1.2: Optimize Resize Strategy

- [ ] Benchmark performance với các resolution khác nhau (800px, 1000px, 1200px, 1500px)
- [ ] Tạo adaptive resize (dựa vào kích thước ảnh gốc)
- [ ] Add logging cho image size before/after
- [ ] Validate memory usage

### ✅ Bước 1.3: Enhanced Noise Reduction

- [ ] Compare performance: GaussianBlur vs MedianBlur vs BilateralFilter
- [ ] Implement multi-stage noise reduction
- [ ] Add edge preservation techniques
- [ ] Test với ảnh có nhiều noise level

## Phase 2: Tối ưu quy trình quét QR (Optimized QR Detection Pipeline)

### ✅ Bước 2.1: Restructure Detection Pipeline

- [ ] Refactor `_multi_stage_qr_detection` theo thứ tự mới:
  1. **Fast Scan**: Direct pyzbar + OpenCV QR on normalized image
  2. **Enhanced Full Image**: Apply filters to whole image
  3. **Card Detection & Region Scan**: Only if above fails
  4. **Corner Scan**: Last resort on detected card corners
- [ ] Add timing logs cho từng stage
- [ ] Add success rate tracking

### ✅ Bước 2.2: Fast Scan Optimization

- [ ] Combine pyzbar và cv2.QRCodeDetector trong 1 pass
- [ ] Optimize grayscale conversion (cache result)
- [ ] Add early return mechanism
- [ ] Minimize memory allocation

### ✅ Bước 2.3: Smart Enhancement Strategy

- [ ] Prioritize enhancement techniques theo success rate
- [ ] Implement adaptive enhancement (stop khi detect được)
- [ ] Add quality scoring cho enhanced images
- [ ] Cache enhancement results

## Phase 3: Cải thiện Card Detection (Robust Card Detection)

### ✅ Bước 3.1: Advanced Contour Filtering

- [ ] Add contour "solidity" check (area/convex_hull_area ratio)
- [ ] Implement Hough Line Transform alternative
- [ ] Add perspective correction validation
- [ ] Improve aspect ratio tolerance

### ✅ Bước 3.2: Multi-Method Card Detection

- [ ] Implement Hough Lines approach
- [ ] Add template matching (nếu có reference card shape)
- [ ] Combine edge detection với color segmentation
- [ ] Add confidence scoring cho detection methods

### ✅ Bước 3.3: Fallback Strategies

- [ ] Grid-based scanning (divide image into regions)
- [ ] Histogram analysis cho card background
- [ ] Add manual override parameters
- [ ] Implement "no card mode" option

## Phase 4: Performance & Reliability (Testing & Optimization)

### ✅ Bước 4.1: Comprehensive Testing

- [ ] Create test dataset với diverse conditions:
  - Different lighting conditions
  - Various backgrounds
  - Multiple angles
  - Different image qualities
- [ ] Implement automated testing pipeline
- [ ] Add performance benchmarks
- [ ] Create success rate metrics

### ✅ Bước 4.2: Error Handling & Logging

- [ ] Add detailed error categorization
- [ ] Implement retry mechanism với different parameters
- [ ] Add debug image output option
- [ ] Create failure analysis tools

### ✅ Bước 4.3: Configuration Management

- [ ] Move hardcoded parameters to config file
- [ ] Add runtime parameter adjustment
- [ ] Implement A/B testing framework
- [ ] Create tuning utilities

## Phase 5: Integration & Deployment (System Integration)

### ✅ Bước 5.1: API Improvements

- [ ] Add processing mode selection (fast/thorough/auto)
- [ ] Implement batch processing
- [ ] Add image quality assessment endpoint
- [ ] Create debug/analysis endpoints

### ✅ Bước 5.2: Monitoring & Analytics

- [ ] Add performance metrics collection
- [ ] Implement success rate tracking
- [ ] Create dashboard cho monitoring
- [ ] Add alerting cho performance issues

### ✅ Bước 5.3: Documentation & Deployment Scripts

- [ ] Create deployment scripts với conda environment
- [ ] Add comprehensive API documentation
- [ ] Create troubleshooting guide
- [ ] Implement health check endpoints

## Automated Deployment Script

### Script Requirements:

1. Activate conda environment `identifill_env`
2. Navigate to service directory
3. Run main.py với proper parameters
4. Handle environment variables
5. Add logging và error handling

---

## Priority Order:

1. **HIGH**: Phase 1 (Image Normalization) - Foundation cho all improvements
2. **HIGH**: Phase 2 (Pipeline Optimization) - Direct impact on success rate
3. **MEDIUM**: Phase 3 (Card Detection) - Fallback improvements
4. **MEDIUM**: Phase 4 (Testing) - Validation và reliability
5. **LOW**: Phase 5 (Integration) - Polish và deployment

## Success Metrics:

- QR Detection success rate: Target >90% (from current ~70-80%)
- Average processing time: Target <2s per image
- False positive rate: Target <5%
- Memory usage: Keep under 500MB per request

## Timeline Estimate:

- Phase 1: 2-3 days
- Phase 2: 3-4 days
- Phase 3: 2-3 days
- Phase 4: 2-3 days
- Phase 5: 1-2 days

**Total**: ~10-15 days for complete implementation
