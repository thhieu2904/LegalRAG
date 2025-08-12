# file: backend/rebuild.py
import logging
import sys
from pathlib import Path

# Thêm đường dẫn 'backend' vào sys.path để có thể import từ 'app'
# Điều này giúp script chạy được từ thư mục backend
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.services.llm_service import LLMService
from app.services.vectordb_service import VectorDBService
from app.services.rag_service import RAGService

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("--- BẮT ĐẦU QUÁ TRÌNH XÂY DỰNG LẠI DATABASE CHÍNH THỨC ---")
    logging.info(f"Sử dụng thư mục database: {settings.vectordb_path}")
    logging.info(f"Sử dụng thư mục tài liệu: {settings.documents_path}")

    try:
        # Xóa thư mục vectordb cũ để đảm bảo làm mới hoàn toàn
        # Đây là bước quan trọng để tránh dữ liệu cũ còn sót lại
        import shutil
        if settings.vectordb_path.exists():
            logging.warning(f"Đang xóa database cũ tại: {settings.vectordb_path}")
            shutil.rmtree(settings.vectordb_path)
        settings.vectordb_path.mkdir(parents=True, exist_ok=True)
        logging.info("Đã xóa và tạo lại thư mục database.")

        # Khởi tạo các service cần thiết
        llm_service = LLMService(
            model_path=str(settings.llm_model_file_path),
            model_url=settings.llm_model_url,
            n_ctx=settings.n_ctx
        )
        vectordb_service = VectorDBService(
            persist_directory=str(settings.vectordb_path),
            embedding_model=settings.embedding_model_name
        )
        rag_service = RAGService(
            documents_dir=str(settings.documents_path),
            vectordb_service=vectordb_service,
            llm_service=llm_service
        )

        # Chạy hàm build_index
        logging.info("Bắt đầu xử lý tài liệu và nạp vào ChromaDB...")
        # Không cần force_rebuild=True nữa vì chúng ta đã tự xóa thư mục
        result = rag_service.build_index()

        if result.get('status') == 'success':
            logging.info("✅ HOÀN TẤT: Xây dựng lại cơ sở dữ liệu thành công!")
            logging.info(f"   - Chi tiết: {result.get('message')}")
        else:
            logging.error(f"❌ LỖI: {result.get('message')}")

    except Exception as e:
        logging.error(f"Lỗi nghiêm trọng không xác định: {e}", exc_info=True)

if __name__ == "__main__":
    main()