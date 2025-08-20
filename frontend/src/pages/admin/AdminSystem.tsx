import { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Alert, AlertDescription } from "../../components/ui/alert";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import {
  Settings,
  Save,
  RotateCcw,
  Database,
  Cpu,
  Thermometer,
  Hash,
  CheckCircle,
  AlertTriangle,
  Info,
  FileText,
} from "lucide-react";

interface EnvConfig {
  // Core AI Settings
  MAX_TOKENS: number;
  TEMPERATURE: number;
  CONTEXT_LENGTH: number;
  N_CTX: number;
  N_GPU_LAYERS: number;

  // Search Settings
  BROAD_SEARCH_K: number;
  SIMILARITY_THRESHOLD: number;
  DEFAULT_SIMILARITY_THRESHOLD: number;

  // Server Settings
  DEBUG: boolean;
  HOST: string;
  PORT: number;

  // Feature Toggles
  USE_ROUTING: boolean;
  USE_RERANKER: boolean;
}

interface ConfigField {
  key: keyof EnvConfig;
  label: string;
  description: string;
  type: "integer" | "float" | "boolean" | "string";
  min?: number;
  max?: number;
  step?: number;
  icon: React.ReactNode;
  category: "ai" | "search" | "server" | "features";
  recommended?: number | boolean | string;
}

