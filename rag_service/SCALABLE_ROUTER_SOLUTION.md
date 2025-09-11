# SCALABLE ROUTER IMPROVEMENT STRATEGY

===============================================

**Vấn đề cốt lõi**: Router nhầm DOC_008 thay vì DOC_002 với 166 documents/13 collections
**Yêu cầu**: Giải pháp scalable, không hard-code patterns

# 🚀 SCALABLE SOLUTIONS

## PHƯƠNG ÁN 1: HIERARCHICAL SEMANTIC ROUTING ⭐⭐⭐⭐⭐

### 1.1 Two-Stage Router Architecture

```python
class HierarchicalRouter:
    """
    Stage 1: Intent Classification (procedure type)
    Stage 2: Document Selection (specific document)
    """

    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.document_router = DocumentRouter()

    def route(self, query: str) -> Dict[str, Any]:
        # Stage 1: Classify intent category
        intent_category = self.intent_classifier.classify(query)

        # Stage 2: Route within category
        candidates = self.get_candidates_by_intent(intent_category)
        best_doc = self.document_router.route_within_candidates(query, candidates)

        return {
            "intent_category": intent_category,
            "selected_document": best_doc,
            "routing_path": f"{intent_category} → {best_doc}"
        }
```

### 1.2 Auto Intent Category Detection

```python
class AutoIntentCategorizer:
    """Tự động phân loại documents thành intent categories"""

    def analyze_document_corpus(self, documents: Dict) -> Dict[str, List[str]]:
        """Phân tích corpus để tìm ra intent categories tự động"""

        # Step 1: Extract key phrases từ tất cả questions
        all_questions = []
        doc_phrases = {}

        for collection, docs in documents.items():
            for doc_id, doc_data in docs.items():
                questions = [doc_data['main_question']] + doc_data['question_variants']
                phrases = self.extract_key_phrases(questions)
                doc_phrases[f"{collection}#{doc_id}"] = phrases
                all_questions.extend(questions)

        # Step 2: Clustering để tìm intent groups
        intent_clusters = self.cluster_by_semantic_similarity(doc_phrases)

        # Step 3: Auto-assign intent names
        intent_categories = {}
        for cluster_id, doc_list in intent_clusters.items():
            intent_name = self.generate_intent_name(cluster_id, doc_list)
            intent_categories[intent_name] = doc_list

        return intent_categories

    def extract_key_phrases(self, questions: List[str]) -> List[str]:
        """Extract key phrases using Vietnamese NLP"""
        # Sử dụng underthesea hoặc VnCoreNLP
        import underthesea

        key_phrases = []
        for question in questions:
            # POS tagging để lấy noun phrases
            pos_tags = underthesea.pos_tag(question)
            noun_phrases = self.extract_noun_phrases(pos_tags)
            key_phrases.extend(noun_phrases)

        return list(set(key_phrases))

    def cluster_by_semantic_similarity(self, doc_phrases: Dict) -> Dict[int, List[str]]:
        """Clustering documents by semantic similarity"""
        from sklearn.cluster import AgglomerativeClustering

        # Create embeddings for each document's phrases
        embeddings = []
        doc_ids = []

        for doc_id, phrases in doc_phrases.items():
            combined_text = " ".join(phrases)
            embedding = self.embedding_model.encode([combined_text])[0]
            embeddings.append(embedding)
            doc_ids.append(doc_id)

        # Hierarchical clustering
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=0.3,  # Adjust based on similarity threshold
            linkage='ward'
        )

        cluster_labels = clustering.fit_predict(embeddings)

        # Group documents by cluster
        clusters = {}
        for doc_id, cluster_id in zip(doc_ids, cluster_labels):
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(doc_id)

        return clusters
```

**Ưu điểm**:

- Tự động, không cần manual patterns
- Scale được với hàng ngàn documents
- Giữ được accuracy cao

**Nhược điểm**:

- Cần implement clustering logic
- Setup phức tạp hơn

