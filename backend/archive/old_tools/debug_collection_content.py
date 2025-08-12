import chromadb
import logging
from chromadb.config import Settings

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Tắt Telemetry để log gọn gàng hơn (Tùy chọn) ---
# Thêm dòng này vào cài đặt client để tránh các lỗi "Failed to send telemetry"
client_settings = Settings(anonymized_telemetry=False)
client = chromadb.PersistentClient(path="./chroma_db", settings=client_settings)

COLLECTION_NAMES = ["ho_tich_cap_xa", "nuoi_con_nuoi", "chung_thuc"]

def debug_collection(collection_name):
    """
    Hàm để kiểm tra và in ra nội dung của một collection trong ChromaDB.
    """
    try:
        logging.info(f"\n==================================================")
        logging.info(f"Đang kiểm tra collection: {collection_name}")
        logging.info(f"==================================================")

        # Lấy collection
        collection = client.get_collection(name=collection_name)
        
        # Đếm số lượng documents
        count = collection.count()
        logging.info(f"Collection '{collection_name}' có {count} documents.")

        if count == 0:
            logging.warning(f"Collection '{collection_name}' rỗng!")
            return

        # Lấy 5 documents đầu tiên để kiểm tra
        # Sửa lỗi từ script cũ của bạn: 'include' phải là một list các trường muốn lấy
        items = collection.get(
            limit=5,
            include=['documents', 'metadatas', 'embeddings']
        )

        # In thông tin chi tiết của từng item
        for i in range(len(items['ids'])):
            doc_id = items['ids'][i]
            document = items['documents'][i]
            metadata = items['metadatas'][i]
            embedding = items['embeddings'][i] # Lấy vector embedding

            logging.info(f"\n--- Item #{i+1} trong '{collection_name}' ---")
            logging.info(f"  ID: {doc_id}")
            logging.info(f"  Metadata: {metadata}")
            # In một phần document để xem trước
            logging.info(f"  Document (preview): {document[:200]}...") 
            
            # Kiểm tra embedding
            if embedding:
                # Kiểm tra xem có phải tất cả đều là 0 không
                is_all_zeros = all(v == 0.0 for v in embedding)
                logging.info(f"  Embedding (đầu tiên 10 chiều): {embedding[:10]}")
                if is_all_zeros:
                    logging.error("  CẢNH BÁO: Vector embedding này TOÀN SỐ 0!")
            else:
                logging.error("  LỖI: Không tìm thấy embedding cho item này.")

    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra collection {collection_name}: {e}")

if __name__ == "__main__":
    for name in COLLECTION_NAMES:
        debug_collection(name)