export default function AdminSystem() {
  const [config, setConfig] = useState<EnvConfig>({
    // AI Settings
    MAX_TOKENS: 1200,
    TEMPERATURE: 0.1,
    CONTEXT_LENGTH: 4096,
    N_CTX: 4096,
    N_GPU_LAYERS: -1,

    // Search Settings
    BROAD_SEARCH_K: 30,
    SIMILARITY_THRESHOLD: 0.35,
    DEFAULT_SIMILARITY_THRESHOLD: 0.4,

    // Server Settings
    DEBUG: true,
    HOST: "localhost",
    PORT: 8000,

    // Features
    USE_ROUTING: true,
    USE_RERANKER: true,
  });

  const [originalConfig, setOriginalConfig] = useState<EnvConfig>({
    ...config,
  });
  const [hasChanges, setHasChanges] = useState(false);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<string | null>(null);

  const configFields: ConfigField[] = [
    // AI Settings
    {
      key: "MAX_TOKENS",
      label: "Độ dài câu trả lời tối đa",
      description: "Số từ tối đa trong câu trả lời (1200 = ~4800 ký tự)",
      type: "integer",
      min: 500,
      max: 4000,
      step: 100,
      icon: <Hash className="h-4 w-4" />,
      category: "ai",
      recommended: 1200,
    },
    {
      key: "TEMPERATURE",
      label: "Mức độ sáng tạo",
      description: "0.1 = rất chính xác, 0.5 = cân bằng, 1.0 = sáng tạo",
      type: "float",
      min: 0.0,
      max: 1.0,
      step: 0.1,
      icon: <Thermometer className="h-4 w-4" />,
      category: "ai",
      recommended: 0.1,
    },
    {
      key: "CONTEXT_LENGTH",
      label: "Độ dài ngữ cảnh",
      description: "Số tokens tối đa để xử lý (4096 phù hợp 6GB VRAM)",
      type: "integer",
      min: 2048,
      max: 8192,
      step: 1024,
      icon: <Cpu className="h-4 w-4" />,
      category: "ai",
      recommended: 4096,
    },
    {
      key: "N_GPU_LAYERS",
      label: "Layers trên GPU",
      description: "Số layers chạy GPU (-1 = auto, 0 = chỉ CPU)",
      type: "integer",
      min: -1,
      max: 50,
      step: 1,
      icon: <Cpu className="h-4 w-4" />,
      category: "ai",
      recommended: -1,
    },

    // Search Settings
    {
      key: "BROAD_SEARCH_K",
      label: "Số tài liệu tìm kiếm",
      description: "Số tài liệu tìm kiếm trước khi lọc (30 = tìm rộng)",
      type: "integer",
      min: 10,
      max: 100,
      step: 5,
      icon: <Database className="h-4 w-4" />,
      category: "search",
      recommended: 30,
    },
    {
      key: "SIMILARITY_THRESHOLD",
      label: "Ngưỡng độ tương đồng",
      description: "Ngưỡng lọc kết quả (0.35 = lọc lỏng, 0.7 = lọc chặt)",
      type: "float",
      min: 0.1,
      max: 0.9,
      step: 0.05,
      icon: <Database className="h-4 w-4" />,
      category: "search",
      recommended: 0.35,
    },

    // Features
    {
      key: "USE_ROUTING",
      label: "Sử dụng định tuyến thông minh",
      description: "Tự động chọn collection phù hợp cho câu hỏi",
      type: "boolean",
      icon: <Settings className="h-4 w-4" />,
      category: "features",
      recommended: true,
    },
    {
      key: "USE_RERANKER",
      label: "Sử dụng sắp xếp lại kết quả",
      description: "Cải thiện độ chính xác bằng reranking",
      type: "boolean",
      icon: <Settings className="h-4 w-4" />,
      category: "features",
      recommended: true,
    },
  ];

  const handleConfigChange = (
    key: keyof EnvConfig,
    value: number | boolean | string
  ) => {
    setConfig((prev) => ({
      ...prev,
      [key]: value,
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // TODO: Save to backend .env file
      await new Promise((resolve) => setTimeout(resolve, 1000));

      console.log("Saving config to .env:", config);

      setOriginalConfig({ ...config });
      setHasChanges(false);
      setLastSaved(new Date().toLocaleTimeString("vi-VN"));
    } catch (error) {
      console.error("Error saving config:", error);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setConfig({ ...originalConfig });
    setHasChanges(false);
  };

  const handleResetToRecommended = () => {
    const recommendedConfig: EnvConfig = {
      MAX_TOKENS: 1200,
      TEMPERATURE: 0.1,
      CONTEXT_LENGTH: 4096,
      N_CTX: 4096,
      N_GPU_LAYERS: -1,
      BROAD_SEARCH_K: 30,
      SIMILARITY_THRESHOLD: 0.35,
      DEFAULT_SIMILARITY_THRESHOLD: 0.4,
      DEBUG: true,
      HOST: "localhost",
      PORT: 8000,
      USE_ROUTING: true,
      USE_RERANKER: true,
    };
    setConfig(recommendedConfig);
    setHasChanges(true);
  };

  const getFieldsByCategory = (category: string) => {
    return configFields.filter((field) => field.category === category);
  };

  const CategoryCard = ({
    title,
    description,
    icon,
    fields,
  }: {
    title: string;
    description: string;
    icon: React.ReactNode;
    fields: ConfigField[];
  }) => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          {icon}
          <span>{title}</span>
        </CardTitle>
        <p className="text-sm text-gray-600">{description}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        {fields.map((field) => (
          <div key={field.key} className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="flex items-center space-x-2">
                {field.icon}
                <span>{field.label}</span>
              </Label>
              {field.recommended !== undefined && (
                <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                  Khuyến nghị: {field.recommended.toString()}
                </span>
              )}
            </div>

            <p className="text-sm text-gray-600">{field.description}</p>

            <div className="flex items-center space-x-3">
              {field.type === "boolean" ? (
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={config[field.key] as boolean}
                    onChange={(e) =>
                      handleConfigChange(field.key, e.target.checked)
                    }
                    className="rounded"
                  />
                  <span className="text-sm">
                    {config[field.key] ? "Bật" : "Tắt"}
                  </span>
                </label>
              ) : field.type === "string" ? (
                <Input
                  value={config[field.key] as string}
                  onChange={(e) =>
                    handleConfigChange(field.key, e.target.value)
                  }
                  className="max-w-xs"
                />
              ) : (
                <>
                  <Input
                    type="number"
                    value={config[field.key] as number}
                    onChange={(e) =>
                      handleConfigChange(
                        field.key,
                        field.type === "integer"
                          ? parseInt(e.target.value) || 0
                          : parseFloat(e.target.value) || 0
                      )
                    }
                    min={field.min}
                    max={field.max}
                    step={field.step}
                    className="w-32"
                  />
                  {field.min !== undefined && field.max !== undefined && (
                    <div className="flex-1 text-xs text-gray-400">
                      {field.min} - {field.max}
                    </div>
                  )}
                </>
              )}
            </div>

            {field.recommended !== undefined &&
              config[field.key] !== field.recommended && (
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription className="text-sm">
                    Giá trị khuyến nghị:{" "}
                    <strong>{field.recommended.toString()}</strong>
                  </AlertDescription>
                </Alert>
              )}
          </div>
        ))}
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Cài đặt hệ thống</h1>
        <p className="text-gray-600 mt-2">
          Điều chỉnh cấu hình hoạt động của hệ thống AI
        </p>
      </div>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          <strong>Lưu ý:</strong> Thay đổi cài đặt sẽ ghi vào file{" "}
          <code>backend/.env</code>. Khởi động lại server để áp dụng một số thay
          đổi.
        </AlertDescription>
      </Alert>

      {/* Status */}
      {lastSaved && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>Đã lưu thành công!</strong> Lần cuối: {lastSaved}
          </AlertDescription>
        </Alert>
      )}

      {/* Configuration Categories */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CategoryCard
          title="Cài đặt AI"
          description="Điều chỉnh tham số mô hình AI và chất lượng câu trả lời"
          icon={<Cpu className="h-5 w-5 text-blue-600" />}
          fields={getFieldsByCategory("ai")}
        />

        <CategoryCard
          title="Cài đặt tìm kiếm"
          description="Điều chỉnh cách thức tìm kiếm và lọc tài liệu"
          icon={<Database className="h-5 w-5 text-green-600" />}
          fields={getFieldsByCategory("search")}
        />

        <CategoryCard
          title="Tính năng"
          description="Bật/tắt các tính năng nâng cao của hệ thống"
          icon={<Settings className="h-5 w-5 text-purple-600" />}
          fields={getFieldsByCategory("features")}
        />

        {/* Environment File Preview */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-orange-600" />
              <span>File cấu hình (.env)</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto">
              <div className="space-y-1">
                <div># AI Configuration</div>
                <div>MAX_TOKENS={config.MAX_TOKENS}</div>
                <div>TEMPERATURE={config.TEMPERATURE}</div>
                <div>CONTEXT_LENGTH={config.CONTEXT_LENGTH}</div>
                <div>N_GPU_LAYERS={config.N_GPU_LAYERS}</div>
                <div></div>
                <div># Search Configuration</div>
                <div>BROAD_SEARCH_K={config.BROAD_SEARCH_K}</div>
                <div>SIMILARITY_THRESHOLD={config.SIMILARITY_THRESHOLD}</div>
                <div></div>
                <div># Features</div>
                <div>USE_ROUTING={config.USE_ROUTING.toString()}</div>
                <div>USE_RERANKER={config.USE_RERANKER.toString()}</div>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Đường dẫn: backend/.env
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
        <Button
          onClick={handleSave}
          disabled={!hasChanges || saving}
          className="flex items-center space-x-2"
        >
          <Save className="h-4 w-4" />
          <span>{saving ? "Đang lưu..." : "Lưu vào .env"}</span>
        </Button>

        <Button
          variant="outline"
          onClick={handleReset}
          disabled={!hasChanges}
          className="flex items-center space-x-2"
        >
          <RotateCcw className="h-4 w-4" />
          <span>Hoàn tác</span>
        </Button>

        <Button
          variant="outline"
          onClick={handleResetToRecommended}
          className="flex items-center space-x-2"
        >
          <Settings className="h-4 w-4" />
          <span>Khôi phục khuyến nghị</span>
        </Button>
      </div>

      {hasChanges && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <strong>Có thay đổi chưa lưu!</strong> Nhớ nhấn "Lưu vào .env" để áp
            dụng cài đặt.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
