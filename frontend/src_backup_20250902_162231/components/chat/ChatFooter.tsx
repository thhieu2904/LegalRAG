import { ContextInfoModal } from "./ContextInfoModal";

export function ChatFooter() {
  return (
    <div className="chat-footer-container">
      <div className="chat-footer-content">
        <div className="chat-footer-organization">
          <span className="chat-footer-label">Cơ quan chủ quản:</span> TRUNG TÂM
          PHỤ VỤ HÀNH CHÍNH CÔNG XÃ LONG PHÚ
        </div>
        <div className="chat-footer-contact">
          <span className="chat-footer-label">Địa chỉ:</span> Ấp 4, xã Long Phú
          - TP Cần Thơ | <span className="chat-footer-label">Điện thoại:</span>{" "}
          0907007397
        </div>
        {/* <span className="chat-footer-label"> Fax:</span> 02993.857.430 |
          <span className="chat-footer-label"> Email:</span>{" "}
          vanphong.huyenlp@soctrang.gov.vn */}
      </div>

      {/* 🔥 NEW: Context Info Modal in footer */}
      <ContextInfoModal />

      {/* <span className="chat-footer-label"> Fax:</span> 02993.857.430 |
      <span className="chat-footer-label"> Email:</span>{" "}
      vanphong.huyenlp@soctrang.gov.vn */}
    </div>
  );
}