---

## PHƯƠNG ÁN 2: SEMANTIC DISTANCE OPTIMIZATION ⭐⭐⭐⭐

### 2.1 Fine-tuned Similarity Calculation

```python
class OptimizedSemanticRouter:
    """Cải thiện tính toán similarity với domain-specific adjustments"""

    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        self.document_embeddings = {}
        self.similarity_weights = self.learn_optimal_weights()

    def learn_optimal_weights(self) -> Dict[str, float]:
        """Học weights tối ưu từ document metadata"""

        weights = {
            'title_weight': 2.0,        # Title matching quan trọng hơn
            'main_question_weight': 1.8, # Main question weight cao
            'variant_weight': 1.0,       # Variants weight thường
            'metadata_weight': 1.5,      # Metadata quan trọng
            'collection_weight': 1.2     # Collection context
        }

        return weights

    def calculate_enhanced_similarity(
        self,
        query_embedding: np.ndarray,
        doc_data: Dict,
        doc_metadata: Dict
    ) -> float:
        """Tính similarity với multiple components và weights"""

        similarities = []
        weights = []

        # 1. Title similarity (cao nhất)
        if 'title' in doc_metadata:
            title_emb = self.embedding_model.encode([doc_metadata['title']])[0]
            title_sim = cosine_similarity([query_embedding], [title_emb])[0][0]
            similarities.append(title_sim)
            weights.append(self.similarity_weights['title_weight'])

        # 2. Main question similarity
        main_q = doc_data['main_question']
        main_emb = self.embedding_model.encode([main_q])[0]
        main_sim = cosine_similarity([query_embedding], [main_emb])[0][0]
        similarities.append(main_sim)
        weights.append(self.similarity_weights['main_question_weight'])

        # 3. Best variant similarity
        if doc_data['question_variants']:
            variant_embs = self.embedding_model.encode(doc_data['question_variants'])
            variant_sims = cosine_similarity([query_embedding], variant_embs)[0]
            best_variant_sim = max(variant_sims)
            similarities.append(best_variant_sim)
            weights.append(self.similarity_weights['variant_weight'])

        # 4. Metadata similarity (requirements, conditions)
        if 'requirements_conditions' in doc_metadata:
            req_emb = self.embedding_model.encode([doc_metadata['requirements_conditions']])[0]
            req_sim = cosine_similarity([query_embedding], [req_emb])[0][0]
            similarities.append(req_sim)
            weights.append(self.similarity_weights['metadata_weight'])

        # Weighted average
        total_weight = sum(weights)
        weighted_sim = sum(s * w for s, w in zip(similarities, weights)) / total_weight

        return weighted_sim

    def apply_context_boosters(
        self,
        base_similarity: float,
        query: str,
        doc_data: Dict,
        doc_metadata: Dict
    ) -> float:
        """Apply context-specific boosters"""

        boosted_sim = base_similarity

        # Boost 1: Exact keyword matches
        query_lower = query.lower()
        title_lower = doc_metadata.get('title', '').lower()

        exact_matches = sum(1 for word in query_lower.split()
                          if len(word) > 3 and word in title_lower)

        if exact_matches > 0:
            boost = min(0.1, exact_matches * 0.03)  # Max 10% boost
            boosted_sim += boost

        # Boost 2: Procedure type matching
        procedure_keywords = {
            'đăng_ký_đơn': ['đăng ký', 'làm giấy', 'cần giấy'],
            'đăng_ký_kết_hợp': ['kết hợp', 'cùng lúc', 'nhận cha', 'nhận mẹ', '2 trong 1']
        }

        for procedure_type, keywords in procedure_keywords.items():
            if any(kw in query_lower for kw in keywords):
                if procedure_type in title_lower:
                    boosted_sim += 0.05  # 5% boost cho matching procedure type

        # Boost 3: Fee/cost sensitivity
        cost_keywords = ['phí', 'lệ phí', 'chi phí', 'tiền', 'bao nhiêu']
        if any(kw in query_lower for kw in cost_keywords):
            if 'fee_vnd' in doc_metadata and doc_metadata['fee_vnd']:
                boosted_sim += 0.02  # Small boost for cost-relevant docs

        return min(1.0, boosted_sim)  # Cap at 1.0
```

