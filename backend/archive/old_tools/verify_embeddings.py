# file: backend/verify_embeddings.py
import logging
import sys
from pathlib import Path
import numpy as np

# Thêm đường dẫn 'backend' vào sys.path để import từ 'app'
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

import chromadb
from app.core.config import settings

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def verify_data_in_db():
    logging.info("--- BẮT ĐẦU KIỂM TRA DỮ LIỆU VÀ EMBEDDING TRONG DATABASE ---")
    logging.info(f"Đang kết nối tới database tại: {settings.chroma_persist_directory}")

    try:
        client = chromadb.PersistentClient(path=settings.chroma_persist_directory)
        collections = client.list_collections()

        if not collections:
            logging.warning("Không tìm thấy collection nào trong database.")
            return

        logging.info(f"Tìm thấy {len(collections)} collection(s).")

        for collection_obj in collections:
            collection_name = collection_obj.name
            logging.info(f"\n=========================================")
            logging.info(f"🔬 Đang kiểm tra collection: '{collection_name}'")
            logging.info(f"=========================================")

            count = collection_obj.count()
            if count == 0:
                logging.warning("Collection này rỗng.")
                continue

            logging.info(f"Collection có {count} mục. Lấy 3 mục đầu tiên để kiểm tra...")

            # Lấy dữ liệu bao gồm cả documents và embeddings
            items = collection_obj.get(
                limit=3,
                include=["documents", "embeddings", "metadatas"]
            )

            for i in range(len(items['ids'])):
                doc_id = items['ids'][i]
                document = items['documents'][i]
                embedding = items['embeddings'][i]
                metadata = items['metadatas'][i]

                logging.info(f"\n--- Mục #{i+1} (ID: {doc_id}) ---")
                logging.info(f"   📄 Document (preview): '{document[:150].strip().replace(chr(10), ' ')}...'")
                logging.info(f"   🔖 Metadata (title): {metadata.get('document_title', 'N/A')}")
                
                if embedding:
                    # Chuyển thành numpy array để kiểm tra
                    embedding_np = np.array(embedding)
                    is_all_zeros = np.all(embedding_np == 0)

                    logging.info(f"   🧬 Embedding (10 giá trị đầu): {embedding_np[:10]}")
                    
                    if is_all_zeros:
                        logging.error("   🚨 CẢNH BÁO: EMBEDDING NÀY TOÀN SỐ 0! ĐÂY LÀ NGUYÊN NHÂN GÂY LỖI.")
                    else:
                        logging.info("   👍 Embedding có vẻ hợp lệ (khác 0).")
                else:
                    logging.error("   🚨 LỖI: Không có embedding cho mục này.")

    except Exception as e:
        logging.error(f"Lỗi nghiêm trọng khi thực thi: {e}", exc_info=True)

if __name__ == "__main__":
    verify_data_in_db()