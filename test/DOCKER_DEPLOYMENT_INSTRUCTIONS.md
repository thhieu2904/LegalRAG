
🚀 DOCKER DEPLOYMENT INSTRUCTIONS
================================

1. Pre-deployment Validation:
   - Run this script to ensure all modifications are in place
   - Verify Docker and Docker Compose are installed
   - Ensure GPU drivers are properly configured (if using GPU)

2. Build and Deploy:
   ```bash
   # Navigate to project root
   cd D:\Personal\LegalRAG_OCR
   
   # Build Docker images
   docker-compose build
   
   # Start services
   docker-compose up -d
   
   # Check service status
   docker-compose ps
   
   # View logs
   docker-compose logs rag-service
   ```

3. Validation in Docker:
   ```bash
   # Test API endpoint
   curl http://localhost:8000/health
   
   # Check environment inside container
   docker exec legalrag-rag-service python -c "
   from app.core.path_config import PathConfig
   config = PathConfig()
   print(f'Environment: {config.environment}')
   print(f'Base data dir: {config.base_data_dir}')
   print(f'Collections dir: {config.collections_dir}')
   "
   ```

4. Path Verification:
   ```bash
   # Check paths exist in container
   docker exec legalrag-rag-service ls -la /app/data/
   docker exec legalrag-rag-service ls -la /app/data/storage/
   ```

5. Service Testing:
   ```bash
   # Test form detection service
   docker exec legalrag-rag-service python -c "
   from app.services.simple_form_detection import SimpleFormDetectionService
   service = SimpleFormDetectionService()
   print(f'Service environment: {service.path_config.environment}')
   print(f'Storage path: {service.storage_base_path}')
   "
   ```

6. Troubleshooting:
   - If paths don't work: Check environment variables are set correctly
   - If services fail: Check logs with 'docker-compose logs rag-service'
   - If data missing: Ensure volume mount './rag_service/data:/app/data' is working

7. Rollback Plan:
   ```bash
   # Stop services
   docker-compose down
   
   # Remove containers and images if needed
   docker-compose down --rmi all
   ```

⚠️ IMPORTANT NOTES:
- Environment variables in docker-compose.yml will override PathConfig defaults
- Data directory is mounted from local rag_service/data to /app/data in container
- PathConfig will automatically detect Docker environment and use correct paths
- Backward compatibility is maintained for any existing integrations