**Ưu điểm**:

- Cải thiện ngay trên codebase hiện tại
- Tận dụng metadata có sẵn
- Scalable với weighted approach

**Nhược điểm**:

- Vẫn cần tuning weights
- Chưa giải quyết triệt để confusion cases

---

## PHƯƠNG ÁN 3: ADAPTIVE THRESHOLD LEARNING ⭐⭐⭐⭐⭐

### 3.1 Confidence Calibration with User Feedback

```python
class AdaptiveThresholdLearner:
    """Học threshold tối ưu từ user behavior"""

    def __init__(self):
        self.feedback_history = []
        self.threshold_params = {
            'high_confidence': 0.8,
            'medium_confidence': 0.65,
            'low_confidence': 0.5
        }

    def update_thresholds_from_feedback(self, feedback_batch: List[Dict]):
        """Cập nhật thresholds dựa trên user corrections"""

        # Analyze cases where router was wrong
        wrong_predictions = [f for f in feedback_batch if not f['was_correct']]

        for case in wrong_predictions:
            router_confidence = case['router_confidence']
            actual_relevance = case['user_rating']  # 1-5 scale

            # Adjust thresholds if confident prediction was wrong
            if router_confidence > 0.8 and actual_relevance < 3:
                self.threshold_params['high_confidence'] += 0.01

            elif router_confidence < 0.6 and actual_relevance > 4:
                self.threshold_params['low_confidence'] -= 0.01

        # Clamp thresholds trong reasonable range
        self.threshold_params = {
            k: max(0.3, min(0.9, v))
            for k, v in self.threshold_params.items()
        }

    def get_dynamic_threshold(self, query_context: Dict) -> Dict[str, float]:
        """Get thresholds adapted for specific query context"""

        base_thresholds = self.threshold_params.copy()

        # Adjust based on query complexity
        query_complexity = self.estimate_query_complexity(query_context['query'])

        if query_complexity > 0.7:  # Complex query
            # Require higher confidence for complex queries
            base_thresholds = {k: v + 0.05 for k, v in base_thresholds.items()}

        # Adjust based on collection type
        collection = query_context.get('collection')
        if collection and 'kết_hợp' in collection:
            # Higher thresholds for combination procedures
            base_thresholds = {k: v + 0.03 for k, v in base_thresholds.items()}

        return base_thresholds

    def estimate_query_complexity(self, query: str) -> float:
        """Estimate query complexity score 0-1"""

        complexity_factors = {
            'length': len(query.split()) / 20,  # Normalize by 20 words
            'conjunctions': sum(1 for w in ['và', 'hoặc', 'nhưng', 'còn'] if w in query) / 3,
            'conditions': sum(1 for w in ['nếu', 'khi', 'trường hợp'] if w in query) / 2,
            'specificity': sum(1 for w in ['cụ thể', 'chi tiết', 'chính xác'] if w in query) / 2
        }

        complexity = sum(complexity_factors.values()) / len(complexity_factors)
        return min(1.0, complexity)
```

### 3.2 Document Confusion Matrix Learning

