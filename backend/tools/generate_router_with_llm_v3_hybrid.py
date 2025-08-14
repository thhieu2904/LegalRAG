#!/usr/bin/env python3
"""
Enhanced Smart Router Generator with LLM - Version 3 (Hybrid)
============================================================

Kết hợp LLM generation với template structure để có cả chất lượng và cấu trúc tốt.
Sử dụng cấu trúc smart_filters từ template cũ nhưng câu hỏi được sinh bởi LLM.
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

class SmartRouterLLMGeneratorV3:
    """Hybrid generator combining LLM questions with structured smart filters."""
    
    def __init__(self, documents_dir: str = None, output_dir: str = None):
        self.documents_dir = Path(documents_dir or "data/documents")
        self.output_dir = Path(output_dir or "data/router_examples_smart_v3")
        
        # Initialize LLM service
        try:
            self.llm_service = LLMService()
            logger.info(f"✅ LLM Service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM Service: {e}")
            raise

    def _detect_collection_from_path(self, file_path: str) -> str:
        """Detect collection name from file path - FIX THIS."""
        path_lower = file_path.lower()
        
        if 'ho_tich_cap_xa' in path_lower:
            return 'ho_tich_cap_xa'
        elif 'chung_thuc' in path_lower:
            return 'chung_thuc' 
        elif 'nuoi_con_nuoi' in path_lower:
            return 'nuoi_con_nuoi'
        elif 'hanh_chinh' in path_lower:
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

    def analyze_document_metadata_enhanced(self, doc: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """Enhanced metadata analysis to create rich smart_filters like the old version."""
        metadata = doc.get('metadata', {})
        title = metadata.get('title', '')
        code = metadata.get('code', '')
        
        # Create comprehensive smart_filters
        smart_filters = {
            "exact_title": [title] if title else [],
            "title_keywords": self._extract_title_keywords(title),
            "procedure_code": [code] if code else [],
            "agency": self._extract_agency(metadata),
            "agency_level": self._determine_agency_level(metadata, file_path),
            "cost_type": self._determine_cost_type(metadata),
            "processing_speed": self._determine_processing_speed(metadata),
            "applicant_type": metadata.get('applicant_type', ['Cá nhân'])
        }
        
        # Create key_attributes like old version
        key_attributes = {
            "speed": self._map_processing_speed(smart_filters["processing_speed"]),
            "cost": self._map_cost_type(smart_filters["cost_type"]),
            "level": self._map_agency_level(smart_filters["agency_level"]),
            "applicant_scope": smart_filters["applicant_type"]
        }
        
        return {
            'metadata': metadata,
            'smart_filters': smart_filters,
            'key_attributes': key_attributes,
            'confidence_threshold': 0.75,
            'priority_score': 1.0
        }

    def _extract_title_keywords(self, title: str) -> List[str]:
        """Extract key words from title for filtering."""
        if not title:
            return []
        
        # Remove common words and extract meaningful keywords
        common_words = {'thủ', 'tục', 'đăng', 'ký', 'cấp', 'việc', 'của', 'cho', 'và', 'có', 'là', 'trong', 'với', 'theo'}
        words = re.findall(r'\w+', title.lower())
        keywords = [w for w in words if len(w) > 2 and w not in common_words]
        return keywords[:5]  # Limit to 5 keywords

    def _extract_agency(self, metadata: Dict) -> List[str]:
        """Extract agency information."""
        agency = metadata.get('executing_agency', '')
        if not agency:
            return []
        return [agency]

    def _determine_agency_level(self, metadata: Dict, file_path: str) -> List[str]:
        """Determine agency level from metadata and path."""
        agency = metadata.get('executing_agency', '').lower()
        path_lower = file_path.lower()
        
        if 'cấp xã' in agency or 'cap_xa' in path_lower:
            return ['commune']
        elif 'cấp huyện' in agency:
            return ['district'] 
        elif 'cấp tỉnh' in agency:
            return ['province']
        else:
            return ['commune']  # Default

    def _determine_cost_type(self, metadata: Dict) -> List[str]:
        """Determine cost type from metadata."""
        fee_text = metadata.get('fee_text', '') or metadata.get('fee', '')
        if not fee_text:
            return []
        
        fee_lower = fee_text.lower()
        if 'miễn phí' in fee_lower or 'không phí' in fee_lower:
            return ['free']
        else:
            return ['paid']

    def _determine_processing_speed(self, metadata: Dict) -> List[str]:
        """Determine processing speed from metadata."""
        processing_time = metadata.get('processing_time_text', '') or metadata.get('processing_time', '')
        if not processing_time:
            return []
        
        time_lower = processing_time.lower()
        if 'ngay' in time_lower and ('nhận' in time_lower or 'khi' in time_lower):
            return ['immediate']
        elif 'ngày' in time_lower or 'tuần' in time_lower:
            return ['multiple_days']  
        elif 'tháng' in time_lower:
            return ['slow']
        else:
            return ['multiple_days']

    def _map_processing_speed(self, speed_list: List[str]) -> str:
        """Map processing speed to key_attributes format."""
        if not speed_list:
            return "unknown"
        speed = speed_list[0]
        mapping = {
            'immediate': 'immediate',
            'multiple_days': 'multi_day', 
            'slow': 'slow'
        }
        return mapping.get(speed, 'multi_day')

    def _map_cost_type(self, cost_list: List[str]) -> str:
        """Map cost type to key_attributes format."""
        if not cost_list:
            return "unknown"
        return cost_list[0]

    def _map_agency_level(self, level_list: List[str]) -> str:
        """Map agency level to key_attributes format."""
        if not level_list:
            return "commune"
        return level_list[0]

    def generate_questions_with_llm_focused(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Generate focused questions - use LLM for main question but templates for variants."""
        metadata = doc.get('metadata', {})
        document_title = metadata.get('title', 'Thủ tục chưa xác định')
        
        # Generate main question using LLM
        main_question = self._generate_main_question_with_llm(document_title, metadata)
        
        # Generate variants using improved templates 
        variants = self._generate_template_variants(document_title, metadata)
        
        return {
            "main_question": main_question,
            "question_variants": variants
        }

    def _generate_main_question_with_llm(self, title: str, metadata: Dict) -> str:
        """Generate main question using LLM for specificity.""" 
        try:
            # Simple prompt for main question
            user_query = f"Tạo 1 câu hỏi chính về thủ tục '{title}'. Câu hỏi phải cụ thể và bắt đầu bằng tên thủ tục."
            system_prompt = "Chỉ trả lời 1 câu hỏi. Không giải thích."
            
            response_data = self.llm_service.generate_response(
                user_query=user_query,
                max_tokens=50,
                temperature=0.1,
                system_prompt=system_prompt
            )
            
            response = response_data.get('response', '').strip()
            if response and '?' in response:
                # Extract first question
                question = response.split('\n')[0].strip()
                question = self._clean_question_v3(question)
                if len(question) > 10 and title.lower() in question.lower():
                    return question
        except:
            pass
        
        # Fallback to template
        return f"{title} cần điều kiện gì?"

    def _generate_template_variants(self, title: str, metadata: Dict) -> List[str]:
        """Generate high-quality template variants based on context."""
        base_variants = [
            f"Làm {title} cần giấy tờ gì?",
            f"Chi phí {title} bao nhiêu?", 
            f"Thời gian xử lý {title} là bao lâu?",
            f"Làm {title} ở đâu?",
        ]
        
        # Add context-specific questions based on metadata
        additional_variants = []
        
        # Check for foreign element
        if 'nước ngoài' in title.lower():
            additional_variants.append(f"Hồ sơ {title} gồm những giấy tờ nào?")
        
        # Check for online capability
        submission_methods = metadata.get('submission_method', [])
        if isinstance(submission_methods, list) and any('trực tuyến' in method.lower() for method in submission_methods):
            additional_variants.append(f"Có thể làm {title} online không?")
        else:
            additional_variants.append(f"Điều kiện để được {title}?")
        
        # Check for delivery options
        result_delivery = metadata.get('result_delivery', [])
        if isinstance(result_delivery, list) and len(result_delivery) > 1:
            additional_variants.append(f"Nhận kết quả {title} như thế nào?")
        else:
            additional_variants.append(f"Quy trình {title} ra sao?")
            
        return base_variants + additional_variants[:2]  # 4 base + 2 context = 6 total

    def _extract_structured_questions(self, response_text: str, document_title: str) -> Optional[Dict]:
        """Extract questions from structured LLM response."""
        if not response_text:
            return None
            
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
        
        main_question = None
        question_variants = []
        
        for line in lines:
            # Look for main question
            if line.startswith('CHÍNH:'):
                main_question = line.replace('CHÍNH:', '').strip()
                continue
            
            # Look for numbered questions
            match = re.match(r'^\d+\.\s*(.+)', line)
            if match:
                question = match.group(1).strip()
                question = self._clean_question_v3(question)
                if question and len(question) > 5:
                    question_variants.append(question)
        
        # Fallback: extract any questions with proper format
        if not main_question or len(question_variants) < 3:
            return self._extract_fallback_from_text(response_text, document_title)
        
        return {
            "main_question": self._clean_question_v3(main_question) or f"{document_title} cần điều kiện gì?",
            "question_variants": question_variants[:7]  # Limit to 7 variants
        }

    def _extract_fallback_from_text(self, text: str, document_title: str) -> Dict:
        """Fallback extraction if structured format fails."""
        questions = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Remove numbering and clean
            cleaned = re.sub(r'^[\d\.\-\*\+]+\s*', '', line).strip()
            if cleaned.endswith('?') and len(cleaned) > 10 and len(cleaned) < 80:
                questions.append(self._clean_question_v3(cleaned))
        
        # Remove duplicates and filter
        unique_questions = []
        seen = set()
        for q in questions:
            if q.lower() not in seen and len(q) > 5:
                unique_questions.append(q)
                seen.add(q.lower())
        
        if len(unique_questions) >= 2:
            return {
                "main_question": unique_questions[0],
                "question_variants": unique_questions[1:7]
            }
        
        return self._create_fallback_questions(document_title)

    def _create_fallback_questions(self, document_title: str) -> Dict:
        """Create fallback questions when LLM fails."""
        return {
            "main_question": f"{document_title} cần điều kiện gì?",
            "question_variants": [
                f"Làm {document_title} cần giấy tờ gì?",
                f"Chi phí {document_title} bao nhiêu?", 
                f"Thời gian xử lý {document_title} là bao lâu?",
                f"Làm {document_title} ở đâu?",
                f"Có thể làm {document_title} online không?"
            ]
        }

    def _clean_question_v3(self, question: str) -> str:
        """Enhanced cleaning for V3."""
        if not question:
            return question
            
        # Remove numbering, bullet points, and extra whitespace
        question = re.sub(r'^[\d\-\*\+\.\)]\s*', '', question).strip()
        
        # Remove quotes and extra whitespace
        question = question.strip().strip('"').strip("'").strip()
        
        # Remove trailing underscores and parenthetical notes
        question = re.sub(r'\s*_+\s*', ' ', question)
        question = re.sub(r'\s*\([^)]*\)\s*$', '', question)
        
        # Fix double question marks
        question = re.sub(r'\?\?+', '?', question)
        question = re.sub(r'\.+\?', '?', question)
        
        # Ensure question ends with question mark
        if question and not question.endswith('?'):
            question += '?'
            
        # Limit length to keep questions concise
        if len(question) > 80:
            question = question[:77] + "...?"
            
        return question

    def _summarize_document_for_prompt(self, doc: Dict[str, Any]) -> str:
        """Create concise summary for prompt."""
        parts = []
        metadata = doc.get("metadata", {})
        
        # Basic info
        if metadata.get('applicant_type'):
            parts.append(f"Đối tượng: {', '.join(metadata['applicant_type']) if isinstance(metadata['applicant_type'], list) else metadata['applicant_type']}")
        if metadata.get('executing_agency'):
            parts.append(f"Cơ quan: {metadata['executing_agency']}")
        if metadata.get('processing_time_text') or metadata.get('processing_time'):
            parts.append(f"Thời gian: {metadata.get('processing_time_text', metadata.get('processing_time', ''))}")
        if metadata.get('fee_text') or metadata.get('fee'):
            parts.append(f"Phí: {metadata.get('fee_text', metadata.get('fee', ''))}")
        
        return ". ".join(parts)

    def generate_all_smart_examples(self, force_rebuild: bool = False) -> int:
        """Generate all smart router examples with hybrid approach."""
        logger.info("🎯 Generating smart router examples using LLM V3 (Hybrid)...")
        
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
                
                # 1. ENHANCED METADATA ANALYSIS
                analysis = self.analyze_document_metadata_enhanced(doc, str(json_file))
                collection_name = self._detect_collection_from_path(str(json_file))
                
                # 2. GENERATE FOCUSED QUESTIONS WITH LLM
                questions = self.generate_questions_with_llm_focused(doc)
                
                # 3. CREATE STRUCTURED ROUTER DATA (like old format)
                router_data = {
                    'metadata': {
                        'title': doc.get('metadata', {}).get('title', ''),
                        'code': doc.get('metadata', {}).get('code', ''),
                        'collection': collection_name,
                        'source_document': str(relative_path),
                        'generated_by': 'llm_powered_generator_v3.0_hybrid',
                        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
                    },
                    'main_question': questions['main_question'],
                    'question_variants': questions.get('question_variants', []),
                    'smart_filters': analysis['smart_filters'],
                    'key_attributes': analysis['key_attributes'],
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
                
                time.sleep(0.3)  # Brief pause

            except Exception as e:
                logger.error(f"   ⚠️ Error processing {json_file.name}: {e}")
                continue
        
        # Generate summary
        self._generate_summary(processed_files, total_examples, json_files)
        return processed_files

    def _generate_summary(self, processed_files: int, total_examples: int, json_files: List[Path]):
        """Generate summary report."""
        collections = {}
        for json_file in json_files:
            collection = self._detect_collection_from_path(str(json_file))
            collections[collection] = collections.get(collection, 0) + 1
        
        summary = {
            'generator_info': {
                'version': 'llm_powered_v3.0_hybrid',
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'llm_model': 'PhoGPT-4B-Chat',
                'approach': 'hybrid_structured_llm_with_rich_metadata'
            },
            'statistics': {
                'total_files_processed': processed_files,
                'total_source_files': len(json_files),
                'total_examples_generated': total_examples,
                'collections_distribution': collections
            },
            'quality_metrics': {
                'avg_variants_per_document': total_examples / processed_files if processed_files > 0 else 0,
                'success_rate': (processed_files / len(json_files)) * 100 if json_files else 0,
                'features': [
                    'rich_smart_filters',
                    'context_specific_questions', 
                    'proper_collection_detection',
                    'structured_metadata'
                ]
            }
        }
        
        summary_file = self.output_dir / "llm_generation_summary_v3.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n📊 Summary saved to {summary_file}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Generate smart router examples using LLM V3 (Hybrid)')
    parser.add_argument('--force', action='store_true', help='Force rebuild existing examples')
    parser.add_argument('--docs', type=str, default='data/documents', help='Documents directory')
    parser.add_argument('--output', type=str, default='data/router_examples_smart_v3', help='Output directory')
    
    args = parser.parse_args()
    
    try:
        generator = SmartRouterLLMGeneratorV3(args.docs, args.output)
        
        logger.info("🚀 Starting LLM-powered Smart Router Generation V3 (Hybrid)...")
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
