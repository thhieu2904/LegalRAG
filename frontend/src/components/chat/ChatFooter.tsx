import { ContextInfoModal } from "./ContextInfoModal";

export function ChatFooter() {
  return (
    <div className="bg-gray-100 border-t border-gray-200 py-3 relative">
      <div className="text-center text-gray-600 text-sm space-y-1">
        <div>
          <span className="font-medium">Cơ quan chủ quản:</span> TRUNG TÂM PHỤ
          VỤ HÀNH CHÍNH CÔNG XÃ LONG PHÚ
        </div>
        <div>
          <span className="font-medium">Địa chỉ:</span> Ấp 4, xã Long Phú - TP
          Cần Thơ | <span className="font-medium">Điện thoại:</span> 0907007397
        </div>
        {/* <span className="font-medium"> Fax:</span> 02993.857.430 |
          <span className="font-medium"> Email:</span>{" "}
          vanphong.huyenlp@soctrang.gov.vn */}
      </div>

      {/* 🔥 NEW: Context Info Modal in footer */}
      <ContextInfoModal />

      {/* <span className="font-medium"> Fax:</span> 02993.857.430 |
      <span className="font-medium"> Email:</span>{" "}
      vanphong.huyenlp@soctrang.gov.vn */}
    </div>
  );
}