```python
class ConfusionMatrixLearner:
    """Học confusion patterns giữa các documents"""

    def __init__(self):
        self.confusion_matrix = defaultdict(lambda: defaultdict(int))
        self.correction_patterns = {}

    def record_confusion(self, predicted_doc: str, actual_doc: str, query: str):
        """Record confusion case"""
        self.confusion_matrix[predicted_doc][actual_doc] += 1

        # Store query pattern for learning
        if predicted_doc != actual_doc:
            key = f"{predicted_doc}→{actual_doc}"
            if key not in self.correction_patterns:
                self.correction_patterns[key] = []
            self.correction_patterns[key].append(query)

    def get_confusion_penalty(self, doc1: str, doc2: str) -> float:
        """Get penalty score if doc1 and doc2 are often confused"""

        total_confusions = sum(self.confusion_matrix[doc1].values())
        if total_confusions == 0:
            return 0.0

        confusion_rate = self.confusion_matrix[doc1][doc2] / total_confusions

        # Apply penalty based on confusion rate
        if confusion_rate > 0.3:  # 30% confusion rate
            return 0.1  # 10% penalty
        elif confusion_rate > 0.1:  # 10% confusion rate
            return 0.05  # 5% penalty

        return 0.0

    def learn_distinguishing_features(self) -> Dict[str, List[str]]:
        """Học features để phân biệt confused documents"""

        distinguishing_features = {}

        for confusion_key, queries in self.correction_patterns.items():
            predicted_doc, actual_doc = confusion_key.split('→')

            # Analyze queries where actual_doc was correct
            distinguishing_words = self.extract_distinguishing_words(queries)

            distinguishing_features[confusion_key] = distinguishing_words

        return distinguishing_features

    def extract_distinguishing_words(self, queries: List[str]) -> List[str]:
        """Extract words that distinguish correct vs incorrect routing"""

        # Simple approach: find most frequent meaningful words
        word_counts = defaultdict(int)

        for query in queries:
            words = query.lower().split()
            meaningful_words = [w for w in words if len(w) > 3 and w not in STOPWORDS]

            for word in meaningful_words:
                word_counts[word] += 1

        # Return top distinguishing words
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:10]]
```

**Ưu điểm**:

- Tự học từ user feedback
- Giải quyết confusion patterns cụ thể
- Cải thiện liên tục theo thời gian

**Nhược điểm**:

- Cần thời gian collect feedback
- Cold start problem

---

## PHƯƠNG ÁN 4: CONTRASTIVE LEARNING APPROACH ⭐⭐⭐⭐

### 4.1 Negative Sampling for Better Discrimination

```python
class ContrastiveLearningRouter:
    """Sử dụng contrastive learning để phân biệt documents tốt hơn"""

    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        self.negative_samples = self.generate_negative_samples()

    def generate_negative_samples(self) -> Dict[str, List[str]]:
        """Generate negative samples for each document"""

        negative_samples = {}

        # For each document, find similar but different documents
        for collection, docs in self.example_questions.items():
            for doc_id, doc_data in docs.items():

                # Find similar documents (potential negatives)
                similar_docs = self.find_similar_documents(doc_data, threshold=0.6)

                # Create negative samples by modifying questions
                negatives = []
                for similar_doc in similar_docs:
                    negative_query = self.create_negative_query(
                        doc_data['main_question'],
                        similar_doc['main_question']
                    )
                    negatives.append(negative_query)

                negative_samples[f"{collection}#{doc_id}"] = negatives

        return negative_samples

    def create_negative_query(self, target_question: str, similar_question: str) -> str:
        """Create negative sample by mixing target with similar question"""

        # Extract key differences
        target_words = set(target_question.lower().split())
        similar_words = set(similar_question.lower().split())

        # Words unique to similar question (potential confusion points)
        confusion_words = similar_words - target_words

        # Create negative by adding confusion words to target
        if confusion_words:
            confusion_phrase = ' '.join(list(confusion_words)[:3])
            negative = f"{target_question} {confusion_phrase}"
            return negative

        return target_question

    def calculate_contrastive_score(
        self,
        query: str,
        target_doc: Dict,
        doc_id: str
    ) -> float:
        """Calculate score using contrastive approach"""

        query_emb = self.embedding_model.encode([query])[0]

        # Positive score (similarity to target)
        target_emb = self.embedding_model.encode([target_doc['main_question']])[0]
        positive_score = cosine_similarity([query_emb], [target_emb])[0][0]

        # Negative score (similarity to negative samples)
        negatives = self.negative_samples.get(doc_id, [])
        if negatives:
            negative_embs = self.embedding_model.encode(negatives)
            negative_scores = cosine_similarity([query_emb], negative_embs)[0]
            max_negative_score = max(negative_scores) if len(negative_scores) > 0 else 0
        else:
            max_negative_score = 0

        # Contrastive score: positive - max_negative
        contrastive_score = positive_score - (max_negative_score * 0.3)  # Weight negative impact

        return max(0, contrastive_score)  # Ensure non-negative
```

