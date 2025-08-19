import logoHCC from "../../assets/LOGO_HCC.jpg";

export function ChatHeader() {
  return (
    <div className="bg-white border-b shadow-sm">
      {/* Main header bar */}
      <div className="flex items-center px-6 py-4">
        {/* Logo bên trái */}
        <div className="w-1/4 flex items-center">
          <img
            src={logoHCC}
            alt="Logo Trung tâm Hành chính công"
            className="w-12 h-12 object-contain"
          />
        </div>

        {/* Tên trung tâm ở giữa */}
        <div className="w-1/2 text-center">
          <h1 className="font-medium text-red-600 text-lg">
            TRUNG TÂM PHỤC VỤ HÀNH CHÍNH CÔNG XÃ LONG PHÚ
          </h1>
        </div>

        {/* Thông tin trợ lý AI bên phải */}
        <div className="w-1/4 text-right">
          <div className="font-medium text-blue-600 text-base">
            Trợ lý Pháp luật AI
          </div>
          <div className="text-gray-600 text-sm mt-1">
            Hệ thống hỗ trợ thông tin thủ tục hành chính
          </div>
        </div>
      </div>
    </div>
  );
}
