# Rerank Service

Vietnamese document reranking service using `AITeamVN/Vietnamese_Reranker`.

## Features

- **Cross-Encoder Reranking**: Re-scores query-document pairs for better relevance
- **Vietnamese Optimized**: Fine-tuned for Vietnamese legal documents
- **GPU Support**: Optional CUDA acceleration
- **Batch Processing**: Efficient batch inference
- **Health Monitoring**: Health check endpoints

## Architecture

```
Query + Candidates → Cross-Encoder → Relevance Scores → Top-K Results
```

## API Endpoints

### POST /rerank

Rerank documents based on query relevance.

**Request:**

```json
{
  "query": "điều kiện thành lập công ty",
  "documents": [
    "Văn bản về điều kiện thành lập doanh nghiệp...",
    "Hướng dẫn đăng ký kinh doanh...",
    "Quy định về vốn điều lệ..."
  ],
  "top_k": 5
}
```

**Response:**

```json
{
  "results": [
    {
      "index": 0,
      "text": "Văn bản về điều kiện thành lập doanh nghiệp...",
      "score": 0.8934,
      "rank": 1
    }
  ],
  "processing_time": 0.023
}
```

### GET /health

Health check endpoint.

## Environment Variables

See `.env.example` for all configuration options.

Key variables:

- `MODEL_NAME`: HuggingFace model identifier
- `DEVICE`: cpu or cuda
- `BATCH_SIZE`: Inference batch size
- `TOP_K`: Default number of results

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python src/main.py

# Run with Docker
docker build -t rerank-service .
docker run -p 8013:8013 --env-file .env rerank-service
```

## Performance

- **CPU**: ~50ms per batch (16 pairs)
- **GPU**: ~10ms per batch (64 pairs)
- **Accuracy**: +25% MRR improvement over BM25

## Model Details

- **Model**: AITeamVN/Vietnamese_Reranker
- **Max Length**: 2304 tokens
- **Input**: Query + Document pairs
- **Output**: Relevance scores (0-1)