**Ưu điểm**:

- Explicit learning để phân biệt similar documents
- Tự động generate negative samples
- Improve discrimination power

**Nhược điểm**:

- Computational overhead
- Cần careful tuning của negative weight

---

## PHƯƠNG ÁN 5: ENSEMBLE ROUTING WITH CONFIDENCE WEIGHTING ⭐⭐⭐⭐⭐

### 5.1 Multi-Model Ensemble

```python
class EnsembleRouter:
    """Kết hợp nhiều routing methods với dynamic weighting"""

    def __init__(self):
        self.routers = {
            'semantic': SemanticRouter(),
            'keyword': KeywordRouter(),
            'metadata': MetadataRouter(),
            'cost_based': CostBasedRouter()
        }
        self.weights = {
            'semantic': 0.4,
            'keyword': 0.2,
            'metadata': 0.25,
            'cost_based': 0.15
        }

    def route_with_ensemble(self, query: str) -> Dict[str, Any]:
        """Route using weighted ensemble of multiple methods"""

        results = {}
        for name, router in self.routers.items():
            result = router.route(query)
            results[name] = result

        # Aggregate scores với confidence weighting
        document_scores = defaultdict(float)
        total_confidence = 0

        for router_name, result in results.items():
            confidence = result.get('confidence', 0)
            doc_id = result.get('selected_document')

            if doc_id:
                weight = self.weights[router_name] * confidence
                document_scores[doc_id] += weight
                total_confidence += weight

        # Normalize scores
        if total_confidence > 0:
            document_scores = {
                doc: score / total_confidence
                for doc, score in document_scores.items()
            }

        best_doc = max(document_scores.items(), key=lambda x: x[1])

        return {
            'selected_document': best_doc[0],
            'ensemble_confidence': best_doc[1],
            'individual_results': results,
            'reasoning': self.explain_decision(results, best_doc)
        }

    def explain_decision(self, results: Dict, best_doc: Tuple) -> str:
        """Explain why this document was selected"""

        explanations = []
        for router_name, result in results.items():
            if result.get('selected_document') == best_doc[0]:
                conf = result.get('confidence', 0)
                explanations.append(f"{router_name}: {conf:.2f}")

        return f"Selected {best_doc[0]} based on: {', '.join(explanations)}"
```

### 5.2 Individual Router Implementations

