/**
 * 🗃️ UPDATED DATABASE COMPONENT
 * Sử dụng admin API thay vì mock data
 */

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Badge } from "../../components/ui/badge";
import {
  FolderOpen,
  FileText,
  Plus,
  Edit,
  Trash2,
  Upload,
  Search,
  File,
  FilePlus,
  Download,
  Eye,
  CheckCircle,
  Clock,
  AlertCircle,
  Settings,
  Filter,
  RefreshCw,
  Database,
  FileCheck,
  FileX,
  Loader,
  ArrowUpDown,
  ChevronDown,
} from "lucide-react";
import type {
  LegalCollection,
  LegalDocument,
  ProcessingStep,
} from "../../types/admin";
import { useModal } from "../../hooks/useModal";
import {
  CollectionModal,
  DocumentModal,
  DocumentViewModal,
  DeleteModal,
} from "../../components/admin/modals/DatabaseModals";
import { 
  fetchCollections, 
  fetchCollectionDocuments,
  type AdminCollection,
  type AdminDocument 
} from "../../api/admin-api";

export default function AdminDatabase() {
  const [selectedCollection, setSelectedCollection] =
    useState<LegalCollection | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus] = useState<string>("all");
  const [filterCategory] = useState<string>("all");

  // API state management
  const [collections, setCollections] = useState<LegalCollection[]>([]);
  const [adminCollections, setAdminCollections] = useState<AdminCollection[]>([]);
  const [adminDocuments, setAdminDocuments] = useState<AdminDocument[]>([]);
  const [isLoadingCollections, setIsLoadingCollections] = useState(false);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Modal management
  const collectionModal = useModal();
  const documentModal = useModal();
  const viewModal = useModal();
  const deleteModal = useModal();

  // Load collections from admin API
  useEffect(() => {
    loadCollections();
  }, []);

  // Load documents when collection is selected
  useEffect(() => {
    if (selectedCollection) {
      loadDocuments(selectedCollection.name);
    }
  }, [selectedCollection]);

  const loadCollections = async () => {
    try {
      setIsLoadingCollections(true);
      setError(null);
      console.log("🗃️ Loading collections from admin API...");
      
      const adminCollectionsData = await fetchCollections();
      setAdminCollections(adminCollectionsData);
      
      // Convert AdminCollection to LegalCollection format for UI compatibility
      const legacyCollections: LegalCollection[] = adminCollectionsData.map(adminCol => ({
        id: adminCol.name,
        name: adminCol.name,
        displayName: adminCol.display_name,
        documentCount: adminCol.document_count,
        updatedAt: new Date().toISOString().split('T')[0], // Today's date as fallback
        description: adminCol.description,
        status: "active" as const,
        totalSize: adminCol.document_count * 1000000, // Estimate 1MB per document
        category: "procedure" as const, // Default category
        createdAt: new Date().toISOString().split('T')[0],
      }));
      
      setCollections(legacyCollections);
      console.log(`✅ Loaded ${legacyCollections.length} collections`);
      
    } catch (err) {
      console.error("❌ Error loading collections:", err);
      setError("Không thể tải danh sách collections. Vui lòng thử lại.");
    } finally {
      setIsLoadingCollections(false);
    }
  };

  const loadDocuments = async (collectionName: string) => {
    try {
      setIsLoadingDocuments(true);
      setError(null);
      console.log(`🗃️ Loading documents for collection: ${collectionName}`);
      
      const documentsData = await fetchCollectionDocuments(collectionName);
      setAdminDocuments(documentsData);
      
      console.log(`✅ Loaded ${documentsData.length} documents`);
      
    } catch (err) {
      console.error(`❌ Error loading documents for ${collectionName}:`, err);
      setError(`Không thể tải documents cho collection ${collectionName}`);
      setAdminDocuments([]);
    } finally {
      setIsLoadingDocuments(false);
    }
  };

  // Convert AdminDocument to LegalDocument format for UI compatibility
  const convertToLegalDocuments = (adminDocs: AdminDocument[]): LegalDocument[] => {
    return adminDocs.map(adminDoc => ({
      id: adminDoc.doc_id,
      collectionId: selectedCollection?.name || "",
      name: adminDoc.title,
      fileName: adminDoc.source_file.replace(/\.[^/.]+$/, ""), // Remove extension
      title: adminDoc.title,
      version: "1.0",
      status: adminDoc.status === "active" ? "processed" as const : "error" as const,
      documentType: "regulation" as const,
      language: "vi" as const,
      tags: [adminDoc.code],
      documentNumber: adminDoc.code,
      issuedBy: adminDoc.executing_agency,
      issuedDate: adminDoc.effective_date,
      effectiveDate: adminDoc.effective_date,
      createdAt: adminDoc.effective_date,
      updatedAt: adminDoc.effective_date,
      sourceFile: {
        id: `${adminDoc.doc_id}_source`,
        filename: adminDoc.source_file,
        originalName: adminDoc.source_file,
        path: `/docs/${adminDoc.source_file}`,
        size: 1000000, // Default 1MB
        mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        uploadedAt: adminDoc.effective_date,
        status: "processed" as const,
      },
      processedFile: adminDoc.has_processed_json ? {
        id: `${adminDoc.doc_id}_json`,
        filename: `${adminDoc.doc_id}.json`,
        originalName: `${adminDoc.doc_id}.json`,
        path: `/docs/${adminDoc.doc_id}.json`,
        size: 500000,
        mimeType: "application/json",
        uploadedAt: adminDoc.effective_date,
        status: "processed" as const,
      } : undefined,
      formFile: adminDoc.has_forms ? {
        id: `${adminDoc.doc_id}_form`,
        filename: `form_${adminDoc.doc_id}.pdf`,
        originalName: `Form ${adminDoc.title}.pdf`,
        path: `/forms/form_${adminDoc.doc_id}.pdf`,
        size: 1000000,
        mimeType: "application/pdf",
        uploadedAt: adminDoc.effective_date,
        status: "processed" as const,
      } : undefined,
      questionsFile: adminDoc.has_questions ? {
        id: `${adminDoc.doc_id}_questions`,
        filename: `questions_${adminDoc.doc_id}.json`,
        originalName: `Questions ${adminDoc.title}.json`,
        path: `/questions/questions_${adminDoc.doc_id}.json`,
        size: 100000,
        mimeType: "application/json",
        uploadedAt: adminDoc.effective_date,
        status: "processed" as const,
      } : undefined,
      processingSteps: [],
      metadata: {
        applicantType: adminDoc.applicant_type,
        processingTime: adminDoc.processing_time_text,
        fee: adminDoc.fee_text,
        feeAmount: adminDoc.fee_vnd,
        questionCount: adminDoc.question_count,
        formCount: adminDoc.form_count,
      }
    }));
  };

  // Get documents for current collection
  const documents = convertToLegalDocuments(adminDocuments);

  // Filter collections and documents based on search term
  const filteredCollections = collections.filter((collection) =>
    collection.displayName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    collection.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredDocuments = documents.filter((doc) =>
    doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.documentNumber.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "processed":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "processing":
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <File className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      processed: "default" as const,
      processing: "secondary" as const,
      error: "destructive" as const,
      active: "default" as const,
    };
    return variants[status as keyof typeof variants] || "secondary";
  };

  if (error) {
    return (
      <div className="p-6">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
            <Button 
              onClick={loadCollections} 
              className="mt-4"
              variant="outline"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Thử lại
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }