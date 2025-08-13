#!/usr/bin/env python3
"""
Smart Router Examples Generator for LegalRAG
============================================

Tạo router examples "sắc bén" với TOÀN BỘ logic từ generate_smart_router_examples.py:
1. Advanced question templates với metadata-aware specificity
2. Smart filters với multi-dimensional filtering từ metadata analysis
3. Khai thác đầy đủ "mỏ vàng" metadata với key attributes
4. Priority scoring cho routing decisions

Usage:
    cd backend
    python tools/3_generate_smart_router.py
    python tools/3_generate_smart_router.py --force  # Rebuild existing
"""

import sys
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
import logging
import argparse

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SmartRouterGenerator:
    def __init__(self, documents_dir: str, output_dir: str):
        self.documents_dir = Path(documents_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Advanced question templates TOÀN BỘ từ generate_smart_router_examples.py
        self.advanced_templates = {
            # Patterns for birth registration
            'khai_sinh': {
                'standard': {
                    'main': "Đăng ký khai sinh {specificity} cần giấy tờ gì?",
                    'variants': [
                        "Làm giấy khai sinh {specificity} ở đâu và cần những gì?",
                        "Thủ tục khai báo sinh con {specificity} như thế nào?",
                        "Hồ sơ đăng ký khai sinh {specificity} gồm những gì?",
                        "Đăng ký khai sinh {specificity} tốn bao nhiêu tiền?",
                        "Phí đăng ký khai sinh {specificity} cho con là bao nhiêu?",
                        "Lệ phí khai sinh {specificity} có tốn phí không?",
                        "Chi phí làm giấy khai sinh {specificity} như thế nào?",
                        "Khai sinh {specificity} có miễn phí không?"
                    ]
                },
                'mobile': {
                    'main': "Đăng ký khai sinh lưu động khác gì so với đăng ký thường?",
                    'variants': [
                        "Khi nào cần đăng ký khai sinh lưu động?",
                        "Thủ tục khai sinh lưu động có phức tạp không?",
                        "Đăng ký khai sinh lưu động mất bao lâu?",
                        "Điều kiện để được khai sinh lưu động?",
                        "Chi phí khai sinh lưu động như thế nào?"
                    ]
                },
                'foreign_element': {
                    'main': "Đăng ký khai sinh có yếu tố nước ngoài cần giấy tờ gì thêm?",
                    'variants': [
                        "Khai sinh cho con có cha mẹ là người nước ngoài?",
                        "Thủ tục khai sinh có yếu tố nước ngoài phức tạp như thế nào?",
                        "Giấy tờ nước ngoài cần hợp pháp hóa không?",
                        "Khai sinh với yếu tố nước ngoài cần dịch thuật không?",
                        "Thủ tục khai sinh cho người nước ngoài tại Việt Nam?"
                    ]
                }
            },
            
            # Marriage registration patterns  
            'ket_hon': {
                'standard': {
                    'main': "Đăng ký kết hôn {specificity} cần điều kiện gì?",
                    'variants': [
                        "Thủ tục kết hôn {specificity} làm ở đâu?",
                        "Hồ sơ kết hôn {specificity} gồm những giấy tờ nào?",
                        "Kết hôn {specificity} mất bao lâu được cấp giấy?",
                        "Điều kiện để được đăng ký kết hôn {specificity}?",
                        "Chi phí đăng ký kết hôn {specificity}?"
                    ]
                },
                'mobile': {
                    'main': "Đăng ký kết hôn lưu động diễn ra khi nào?",
                    'variants': [
                        "Kết hôn lưu động có khác gì kết hôn thường?",
                        "Điều kiện để được kết hôn lưu động?",
                        "Phí kết hôn lưu động có cao hơn không?",
                        "Kết hôn lưu động cần đặt lịch trước không?",
                        "Thủ tục kết hôn lưu động phức tạp ra sao?"
                    ]
                }
            },
            
            # Death registration patterns
            'khai_tu': {
                'standard': {
                    'main': "Đăng ký khai tử {specificity} cần giấy tờ gì?",
                    'variants': [
                        "Thủ tục khai báo tử {specificity} như thế nào?",
                        "Hồ sơ khai tử {specificity} gồm những gì?",
                        "Khai tử {specificity} làm ở đâu?",
                        "Thời hạn khai báo tử {specificity}?",
                        "Ai có quyền khai báo tử {specificity}?"
                    ]
                }
            },
            
            # Adoption patterns
            'nuoi_con_nuoi': {
                'standard': {
                    'main': "Thủ tục nhận con nuôi {specificity} cần điều kiện gì?",
                    'variants': [
                        "Hồ sơ nhận con nuôi {specificity} gồm những gì?",
                        "Quy trình nuôi con nuôi {specificity} như thế nào?",
                        "Điều kiện để được nhận con nuôi {specificity}?",
                        "Giấy tờ cần thiết cho việc nuôi con nuôi {specificity}?",
                        "Thời gian xử lý hồ sơ nuôi con nuôi {specificity}?"
                    ]
                }
            },
            
            # Notarization patterns
            'chung_thuc': {
                'contracts': {
                    'main': "Chứng thực hợp đồng {contract_type} cần điều kiện gì?",
                    'variants': [
                        "Phí chứng thực hợp đồng {contract_type} bao nhiêu?",
                        "Chứng thực {contract_type} mất bao lâu?",
                        "Hồ sơ chứng thực {contract_type} cần gì?",
                        "Địa điểm chứng thực hợp đồng {contract_type}?",
                        "Thủ tục chứng thực {contract_type} phức tạp không?"
                    ]
                },
                'copies': {
                    'main': "Chứng thực bản sao từ bản chính cần lưu ý gì?",
                    'variants': [
                        "Giấy tờ nào được chứng thực bản sao?",
                        "Phí chứng thực bản sao bao nhiêu?",
                        "Chứng thực bản sao và photo công chứng khác gì?",
                        "Bản sao chứng thực có giá trị bao lâu?",
                        "Thủ tục chứng thực bản sao đơn giản không?"
                    ]
                },
                'signatures': {
                    'main': "Chứng thực chữ ký {signature_type} cần điều kiện gì?",
                    'variants': [
                        "Chứng thực chữ ký {signature_type} ở đâu?",
                        "Giấy tờ cần thiết cho chứng thực chữ ký {signature_type}?",
                        "Phí chứng thực chữ ký {signature_type}?",
                        "Ai có thể chứng thực chữ ký {signature_type}?",
                        "Chữ ký chứng thực có hiệu lực bao lâu?"
                    ]
                }
            }
        }
    
    def analyze_document_metadata(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Phân tích sâu metadata để tạo questions và filters chính xác - TOÀN BỘ từ generate_smart_router_examples.py"""
        metadata = doc.get('metadata', {})
        title = metadata.get('title', '').lower()
        
        analysis = {
            'category': self._categorize_document(title, metadata),
            'specificity': self._extract_specificity(title),
            'key_attributes': self._extract_key_attributes(metadata),
            'smart_filters': self._create_smart_filters(metadata),
            'question_context': self._build_question_context(metadata)
        }
        
        return analysis
    
    def _categorize_document(self, title: str, metadata: Dict) -> str:
        """Phân loại document dựa trên title và metadata patterns - TOÀN BỘ từ generate_smart_router_examples.py"""
        if any(word in title for word in ['khai sinh', 'sinh']):
            if 'lưu động' in title:
                return 'khai_sinh_mobile'
            elif any(word in title for word in ['nước ngoài', 'ngoại quốc']):
                return 'khai_sinh_foreign'
            else:
                return 'khai_sinh_standard'
        
        elif any(word in title for word in ['kết hôn', 'hôn']):
            if 'lưu động' in title:
                return 'ket_hon_mobile'
            elif any(word in title for word in ['nước ngoài', 'ngoại quốc']):
                return 'ket_hon_foreign'
            else:
                return 'ket_hon_standard'
        
        elif any(word in title for word in ['khai tử', 'tử']):
            return 'khai_tu_standard'
        
        elif any(word in title for word in ['nuôi con', 'con nuôi']):
            return 'nuoi_con_nuoi_standard'
        
        elif any(word in title for word in ['chứng thực']):
            if any(word in title for word in ['hợp đồng', 'giao dịch']):
                return 'chung_thuc_contracts'
            elif 'bản sao' in title:
                return 'chung_thuc_copies'
            elif 'chữ ký' in title:
                return 'chung_thuc_signatures'
            else:
                return 'chung_thuc_general'
        
        return 'general'
    
    def _extract_specificity(self, title: str) -> str:
        """Trích xuất đặc điểm riêng của thủ tục - TOÀN BỘ từ generate_smart_router_examples.py"""
        if 'lưu động' in title:
            return 'lưu động'
        elif any(word in title for word in ['nước ngoài', 'ngoại quốc']):
            return 'có yếu tố nước ngoài'
        elif 'lại' in title:
            return 'lại'
        elif 'kết hợp' in title:
            return 'kết hợp'
        elif 'cấp lần đầu' in title:
            return 'cấp lần đầu'
        else:
            return ''
    
    def _extract_key_attributes(self, metadata: Dict) -> Dict[str, Any]:
        """Trích xuất các thuộc tính quan trọng từ metadata - TOÀN BỘ từ generate_smart_router_examples.py"""
        attributes = {}
        
        # Processing time analysis
        processing_time = metadata.get('processing_time_text', '').lower()
        if processing_time:
            if 'ngay' in processing_time and ('khi' in processing_time or 'tức' in processing_time):
                attributes['speed'] = 'same_day'
            elif 'ngày' in processing_time:
                attributes['speed'] = 'multi_day'
            else:
                attributes['speed'] = 'unspecified'
        
        # Fee analysis
        fee_text = metadata.get('fee_text', '').lower()
        if fee_text:
            if any(word in fee_text for word in ['miễn', 'không thu', '0 đồng']):
                attributes['cost'] = 'free'
            elif any(word in fee_text for word in ['đ', 'đồng', 'vnd']):
                attributes['cost'] = 'paid'
            else:
                attributes['cost'] = 'unspecified'
        
        # Authority level
        executing_agency = metadata.get('executing_agency', '').lower()
        if 'cấp xã' in executing_agency or 'xã' in executing_agency:
            attributes['level'] = 'commune'
        elif 'sở' in executing_agency:
            attributes['level'] = 'department'
        elif 'ủy ban' in executing_agency:
            attributes['level'] = 'committee'
        else:
            attributes['level'] = 'unspecified'
        
        # Applicant type
        applicant_type = metadata.get('applicant_type', [])
        if isinstance(applicant_type, list):
            attributes['applicant_scope'] = applicant_type
        
        return attributes
    
    def _create_smart_filters(self, metadata: Dict) -> Dict[str, List[str]]:
        """Tạo filters thông minh dựa trên metadata - TOÀN BỘ từ generate_smart_router_examples.py"""
        filters = {}
        
        # Exact title matching (không tách từ)
        title = metadata.get('title', '')
        if title:
            filters['exact_title'] = [title]
            # Add semantic variations
            filters['title_keywords'] = self._extract_semantic_keywords(title)
        
        # Metadata-based filters
        if metadata.get('code'):
            filters['procedure_code'] = [metadata['code']]
        
        if metadata.get('executing_agency'):
            filters['agency'] = [metadata['executing_agency']]
            # Add agency level
            agency = metadata['executing_agency'].lower()
            if 'cấp xã' in agency:
                filters['agency_level'] = ['commune']
            elif 'sở' in agency:
                filters['agency_level'] = ['department']
        
        # Fee-based filtering
        fee_text = metadata.get('fee_text', '')
        if fee_text:
            if 'miễn' in fee_text.lower():
                filters['cost_type'] = ['free']
            else:
                filters['cost_type'] = ['paid']
        
        # Processing time filtering
        processing_time = metadata.get('processing_time_text', '')
        if 'ngay' in processing_time.lower():
            filters['processing_speed'] = ['same_day']
        elif 'ngày' in processing_time.lower():
            filters['processing_speed'] = ['multiple_days']
        
        # Applicant filtering
        applicant_type = metadata.get('applicant_type', [])
        if applicant_type:
            filters['applicant_type'] = applicant_type
        
        return filters
    
    def _extract_semantic_keywords(self, title: str) -> List[str]:
        """Trích xuất semantic keywords từ title - TOÀN BỘ từ generate_smart_router_examples.py"""
        keywords = []
        
        semantic_groups = {
            'registration_actions': ['đăng ký', 'khai báo', 'đăng kí'],
            'document_types': ['khai sinh', 'kết hôn', 'khai tử', 'chứng thực'],
            'procedure_modifiers': ['lưu động', 'nước ngoài', 'cấp lại', 'bản sao'],
            'legal_entities': ['hợp đồng', 'chữ ký', 'giấy tờ']
        }
        
        title_lower = title.lower()
        for group_name, terms in semantic_groups.items():
            for term in terms:
                if term in title_lower:
                    keywords.append(term)
        
        return list(set(keywords))
    
    def _build_question_context(self, metadata: Dict) -> Dict[str, str]:
        """Build context cho question generation - TOÀN BỘ từ generate_smart_router_examples.py"""
        context = {}
        
        # Contract type cho chứng thực
        title = metadata.get('title', '').lower()
        if 'hợp đồng' in title:
            if 'mua bán' in title:
                context['contract_type'] = 'mua bán'
            elif 'thuê' in title:
                context['contract_type'] = 'thuê nhà'
            elif 'lao động' in title:
                context['contract_type'] = 'lao động'
            else:
                context['contract_type'] = 'dân sự'
        
        # Signature type cho chứng thực chữ ký
        if 'chữ ký' in title:
            if 'giao dịch' in title:
                context['signature_type'] = 'trong giao dịch'
            elif 'hợp đồng' in title:
                context['signature_type'] = 'trên hợp đồng'
            else:
                context['signature_type'] = 'trên giấy tờ'
        
        return context
    
    def _extract_contract_type(self, title: str) -> str:
        """Extract contract type từ title"""
        title_lower = title.lower()
        if 'mua bán' in title_lower:
            return 'mua bán'
        elif 'thuê' in title_lower:
            return 'thuê nhà'
        elif 'lao động' in title_lower:
            return 'lao động'
        else:
            return 'dân sự'
    
    def generate_smart_questions(self, analysis: Dict, metadata: Dict) -> Dict[str, Any]:
        """Generate câu hỏi thông minh dựa trên analysis - TOÀN BỘ từ generate_smart_router_examples.py"""
        category = analysis['category']
        specificity = analysis['specificity']
        context = analysis['question_context']
        
        # Base questions từ template
        if category.startswith('khai_sinh'):
            if 'mobile' in category:
                template = self.advanced_templates['khai_sinh']['mobile']
            elif 'foreign' in category:
                template = self.advanced_templates['khai_sinh']['foreign_element']
            else:
                template = self.advanced_templates['khai_sinh']['standard']
        elif category.startswith('ket_hon'):
            if 'mobile' in category:
                template = self.advanced_templates['ket_hon']['mobile']
            else:
                template = self.advanced_templates['ket_hon']['standard']
        elif category.startswith('khai_tu'):
            template = self.advanced_templates['khai_tu']['standard']
        elif category.startswith('nuoi_con'):
            template = self.advanced_templates['nuoi_con_nuoi']['standard']
        elif category.startswith('chung_thuc'):
            if 'contracts' in category:
                template = self.advanced_templates['chung_thuc']['contracts']
            elif 'copies' in category:
                template = self.advanced_templates['chung_thuc']['copies']
            elif 'signatures' in category:
                template = self.advanced_templates['chung_thuc']['signatures']
            else:
                template = self.advanced_templates['chung_thuc']['contracts']
        else:
            # Generic fallback
            title = metadata.get('title', 'thủ tục này')
            return {
                'main_question': f"Thủ tục {title} cần điều kiện gì?",
                'question_variants': [
                    f"Làm {title} ở đâu?",
                    f"Hồ sơ {title} gồm những gì?",
                    f"Phí {title} bao nhiêu tiền?"
                ]
            }
        
        # Customize questions with specificity and context
        main_question = template['main'].format(
            specificity=specificity,
            contract_type=self._extract_contract_type(metadata.get('title', '')),
            signature_type=context.get('signature_type', 'trên giấy tờ')
        ).replace('  ', ' ').strip()
        
        variants = []
        for variant_template in template['variants']:  # Lấy TẤT CẢ variants để phủ nhiều thông tin nhất
            variant = variant_template.format(
                specificity=specificity,
                contract_type=self._extract_contract_type(metadata.get('title', '')),
                signature_type=context.get('signature_type', 'trên giấy tờ')
            ).replace('  ', ' ').strip()
            variants.append(variant)
        
        return {
            'main_question': main_question,
            'question_variants': variants
        }
    
    def generate_all_smart_examples(self) -> int:
        """Generate individual smart router examples - One file per document"""
        logger.info("🎯 Generating individual smart router examples...")
        
        if not self.documents_dir.exists():
            logger.error(f"❌ Documents directory not found: {self.documents_dir}")
            return 0
        
        # Scan all JSON files recursively
        json_files = list(self.documents_dir.rglob("*.json"))
        if not json_files:
            logger.error("❌ No JSON documents found")
            return 0
        
        logger.info(f"   📄 Found {len(json_files)} JSON files")
        
        # Group by collection for statistics
        collections = {}
        for json_file in json_files:
            collection = self._detect_collection_from_path(str(json_file))
            if collection not in collections:
                collections[collection] = []
            collections[collection].append(json_file)
        
        for collection, files in collections.items():
            logger.info(f"   📂 {collection}: {len(files)} files")
        
        total_examples = 0
        processed_files = 0
        
        # Process each document individually
        for json_file in json_files:
            try:
                # Load document
                with open(json_file, 'r', encoding='utf-8') as f:
                    doc = json.load(f)
                
                # Get collection info
                collection_name = self._detect_collection_from_path(str(json_file))
                
                # Analyze metadata
                analysis = self.analyze_document_metadata(doc)
                
                # Generate questions
                questions = self.generate_smart_questions(analysis, doc.get('metadata', {}))
                
                # Create relative path from documents dir
                relative_path = json_file.relative_to(self.documents_dir)
                
                # Create output path with same structure
                output_file = self.output_dir / relative_path
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Create individual router file
                router_data = {
                    'metadata': {
                        'title': doc.get('metadata', {}).get('title', ''),
                        'code': doc.get('metadata', {}).get('code', ''),
                        'collection': collection_name,
                        'category': analysis['category'],
                        'source_document': str(relative_path),
                        'generated_at': '2025-08-13',
                        'version': '2.0',
                        'generator': 'smart_router_v2'
                    },
                    'main_question': questions['main_question'],
                    'question_variants': questions.get('question_variants', []),
                    'smart_filters': analysis['smart_filters'],
                    'key_attributes': analysis['key_attributes'],
                    'expected_collection': collection_name,
                    'confidence_threshold': 0.75,
                    'priority_score': self._calculate_priority_score(analysis)
                }
                
                # Save individual router file
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(router_data, f, ensure_ascii=False, indent=2)
                
                processed_files += 1
                total_examples += 1 + len(questions.get('question_variants', []))
                
                if processed_files % 10 == 0:
                    logger.info(f"   📝 Processed {processed_files}/{len(json_files)} files...")
            
            except Exception as e:
                logger.warning(f"      ⚠️ Error processing {json_file.name}: {e}")
                continue
        
        # Generate summary file
        summary = {
            'total_files_processed': processed_files,
            'total_examples': total_examples,
            'collections': {name: len(files) for name, files in collections.items()},
            'generator_version': 'smart_router_individual_v2.0',
            'output_structure': 'individual_files_mirror_source',
            'improvements': [
                'Một file router cho mỗi document gốc',
                'Cấu trúc thư mục mirror document structure',
                'Dễ maintain và trace từng document',
                'Better scalability và performance'
            ]
        }
        
        summary_file = self.output_dir / "router_generation_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"   ✅ Generated {processed_files} individual router files")
        logger.info(f"   📊 Total examples: {total_examples}")
        logger.info(f"   📁 Output structure mirrors source documents")
        
        return processed_files
    
    def _detect_collection_from_path(self, file_path: str) -> str:
        """Detect collection name from file path"""
        path_lower = file_path.lower()
        
        if 'ho_tich_cap_xa' in path_lower:
            return 'ho_tich_cap_xa'
        elif 'chung_thuc' in path_lower:
            return 'chung_thuc'
        elif 'nuoi_con_nuoi' in path_lower:
            return 'nuoi_con_nuoi'
        else:
            # Check parent directory names
            parent_dir = Path(file_path).parent.name.lower()
            if any(word in parent_dir for word in ['cap_ho_tich', 'ho_tich']):
                return 'ho_tich_cap_xa'
            elif 'chung_thuc' in parent_dir:
                return 'chung_thuc'
            elif any(word in parent_dir for word in ['nuoi_con', 'con_nuoi']):
                return 'nuoi_con_nuoi'
            else:
                return 'ho_tich_cap_xa'  # Default collection
    
    def _calculate_priority_score(self, analysis: Dict) -> float:
        """Calculate priority score cho routing decisions"""
        score = 0.5  # Base score
        
        # Category-based scoring
        if analysis['category'] != 'general':
            score += 0.2
        
        # Specificity bonus
        if analysis['specificity']:
            score += 0.1
        
        # Key attributes bonus
        if analysis['key_attributes']:
            score += 0.1 * len(analysis['key_attributes'])
        
        # Smart filters bonus
        if analysis['smart_filters']:
            score += 0.05 * len(analysis['smart_filters'])
        
        return min(score, 1.0)  # Cap at 1.0


def main():
    parser = argparse.ArgumentParser(
        description='Generate smart router examples for LegalRAG',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/3_generate_smart_router.py          # Generate smart examples
  python tools/3_generate_smart_router.py --force  # Force rebuild existing

This tool will:
1. Scan all JSON documents recursively in data/documents/
2. Analyze metadata for smart categorization and advanced filtering
3. Generate specific questions using context-aware templates
4. Create multi-dimensional filter keywords with priority scoring
5. Save examples grouped by collection with complete metadata analysis
        """
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force rebuild - overwrite existing examples'
    )
    
    args = parser.parse_args()
    
    # Paths (GIỐNG HỆT generate_smart_router_examples.py)
    documents_dir = backend_dir / "data" / "documents"
    router_examples_dir = backend_dir / "data" / "router_examples_smart"
    
    # Check if documents exist
    if not documents_dir.exists():
        logger.error(f"❌ Documents directory not found: {documents_dir}")
        return 1
    
    logger.info("🧠 Smart Router Examples Generator v2.0")
    logger.info("=" * 60)
    
    # Generate smart examples
    generator = SmartRouterGenerator(str(documents_dir), str(router_examples_dir))
    count = generator.generate_all_smart_examples()
    
    if count > 0:
        logger.info(f"✅ SUCCESS! Generated {count} SMART router examples")
        logger.info(f"📁 Output directory: {router_examples_dir}")
        logger.info("💡 Key improvements:")
        logger.info("   ✓ Câu hỏi đặc trưng cho từng thủ tục")
        logger.info("   ✓ Filter keywords chính xác")
        logger.info("   ✓ Khai thác đầy đủ metadata")
        logger.info("   ✓ Priority scoring cho routing")
        return 0
    else:
        logger.error("❌ No smart examples were generated")
        return 1

if __name__ == "__main__":
    exit(main())