```python
class KeywordRouter:
    """Simple keyword-based routing for fallback"""

    def route(self, query: str) -> Dict[str, Any]:
        keyword_scores = {}

        for collection, docs in self.documents.items():
            for doc_id, doc_data in docs.items():
                score = self.calculate_keyword_overlap(query, doc_data)
                keyword_scores[f"{collection}#{doc_id}"] = score

        best_doc = max(keyword_scores.items(), key=lambda x: x[1])

        return {
            'selected_document': best_doc[0],
            'confidence': best_doc[1],
            'method': 'keyword_matching'
        }

class MetadataRouter:
    """Route based on metadata matching"""

    def route(self, query: str) -> Dict[str, Any]:
        # Extract query features
        query_features = self.extract_query_features(query)

        metadata_scores = {}

        for collection, docs in self.documents.items():
            for doc_id, doc_data in docs.items():
                doc_metadata = self.get_document_metadata(collection, doc_id)
                score = self.calculate_metadata_match(query_features, doc_metadata)
                metadata_scores[f"{collection}#{doc_id}"] = score

        best_doc = max(metadata_scores.items(), key=lambda x: x[1])

        return {
            'selected_document': best_doc[0],
            'confidence': best_doc[1],
            'method': 'metadata_matching'
        }

    def extract_query_features(self, query: str) -> Dict[str, Any]:
        """Extract features from query"""

        features = {
            'has_cost_inquiry': any(w in query.lower() for w in ['phí', 'tiền', 'bao nhiêu']),
            'has_time_inquiry': any(w in query.lower() for w in ['bao lâu', 'thời gian', 'khi nào']),
            'has_requirement_inquiry': any(w in query.lower() for w in ['cần gì', 'giấy tờ', 'hồ sơ']),
            'has_combination_intent': any(w in query.lower() for w in ['kết hợp', 'cùng lúc', 'nhận cha']),
            'estimated_urgency': self.estimate_urgency(query)
        }

        return features

    def calculate_metadata_match(self, query_features: Dict, doc_metadata: Dict) -> float:
        """Calculate match score between query features and document metadata"""

        score = 0.0

        # Cost matching
        if query_features['has_cost_inquiry'] and 'fee_vnd' in doc_metadata:
            score += 0.2

        # Time matching
        if query_features['has_time_inquiry'] and 'processing_time_text' in doc_metadata:
            score += 0.2

        # Requirements matching
        if query_features['has_requirement_inquiry'] and 'requirements_conditions' in doc_metadata:
            score += 0.3

        # Combination intent matching
        if query_features['has_combination_intent']:
            if 'kết hợp' in doc_metadata.get('title', '').lower():
                score += 0.4
            else:
                score -= 0.2  # Penalty for wrong combination intent

        return max(0, min(1, score))

class CostBasedRouter:
    """Route based on cost/complexity preferences"""

    def route(self, query: str) -> Dict[str, Any]:
        cost_preferences = self.extract_cost_preferences(query)

        cost_scores = {}

        for collection, docs in self.documents.items():
            for doc_id, doc_data in docs.items():
                doc_metadata = self.get_document_metadata(collection, doc_id)
                score = self.calculate_cost_match(cost_preferences, doc_metadata)
                cost_scores[f"{collection}#{doc_id}"] = score

        best_doc = max(cost_scores.items(), key=lambda x: x[1])

        return {
            'selected_document': best_doc[0],
            'confidence': best_doc[1],
            'method': 'cost_based_routing'
        }

    def extract_cost_preferences(self, query: str) -> Dict[str, Any]:
        """Extract cost/complexity preferences from query"""

        preferences = {
            'prefers_simple': any(w in query.lower() for w in ['đơn giản', 'nhanh', 'thôi']),
            'accepts_complex': any(w in query.lower() for w in ['kết hợp', 'cùng lúc', 'đầy đủ']),
            'cost_sensitive': any(w in query.lower() for w in ['rẻ', 'tiết kiệm', 'miễn phí']),
            'time_sensitive': any(w in query.lower() for w in ['gấp', 'nhanh', 'ngay'])
        }

        return preferences

    def calculate_cost_match(self, preferences: Dict, doc_metadata: Dict) -> float:
        """Calculate cost-based matching score"""

        score = 0.5  # Base score

        doc_fee = doc_metadata.get('fee_vnd', 0)
        doc_title = doc_metadata.get('title', '').lower()

        # Simple procedure preference
        if preferences['prefers_simple']:
            if 'kết hợp' not in doc_title and doc_fee < 100000:
                score += 0.3
            else:
                score -= 0.2

        # Complex procedure acceptance
        if preferences['accepts_complex']:
            if 'kết hợp' in doc_title:
                score += 0.3

        # Cost sensitivity
        if preferences['cost_sensitive']:
            if doc_fee < 50000:
                score += 0.2
            elif doc_fee > 200000:
                score -= 0.3

        # Time sensitivity (favor simpler procedures)
        if preferences['time_sensitive']:
            processing_time = doc_metadata.get('processing_time_text', '')
            if 'ngay' in processing_time.lower():
                score += 0.2
            elif 'ngày' in processing_time.lower():
                score -= 0.1

        return max(0, min(1, score))
```

