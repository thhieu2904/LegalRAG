#!/usr/bin/env python3
"""
LLM-Powered Smart Router Examples Generator for LegalRAG
=========================================================

Nâng cấp tool tạo router examples bằng cách sử dụng LLM (PhoGPT-4B) để
sinh ra các câu hỏi đa dạng và có chiều sâu ngữ nghĩa hơn, thay thế
cho các template cứng.

Logic cốt lõi:
1.  Giữ lại toàn bộ phần phân tích metadata và smart filters từ tool cũ.
2.  Sử dụng LLMService để đọc nội dung tài liệu và sinh ra bộ câu hỏi
    phong phú dựa trên kỹ thuật prompt "đóng vai".
3.  Tự động hóa việc tạo dữ liệu chất lượng cao cho Router.

Usage:
    cd backend
    python tools/4_generate_router_with_llm.py
    python tools/4_generate_router_with_llm.py --force  # Rebuild existing
"""

import sys
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import argparse
import time

# --- SETUP PATH ---
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
# --- END SETUP PATH ---

# --- IMPORT CÁC THÀNH PHẦN TỪ DỰ ÁN ---
from app.services.language_model import LLMService
from app.core.config import settings

# --- SETUP LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SmartRouterLLMGenerator:
    """
    LLM-powered generator cho smart router examples
    """
    def __init__(self, documents_dir: str, output_dir: str, llm_service: LLMService):
        self.documents_dir = Path(documents_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llm_service = llm_service
        
        # Collection mapping
        self.collection_mapping = {
            'chung_thuc': ['chung_thuc', 'chung-thuc', 'công chứng', 'chung thực'],
            'ho_tich_cap_xa': ['ho_tich', 'hộ tịch', 'khai sinh', 'cap_xa', 'cấp xã', 'ủy ban'],
            'nuoi_con_nuoi': ['nuoi_con_nuoi', 'nuôi con nuôi', 'nhận nuôi', 'con nuôi']
        }
        
        logger.info("🧠 LLM-Powered Generator initialized.")

    def _detect_collection_from_path(self, file_path: str) -> str:
        """Detect collection from file path"""
        path_lower = file_path.lower()
        
        # Check file path for collection indicators
        for collection, keywords in self.collection_mapping.items():
            for keyword in keywords:
                if keyword.replace('_', ' ') in path_lower or keyword.replace(' ', '_') in path_lower:
                    return collection
        
        # Default fallback based on path components
        if 'chung' in path_lower:
            return 'chung_thuc'
        elif 'ho_tich' in path_lower or 'khai_sinh' in path_lower:
            return 'ho_tich_cap_xa'
        elif 'nuoi' in path_lower:
            return 'nuoi_con_nuoi'
        
        return 'chung_thuc'  # Default

    def analyze_document_metadata(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Phân tích metadata của document để tạo smart filters"""
        metadata = doc.get('metadata', {})
        
        # Basic metadata extraction
        title = metadata.get('title', '')
        code = metadata.get('code', '')
        applicant_type = metadata.get('applicant_type', [])
        executing_agency = metadata.get('executing_agency', '')
        
        # Smart filters based on metadata
        smart_filters = {}
        
        # Applicant type filter
        if applicant_type:
            smart_filters['applicant_type'] = applicant_type
        
        # Agency filter
        if executing_agency:
            agency_normalized = executing_agency.lower()
            if 'ubnd' in agency_normalized or 'ủy ban' in agency_normalized:
                smart_filters['agency_level'] = 'local'
            elif 'bộ' in agency_normalized or 'trung ương' in agency_normalized:
                smart_filters['agency_level'] = 'central'
        
        # Fee detection
        fee_info = metadata.get('fee_text', '') or metadata.get('fee', '')
        if fee_info:
            fee_normalized = fee_info.lower()
            if 'miễn' in fee_normalized or 'không' in fee_normalized:
                smart_filters['has_fee'] = False
            elif 'đồng' in fee_normalized or 'vnđ' in fee_normalized:
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
        """
        Sử dụng LLM để sinh ra câu hỏi chính và các biến thể.
        """
        metadata = doc.get('metadata', {})
        document_title = metadata.get('title', 'Thủ tục chưa xác định')
        
        # Tạo một chuỗi tóm tắt nội dung tài liệu để đưa vào prompt
        document_content_summary = self._summarize_document_for_prompt(doc)

        # Prompt tối ưu hóa - ngắn gọn và hiệu quả
        user_query = f"""Tạo 10 câu hỏi khác nhau về thủ tục "{document_title}":

THÔNG TIN: {document_content_summary}

CÁC LOẠI CÂU HỎI CẦN TẠO:
- Thủ tục là gì? Ai làm được?
- Cần giấy tờ gì?
- Làm ở đâu? 
- Chi phí bao nhiêu?
- Mất bao lâu?
- Làm online được không?
- Nhận kết quả thế nào?
- Điều kiện gì?
- Quy trình ra sao?
- Lưu ý gì?

TẠO 10 CÂU HỎI NGẮN GỌN:"""

        # System prompt ngắn gọn
        system_prompt = "Tạo câu hỏi ngắn. Mỗi câu 1 dòng, đánh số. Không lặp lại."
        
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
                
                # Trích xuất và làm sạch chuỗi JSON từ phản hồi của LLM
                response_text = response_data.get('response', '{}')
                logger.info(f"   📝 LLM Response (first 200 chars): {response_text[:200]}...")
                
                generated_data = self._extract_json_from_llm_response(response_text, document_title)
                
                if generated_data:
                    # Đảm bảo có đủ key và value là list
                    if 'question_variants' not in generated_data or not isinstance(generated_data['question_variants'], list):
                        generated_data['question_variants'] = []
                    if 'main_question' not in generated_data:
                         generated_data['main_question'] = generated_data['question_variants'][0] if generated_data['question_variants'] else document_title
                    
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
        
        # Ensure question ends with question mark
        if question and not question.endswith('?'):
            question += '?'
            
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
            
            # Nếu không tìm được sections cụ thể, lấy chunk đầu tiên
            if not hoso_chunk and not quytrình_chunk and not dieukien_chunk and content_chunks:
                first_chunk = content_chunks[0]
                content = first_chunk.get('content', '')[:300]
                parts.append(f"Thông tin chính: {content}...")

        return ". ".join(parts)
        
    def _extract_json_from_llm_response(self, text: str) -> Optional[str]:
        """Trích xuất và tái tạo JSON từ text response của LLM."""
        if not text:
            return None
            
        # Strategy 1: Tìm JSON sẵn có
        json_match = re.search(r'\{.*?"main_question".*?"question_variants".*?\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        # Strategy 2: Extract từ text response thông thường
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        questions = []
        seen_questions = set()  # Để tránh trùng lặp
        
        # Lọc ra những dòng chứa câu hỏi (kết thúc bằng dấu ?)
        for line in lines:
            # Remove numbering và bullet points
            cleaned_line = re.sub(r'^[\d\-\*\+\.\)]\s*', '', line).strip()
            if cleaned_line.endswith('?') and len(cleaned_line) > 5:
                # Tránh trùng lặp
                if cleaned_line.lower() not in seen_questions:
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
            
            # Lấy tất cả câu hỏi còn lại làm variants, tối đa 10 câu
            question_variants = [q for q in questions if q != main_question][:10]
            
            # Tạo JSON object
            result = {
                "main_question": main_question,
                "question_variants": question_variants
            }
            return json.dumps(result, ensure_ascii=False)
        
        # Strategy 3: Tìm patterns phổ biến (fallback)
        main_q_patterns = [
            r'câu hỏi chính[:\-\s]*(.+\?)',
            r'main[_\s]question[:\-\s]*(.+\?)',
            r'(?:^|\n)(.+\?)',  # First question mark
        ]
        
        for pattern in main_q_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                main_question = match.group(1).strip()
                
                # Tìm thêm câu hỏi khác
                remaining_text = text[match.end():]
                variant_questions = re.findall(r'(.+\?)', remaining_text)
                
                # Clean up variants và tránh trùng lặp
                variants = []
                seen = set()
                for q in variant_questions[:8]:  # Lấy tối đa 8 variants
                    cleaned = re.sub(r'^[\d\-\*\+\.\)]\s*', '', q).strip()
                    if cleaned and cleaned != main_question and cleaned.lower() not in seen:
                        variants.append(cleaned)
                        seen.add(cleaned.lower())
                
                result = {
                    "main_question": main_question,
                    "question_variants": variants
                }
                return json.dumps(result, ensure_ascii=False)
        
        return None

    def generate_all_smart_examples(self, force_rebuild: bool = False) -> int:
        """
        Sinh tất cả smart router examples bằng LLM.
        """
        logger.info("🎯 Generating smart router examples using LLM...")
        
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
                        'generated_by': 'llm_powered_generator_v1.0',
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
                'version': 'llm_powered_v1.0',
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
        
        summary_file = self.output_dir / "llm_generation_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n📊 Summary saved to {summary_file}")
        logger.info(f"   ✅ Processed: {processed_files}/{len(json_files)} files")
        logger.info(f"   📝 Generated: {total_examples} total examples")
        logger.info(f"   📊 Success rate: {summary['quality_metrics']['success_rate']:.1f}%")


def main():
    parser = argparse.ArgumentParser(
        description='Generate smart router examples for LegalRAG using LLM.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force rebuild - overwrite existing router examples'
    )
    parser.add_argument(
        '--verify-llm',
        action='store_true',
        help='Only verify LLM service and exit'
    )
    args = parser.parse_args()

    # --- KHỞI TẠO CÁC THÀNH PHẦN CẦN THIẾT ---
    documents_dir = backend_dir / "data" / "documents"
    router_examples_dir = backend_dir / "data" / "router_examples_smart"
    
    if not documents_dir.exists() and not args.verify_llm:
        logger.error(f"❌ Documents directory not found: {documents_dir}")
        return 1

    logger.info("🧠 LLM-Powered Smart Router Examples Generator")
    logger.info("=" * 60)
    
    try:
        # Tải LLMService để sử dụng cho việc sinh câu hỏi
        logger.info("🚀 Initializing LLMService (this may take a moment)...")
        llm = LLMService()
        
        if not llm.is_loaded():
            raise RuntimeError("LLM failed to load. Please check config and model path.")
        
        logger.info("✅ LLMService initialized successfully.")
        
        # Show model info
        model_info = llm.get_model_info()
        logger.info(f"   📊 Model size: {model_info['model_size_mb']:.1f}MB")
        logger.info(f"   🔧 GPU layers: {model_info['model_kwargs'].get('n_gpu_layers', 0)}")
        
        if args.verify_llm:
            logger.info("🧪 Testing LLM with sample query...")
            test_response = llm.generate_response(
                user_query="Thủ tục khai sinh cần gì?",
                max_tokens=100,
                temperature=0.1
            )
            logger.info(f"   ✅ Test response: {test_response['response'][:100]}...")
            logger.info("✅ LLM verification successful!")
            return 0
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize LLMService: {e}")
        logger.error("   Please ensure your LLM model is properly installed.")
        logger.error(f"   Expected model path: {settings.llm_model_path}")
        return 1

    # Khởi tạo và chạy generator
    generator = SmartRouterLLMGenerator(str(documents_dir), str(router_examples_dir), llm)
    count = generator.generate_all_smart_examples(force_rebuild=args.force)
    
    if count > 0:
        logger.info(f"\n🎉 SUCCESS! Generated router examples for {count} documents.")
        logger.info(f"   📂 Output directory: {router_examples_dir}")
        logger.info(f"   💡 Next step: Run 'python tools/4_build_router_cache.py' to build cache")
    else:
        logger.error("\n❌ No new router examples were generated.")
        if not args.force:
            logger.info("   💡 Try using --force flag to rebuild existing examples.")
    
    return 0 if count > 0 else 1

if __name__ == "__main__":
    exit(main())
