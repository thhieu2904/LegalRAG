"""
Frontend API Configuration
Updates to connect to the new microservices architecture
"""

# API URLs - Load from environment variables with fallbacks

QUERY_SERVICE_URL = process.env.VITE_QUERY_SERVICE_URL || 'http://localhost:8005'
ADMIN_SERVICE_URL = process.env.VITE_ADMIN_SERVICE_URL || 'http://localhost:8007'
IDENTIFILL_SERVICE_URL = process.env.VITE_IDENTIFILL_SERVICE_URL || 'http://localhost:8002'
STORAGE_SERVICE_URL = process.env.VITE_STORAGE_SERVICE_URL || 'http://localhost:8001'

# ============================================

# Query Service Endpoints

# ============================================

class QueryAPI:
@staticmethod
async def query(question: str, top_k: int = 10) -> dict:
"""
POST /query
Ask a question and get an answer with sources
"""
const response = await fetch(`${QUERY_SERVICE_URL}/query`, {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({
question,
top_k
})
})
return response.json()

# ============================================

# Admin Service Endpoints

# ============================================

class AdminAPI:
@staticmethod
async def uploadDocument(file: File) -> dict:
"""
POST /upload
Upload and process a document (PDF, DOCX, TXT)
Returns: document_id, chunk count, status
"""
const formData = new FormData()
formData.append('file', file)

        const response = await fetch(`${ADMIN_SERVICE_URL}/upload`, {
            method: 'POST',
            body: formData
        })
        return response.json()

    @staticmethod
    async def listDocuments() -> dict:
        """
        GET /documents
        List all uploaded documents
        """
        const response = await fetch(`${ADMIN_SERVICE_URL}/documents`)
        return response.json()

    @staticmethod
    async def deleteDocument(documentId: str) -> dict:
        """
        DELETE /documents/{id}
        Delete a document (soft delete)
        """
        const response = await fetch(`${ADMIN_SERVICE_URL}/documents/${documentId}`, {
            method: 'DELETE'
        })
        return response.json()

# ============================================

# Identifill Service Endpoints (unchanged)

# ============================================

class IdentifillAPI:
@staticmethod
async def scanCCCD(image: File) -> dict:
"""
POST /scan
Scan CCCD card image and extract information
"""
const formData = new FormData()
formData.append('image', image)

        const response = await fetch(`${IDENTIFILL_SERVICE_URL}/scan`, {
            method: 'POST',
            body: formData
        })
        return response.json()

# ============================================

# Storage Service Endpoints (for direct file access)

# ============================================

class StorageAPI:
@staticmethod
async def downloadFile(documentId: str, filename: str) -> Blob:
"""
GET /download
Download a file from MinIO storage
"""
const response = await fetch(
`${STORAGE_SERVICE_URL}/download?document_id=${documentId}&filename=${filename}`
)
return response.blob()

    @staticmethod
    async def listFiles(documentId: str) -> dict:
        """
        GET /list
        List files in a document folder
        """
        const response = await fetch(
            `${STORAGE_SERVICE_URL}/list?document_id=${documentId}`
        )
        return response.json()

# ============================================

# Usage Examples in React Components

# ============================================

# Example: Upload Document

"""
import { AdminAPI } from '@/api/client'

function UploadComponent() {
const handleUpload = async (file: File) => {
try {
const result = await AdminAPI.uploadDocument(file)
console.log(`Document uploaded: ${result.document_id}`)
console.log(`Processed ${result.message}`)
} catch (error) {
console.error('Upload failed:', error)
}
}
return <input type="file" onChange={(e) => handleUpload(e.target.files[0])} />
}
"""

# Example: Query Documents

"""
import { QueryAPI } from '@/api/client'

function QueryComponent() {
const handleQuery = async (question: string) => {
try {
const result = await QueryAPI.query(question)
console.log('Answer:', result.answer)
console.log('Sources:', result.sources)
console.log('Token count:', result.token_count)
} catch (error) {
console.error('Query failed:', error)
}
}
return <input type="text" onChange={(e) => handleQuery(e.target.value)} />
}
"""