**Ưu điểm**:

- Robust với multiple fallbacks
- Explainable decisions
- Covers different routing aspects

**Nhược điểm**:

- More complex implementation
- Cần maintain multiple routers

---

# 🎯 IMPLEMENTATION PLAN

## Phase 1: Quick Wins (1-2 ngày) ⚡

### Option A: Enhanced Semantic Router (Phương án 2)

- **Target**: Cải thiện semantic calculation hiện tại
- **Implementation**:
  - Thêm weighted similarity calculation vào `_semantic_route_query`
  - Implement context boosters
  - Add metadata-aware scoring
- **Expected Impact**: 15-25% accuracy improvement
- **Risk**: Thấp - chỉ enhance existing logic

### Option B: Adaptive Thresholds (Phương án 3)

- **Target**: Dynamic threshold learning
- **Implementation**:
  - Add feedback collection endpoints
  - Implement threshold adjustment logic
  - Create confusion matrix tracking
- **Expected Impact**: 20-30% accuracy improvement over time
- **Risk**: Trung bình - cần user feedback system

## Phase 2: Medium Term (1 tuần) 🚀

### Option C: Hierarchical Router (Phương án 1)

- **Target**: Two-stage intent classification
- **Implementation**:
  - Auto-categorize existing documents into intent groups
  - Implement two-stage routing logic
  - Add intent classification layer
- **Expected Impact**: 30-40% accuracy improvement
- **Risk**: Trung bình - cần clustering implementation

### Option D: Ensemble Router (Phương án 5)

- **Target**: Multi-method routing with confidence weighting
- **Implementation**:
  - Implement individual routers (keyword, metadata, cost-based)
  - Create ensemble aggregation logic
  - Add decision explanation
- **Expected Impact**: 35-45% accuracy improvement
- **Risk**: Cao - nhiều components, phức tạp

## Phase 3: Advanced (2-3 tuần) 🏆

### Option E: Contrastive Learning (Phương án 4)

- **Target**: Advanced discrimination learning
- **Implementation**:
  - Generate negative samples for each document
  - Implement contrastive scoring
  - Add fine-tuning capabilities
- **Expected Impact**: 40-50% accuracy improvement
- **Risk**: Cao - requires ML expertise

---

# 🏆 RECOMMENDATIONS

## Immediate Action: ENHANCED SEMANTIC ROUTER (Phương án 2A)

**Lý do**:

- Fastest to implement
- Builds on existing codebase
- Low risk, moderate reward
- Có thể implement trong 1-2 ngày

## Medium Term: HIERARCHICAL ROUTER (Phương án 1)

**Lý do**:

- Scalable solution for thousands of documents
- Intuitive approach (intent → document)
- Maintainable architecture

## Long Term: ENSEMBLE + ADAPTIVE LEARNING (Phương án 5 + 3)

**Lý do**:

- Best accuracy potential
- Self-improving system
- Production-ready approach

---

# 📊 SUCCESS METRICS

## Immediate Goals (1 tuần):

- DOC_002 vs DOC_008 accuracy: > 85%
- Overall router accuracy: > 80%
- Response time: < 500ms

## Medium Goals (1 tháng):

- Overall router accuracy: > 90%
- User satisfaction score: > 4/5
- False positive rate: < 10%

## Long-term Goals (3 tháng):

- Support 1000+ documents
- Accuracy: > 95%
- Zero-configuration scaling

---

# 🔧 IMPLEMENTATION DETAILS

Mỗi phương án đều có detailed implementation guidelines và code examples trên. Bạn có thể chọn approach phù hợp với timeline và resources hiện tại.

**Recommendation**: Bắt đầu với **Enhanced Semantic Router** (Option A) để có quick wins, sau đó scale lên **Hierarchical Router** (Option C) cho long-term solution.
