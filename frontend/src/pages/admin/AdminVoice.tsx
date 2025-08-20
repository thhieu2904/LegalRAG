import VoiceManagement from "../../components/VoiceManagement";

export default function AdminVoice() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Quản lý Giọng nói</h1>
        <p className="text-gray-600 mt-2">
          Cấu hình và quản lý tính năng Text-to-Speech của hệ thống
        </p>
      </div>

      <VoiceManagement />
    </div>
  );
}
