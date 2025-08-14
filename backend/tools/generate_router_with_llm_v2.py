#!/usr/bin/env python3
"""
Enhanced Smart Router Generator with LLM - Version 2
=======================================================

Sinh tự động các câu hỏi router examples bằng LLM thay vì template cố định.
Tối ưu hóa để sinh ra 10+ câu hỏi đa dạng từ metadata phong phú.

Sửa đổi: Trả về dictionary thay vì JSON string để tránh lỗi parsing.
"""

import json
import re
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import argparse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add app to Python path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from app.services.language_model import LLMService
except ImportError as e:
    logger.error(f"❌ Cannot import LLMService: {e}")
    logger.error("   Make sure you're in the backend directory and the service is available")
    sys.exit(1)

class SmartRouterLLMGenerator:
    """Enhanced router generator using LLM for question generation."""
    
    def __init__(self, documents_dir: str = None, output_dir: str = None):
        self.documents_dir = Path(documents_dir or "data/documents")
        self.output_dir = Path(output_dir or "data/router_examples_smart")
        
        # Initialize LLM service
        try:
            self.llm_service = LLMService()
            logger.info(f"✅ LLM Service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM Service: {e}")
            raise

    def _detect_collection_from_path(self, file_path: str) -> str:
        """Detect collection name from file path."""
        path_lower = file_path.lower()
        
        if 'hanh_chinh' in path_lower:
            return 'administrative_procedures'
        elif 'kinh_doanh' in path_lower:
            return 'business_procedures'
        elif 'dat_dai' in path_lower:
            return 'land_procedures'
        elif 'xay_dung' in path_lower:
            return 'construction_procedures'
        elif 'tu_phap' in path_lower:
            return 'judicial_procedures'
        else:
            return 'general_procedures'

    def analyze_document_metadata(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze document metadata for smart filtering."""
        metadata = doc.get('metadata', {})
        smart_filters = {}
        
        # Fee analysis
        fee_text = metadata.get('fee_text', '') or metadata.get('fee', '')
        if fee_text:
            fee_lower = fee_text.lower()
            if 'miễn phí' in fee_lower or 'không phí' in fee_lower:
                smart_filters['has_fee'] = False
            else:
                smart_filters['has_fee'] = True
        
        # Processing time
        processing_time = metadata.get('processing_time_text', '') or metadata.get('processing_time', '')
        if processing_time:
            time_normalized = processing_time.lower()
            if 'ngay' in time_normalized:
                smart_filters['processing_speed'] = 'fast'
            elif 'tuần' in time_normalized or 'tháng' in time_normalized:
                smart_filters['processing_speed'] = 'slow'
        
        return {
            'metadata': metadata,
            'smart_filters': smart_filters,
            'confidence_threshold': 0.75,
            'priority_score': 1.0
        }

    def generate_questions_with_llm(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Sử dụng LLM để sinh ra câu hỏi chính và các biến thể."""
        metadata = doc.get('metadata', {})
        document_title = metadata.get('title', 'Thủ tục chưa xác định')
        
        # Tạo một chuỗi tóm tắt nội dung tài liệu để đưa vào prompt
        document_content_summary = self._summarize_document_for_prompt(doc)

        # Prompt tối ưu hóa - ngắn gọn và hiệu quả
        user_query = f"""NHIỆM VỤ: Tạo chính xác 10 câu hỏi về thủ tục "{document_title}"

THÔNG TIN: {document_content_summary}

YÊU CẦU: Tạo 10 câu hỏi ngắn gọn, mỗi câu một dòng, đánh số từ 1-10. Mỗi câu phải khác nhau hoàn toàn.

VÍ DỤ FORMAT:
1. Thủ tục này là gì?
2. Ai có thể làm?
3. Cần giấy tờ gì?
4. Chi phí bao nhiêu?
5. Làm ở đâu?
6. Mất bao lâu?
7. Làm online được không?
8. Nhận kết quả như thế nào?
9. Có điều kiện gì đặc biệt?
10. Lưu ý gì khi làm?

BẮT ĐẦU TẠO 10 CÂU HỎI:"""

        # System prompt ngắn gọn và chỉ thị rõ ràng
        system_prompt = "Tạo chính xác 10 câu hỏi ngắn. Đánh số 1-10. Không giải thích thêm."
        
        # Thêm retry logic để xử lý LLM không ổn định
        max_retries = 2
        for attempt in range(max_retries):
            try:
                logger.info(f"   🤖 Calling LLM (Attempt {attempt + 1}/{max_retries}) for: '{document_title}'")
                response_data = self.llm_service.generate_response(
                    user_query=user_query,
                    max_tokens=500,  # Giảm để tránh repetition
                    temperature=0.3,  # Tăng một chút để có đa dạng
                    system_prompt=system_prompt  # Sử dụng system prompt riêng
                )
                
                # Trích xuất và làm sạch từ phản hồi của LLM
                response_text = response_data.get('response', '')
                logger.info(f"   📝 LLM Response (first 200 chars): {response_text[:200]}...")
                
                generated_data = self._extract_questions_from_llm_response(response_text, document_title)
                
                if generated_data:
                    # Clean up questions
                    generated_data['main_question'] = self._clean_question(generated_data['main_question'])
                    generated_data['question_variants'] = [
                        self._clean_question(q) for q in generated_data['question_variants'] if q.strip()
                    ]
                    
                    logger.info(f"   ✅ LLM generated {1 + len(generated_data['question_variants'])} questions.")
                    return generated_data  # Thành công - thoát khỏi retry loop
                else:
                    raise ValueError("No valid questions found in LLM response")

            except Exception as e:
                logger.warning(f"   ⚠️ Attempt {attempt + 1} failed for '{document_title}': {e}")
                if attempt + 1 == max_retries:
                    logger.error(f"   ❌ All attempts failed for '{document_title}'. Using fallback.")
                    # Fallback: Trả về một câu hỏi cơ bản nếu LLM thất bại hoàn toàn
                    return {
                        "main_question": f"Thủ tục {document_title} cần những gì?",
                        "question_variants": [
                            f"Hồ sơ {document_title} ra sao?",
                            f"Chi phí {document_title} là bao nhiêu?",
                            f"Làm {document_title} ở đâu?"
                        ]
                    }
                time.sleep(1)  # Chờ 1 giây trước khi thử lại
        
        # Shouldn't reach here, but just in case
        return {
            "main_question": f"Thủ tục {document_title} cần những gì?",
            "question_variants": [
                f"Hồ sơ {document_title} ra sao?",
                f"Chi phí {document_title} là bao nhiêu?"
            ]
        }

    def _clean_question(self, question: str) -> str:
        """Clean up generated questions"""
        if not question:
            return question
            
        # Remove numbering, bullet points, and extra whitespace
        question = re.sub(r'^[\d\-\*\+\.\)]\s*', '', question).strip()
        
        # Remove quotes and extra whitespace
        question = question.strip().strip('"').strip("'").strip()
        
        # Remove trailing underscores and parenthetical examples
        question = re.sub(r'\s*_+\s*$', '', question)  # Remove trailing ___
        question = re.sub(r'\s*\([^)]*\)\s*$', '', question)  # Remove (examples) at end
        
        # Ensure question ends with question mark
        if question and not question.endswith('?'):
            question += '?'
            
        # Limit question length to avoid overly long questions
        if len(question) > 100:
            question = question[:97] + "...?"
            
        return question

    def _summarize_document_for_prompt(self, doc: Dict[str, Any]) -> str:
        """Tạo một bản tóm tắt chi tiết từ file JSON để làm input cho LLM."""
        parts = []
        metadata = doc.get("metadata", {})
        
        # Basic info với nhiều chi tiết hơn
        applicant_types = metadata.get('applicant_type', ['Cá nhân'])
        if isinstance(applicant_types, list):
            parts.append(f"Đối tượng: {', '.join(applicant_types)}")
        else:
            parts.append(f"Đối tượng: {applicant_types}")
        
        parts.append(f"Cơ quan thực hiện: {metadata.get('executing_agency', 'N/A')}")
        parts.append(f"Thời gian xử lý: {metadata.get('processing_time_text', metadata.get('processing_time', 'N/A'))}")
        parts.append(f"Lệ phí: {metadata.get('fee_text', metadata.get('fee', 'N/A'))}")
        
        # Thêm thông tin về submission method
        submission_method = metadata.get('submission_method', [])
        if submission_method:
            if isinstance(submission_method, list):
                parts.append(f"Cách nộp hồ sơ: {', '.join(submission_method)}")
            else:
                parts.append(f"Cách nộp hồ sơ: {submission_method}")
        
        # Thêm thông tin về result delivery
        result_delivery = metadata.get('result_delivery', [])
        if result_delivery:
            if isinstance(result_delivery, list):
                parts.append(f"Cách nhận kết quả: {', '.join(result_delivery)}")
            else:
                parts.append(f"Cách nhận kết quả: {result_delivery}")
        
        # Content chunks - get key information từ nhiều sections
        content_chunks = doc.get("content_chunks", [])
        if content_chunks:
            # Tìm section hồ sơ
            hoso_chunk = next((c for c in content_chunks if "hồ sơ" in c.get("section_title", "").lower()), None)
            if hoso_chunk:
                content = hoso_chunk.get('content', '')[:400]  # Tăng giới hạn
                parts.append(f"Thành phần hồ sơ: {content}...")
            
            # Tìm section quy trình
            quytrình_chunk = next((c for c in content_chunks if any(keyword in c.get("section_title", "").lower() 
                                                                    for keyword in ["quy trình", "thủ tục", "cách thức"])), None)
            if quytrình_chunk and quytrình_chunk != hoso_chunk:
                content = quytrình_chunk.get('content', '')[:300]
                parts.append(f"Quy trình thực hiện: {content}...")
            
            # Tìm section điều kiện/yêu cầu
            dieukien_chunk = next((c for c in content_chunks if any(keyword in c.get("section_title", "").lower() 
                                                                   for keyword in ["điều kiện", "yêu cầu", "đối tượng"])), None)
            if dieukien_chunk and dieukien_chunk != hoso_chunk and dieukien_chunk != quytrình_chunk:
                content = dieukien_chunk.get('content', '')[:200]
                parts.append(f"Điều kiện/Yêu cầu: {content}...")

        return ". ".join(parts)
        
    def _extract_questions_from_llm_response(self, text: str, document_title: str) -> Optional[Dict]:
        """Trích xuất và tạo dictionary từ text response của LLM."""
        if not text:
            return None
            
        # Strategy 1: Tìm JSON sẵn có
        json_match = re.search(r'\{.*?"main_question".*?"question_variants".*?\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        # Strategy 2: Extract từ text response thông thường với deduplication
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        questions = []
        seen_questions = set()  # Để tránh trùng lặp
        
        # Lọc ra những dòng chứa câu hỏi (có đánh số hoặc kết thúc bằng dấu ?)
        for line in lines:
            # Remove numbering và bullet points
            cleaned_line = re.sub(r'^[\d\-\*\+\.\)]\s*', '', line).strip()
            
            # Lọc câu hỏi dài hơn 5 ký tự và có dấu ? hoặc có từ khóa câu hỏi
            if (cleaned_line.endswith('?') or any(keyword in cleaned_line.lower() 
                                                 for keyword in ['gì', 'như thế nào', 'bao nhiêu', 'ở đâu', 'khi nào', 'ai'])) and len(cleaned_line) > 5:
                # Tránh trùng lặp bằng cách kiểm tra similarity
                is_duplicate = any(self._are_questions_similar(cleaned_line.lower(), seen) 
                                 for seen in seen_questions)
                if not is_duplicate:
                    if not cleaned_line.endswith('?'):
                        cleaned_line += '?'  # Thêm dấu ? nếu chưa có
                    questions.append(cleaned_line)
                    seen_questions.add(cleaned_line.lower())
        
        if len(questions) >= 1:
            # Chọn câu hỏi chính - ưu tiên câu hỏi tổng quan
            main_question = questions[0]
            
            # Tìm câu hỏi tổng quan tốt hơn nếu có
            for q in questions[:3]:  # Chỉ xem 3 câu đầu
                if any(keyword in q.lower() for keyword in ["là gì", "như thế nào", "thủ tục", "quy trình"]):
                    main_question = q
                    break
            
            # Lấy tất cả câu hỏi còn lại làm variants, tối đa 12 câu
            question_variants = [q for q in questions if q != main_question][:12]
            
            return {
                "main_question": main_question,
                "question_variants": question_variants
            }
        
        # Strategy 3: Fallback với template questions
        return {
            "main_question": f"Thủ tục {document_title} là gì?",
            "question_variants": [
                f"Làm {document_title} cần giấy tờ gì?",
                f"Chi phí {document_title} bao nhiêu?",
                f"Thời gian xử lý {document_title} là bao lâu?",
                f"Làm {document_title} ở đâu?",
                f"Có thể làm {document_title} online không?",
                f"Nhận kết quả {document_title} thế nào?"
            ]
        }
        
    def _are_questions_similar(self, q1: str, q2: str, threshold: float = 0.7) -> bool:
        """Kiểm tra 2 câu hỏi có tương tự nhau không để tránh trùng lặp."""
        # Simple similarity check dựa trên từ khóa chính
        keywords1 = set(re.findall(r'\w+', q1.lower()))
        keywords2 = set(re.findall(r'\w+', q2.lower()))
        
        if not keywords1 or not keywords2:
            return False
        
        # Jaccard similarity
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union > threshold if union > 0 else False

    def generate_all_smart_examples(self, force_rebuild: bool = False) -> int:
        """Sinh tất cả smart router examples bằng LLM."""
        logger.info("🎯 Generating smart router examples using LLM v2...")
        
        if not self.documents_dir.exists():
            logger.error(f"❌ Documents directory not found: {self.documents_dir}")
            return 0
        
        json_files = sorted(list(self.documents_dir.rglob("*.json")))
        if not json_files:
            logger.error("❌ No JSON documents found")
            return 0
        
        logger.info(f"   📄 Found {len(json_files)} JSON files to process.")
        
        total_examples = 0
        processed_files = 0
        
        for i, json_file in enumerate(json_files):
            logger.info("-" * 60)
            logger.info(f"Processing file {i+1}/{len(json_files)}: {json_file.name}")
            
            relative_path = json_file.relative_to(self.documents_dir)
            output_file = self.output_dir / relative_path

            if not force_rebuild and output_file.exists():
                logger.info(f"   ⏩ Skipping, router file already exists. Use --force to overwrite.")
                continue

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    doc = json.load(f)
                
                # 1. PHÂN TÍCH METADATA
                analysis = self.analyze_document_metadata(doc)
                collection_name = self._detect_collection_from_path(str(json_file))
                
                # 2. SINH CÂU HỎI BẰNG LLM
                questions = self.generate_questions_with_llm(doc)
                
                # 3. TẠO VÀ LƯU FILE ROUTER
                router_data = {
                    'metadata': {
                        'title': doc.get('metadata', {}).get('title', ''),
                        'code': doc.get('metadata', {}).get('code', ''),
                        'collection': collection_name,
                        'source_document': str(relative_path),
                        'generated_by': 'llm_powered_generator_v2.0',
                        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
                    },
                    'main_question': questions['main_question'],
                    'question_variants': questions.get('question_variants', []),
                    'smart_filters': analysis['smart_filters'],
                    'expected_collection': collection_name,
                    'confidence_threshold': analysis.get('confidence_threshold', 0.75),
                    'priority_score': analysis.get('priority_score', 1.0)
                }
                
                # Ensure output directory exists
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Save router data
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(router_data, f, ensure_ascii=False, indent=2)
                
                processed_files += 1
                num_questions = 1 + len(questions.get('question_variants', []))
                total_examples += num_questions
                logger.info(f"   💾 Saved {num_questions} examples to {output_file.name}")
                
                # Thêm một khoảng nghỉ nhỏ để không làm LLM quá tải
                time.sleep(0.5) 

            except Exception as e:
                logger.error(f"   ⚠️ Error processing {json_file.name}: {e}")
                continue
        
        # Tạo file tóm tắt
        self._generate_summary(processed_files, total_examples, json_files)
        return processed_files

    def _generate_summary(self, processed_files: int, total_examples: int, json_files: List[Path]):
        """Tạo file tóm tắt kết quả."""
        collections = {}
        for json_file in json_files:
            collection = self._detect_collection_from_path(str(json_file))
            collections[collection] = collections.get(collection, 0) + 1
        
        summary = {
            'generator_info': {
                'version': 'llm_powered_v2.0',
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'llm_model': 'PhoGPT-4B-Chat'
            },
            'statistics': {
                'total_files_processed': processed_files,
                'total_source_files': len(json_files),
                'total_examples_generated': total_examples,
                'collections_distribution': collections
            },
            'quality_metrics': {
                'avg_variants_per_document': total_examples / processed_files if processed_files > 0 else 0,
                'success_rate': (processed_files / len(json_files)) * 100 if json_files else 0
            }
        }
        
        summary_file = self.output_dir / "llm_generation_summary_v2.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n📊 Summary saved to {summary_file}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Generate smart router examples using LLM v2')
    parser.add_argument('--force', action='store_true', help='Force rebuild existing examples')
    parser.add_argument('--docs', type=str, default='data/documents', help='Documents directory')
    parser.add_argument('--output', type=str, default='data/router_examples_smart', help='Output directory')
    
    args = parser.parse_args()
    
    try:
        generator = SmartRouterLLMGenerator(args.docs, args.output)
        
        logger.info("🚀 Starting LLM-powered Smart Router Generation v2...")
        start_time = time.time()
        
        processed_count = generator.generate_all_smart_examples(force_rebuild=args.force)
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info("=" * 60)
        logger.info(f"✅ Generation completed!")
        logger.info(f"   📊 Processed: {processed_count} files")
        logger.info(f"   ⏱️  Duration: {duration:.2f} seconds")
        logger.info(f"   📁 Output: {args.output}")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Process interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
