"""
Session Persistence Manager
===========================

Quản lý lưu trữ dữ liệu session và counter vào file JSON để tránh mất dữ liệu khi container restart.

Features:
- 💾 Lưu daily counter vào file (persistent across restarts)
- 📁 Lưu individual session data vào JSON files
- 🔄 Load counter từ file khi startup
- 🧹 Cleanup old sessions theo policy
- 📊 Statistics và monitoring

Architecture:
    /app/data/sessions/
    ├── daily_counter.json              # Counter hiện tại
    ├── sessions/
    │   ├── 20251019-001.json
    │   ├── 20251019-002.json
    │   └── 20251019-042.json          # Most recent
    └── metadata.json                   # Backup metadata
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import asdict, is_dataclass

logger = logging.getLogger(__name__)


class SessionPersistenceManager:
    """Quản lý persistent storage cho sessions và counter"""

    def __init__(self, storage_path: str = "/app/data/sessions"):
        """
        Initialize SessionPersistenceManager
        
        Args:
            storage_path: Đường dẫn thư mục lưu session data (default: /app/data/sessions)
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.counter_file = self.storage_path / "daily_counter.json"
        self.sessions_dir = self.storage_path / "sessions"
        self.sessions_dir.mkdir(exist_ok=True)
        self.metadata_file = self.storage_path / "metadata.json"
        
        # In-memory state (will be loaded from file)
        self.daily_counter = 0
        self.last_date = ""
        
        logger.info(f"📁 SessionPersistenceManager initialized at: {self.storage_path}")
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize storage directories and check files"""
        try:
            if not self.counter_file.exists():
                logger.info("🆕 Creating new daily_counter.json")
                self._save_counter_to_file()
            else:
                self.load_counter_from_file()
                logger.info(f"✅ Loaded counter: {self.daily_counter} for date: {self.last_date}")
        except Exception as e:
            logger.error(f"❌ Error initializing storage: {e}")
            self.daily_counter = 0
            self.last_date = ""
    
    def load_counter_from_file(self) -> Dict[str, Any]:
        """
        Load counter từ file
        
        Returns:
            Dict với keys: counter, date, last_saved
        """
        try:
            if self.counter_file.exists():
                with open(self.counter_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.daily_counter = data.get("counter", 0)
                    self.last_date = data.get("date", "")
                    logger.info(f"📖 Loaded counter from file: {self.daily_counter} ({self.last_date})")
                    return data
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error reading daily_counter.json: {e}")
            self.daily_counter = 0
            self.last_date = ""
        except Exception as e:
            logger.error(f"❌ Unexpected error loading counter: {e}")
            self.daily_counter = 0
            self.last_date = ""
        
        return {"counter": 0, "date": "", "last_saved": None}
    
    def _save_counter_to_file(self):
        """Save counter vào file (internal method)"""
        try:
            counter_data = {
                "counter": self.daily_counter,
                "date": self.last_date,
                "last_saved": datetime.now().isoformat(),
                "note": "Persistent daily session counter"
            }
            with open(self.counter_file, 'w', encoding='utf-8') as f:
                json.dump(counter_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Error saving counter to file: {e}")
    
    def get_next_session_id(self) -> str:
        """
        Lấy session ID tiếp theo và tự động increment counter
        
        Returns:
            Session ID theo format: YYYYMMDD-XXX (e.g., 20251019-001)
        """
        today = datetime.now().strftime("%Y%m%d")
        
        # Check if date changed (new day) - reset counter
        if today != self.last_date:
            self.daily_counter = 0
            self.last_date = today
            logger.info(f"🆕 New day detected: {today}. Counter reset to 0")
        
        # Increment counter
        self.daily_counter += 1
        
        # Save to file immediately
        self._save_counter_to_file()
        
        session_id = f"{today}-{self.daily_counter:03d}"
        logger.info(f"📌 Generated session ID: {session_id} (counter: {self.daily_counter})")
        
        return session_id
    
    def persist_session(self, session_id: str, session_data: Any) -> bool:
        """
        Persist individual session data to JSON file
        
        Args:
            session_id: Session ID (e.g., 20251019-001)
            session_data: Session object (dataclass) or dict
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert dataclass to dict if needed
            if is_dataclass(session_data) and not isinstance(session_data, type):
                session_dict = asdict(session_data)
            else:
                session_dict = session_data if isinstance(session_data, dict) else {}
            
            # Convert any complex types to serializable formats
            session_dict = self._make_serializable(session_dict)
            
            session_file = self.sessions_dir / f"{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_dict, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"💾 Persisted session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error persisting session {session_id}: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session data from file
        
        Args:
            session_id: Session ID to load
            
        Returns:
            Session data dict or None if not found
        """
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"❌ Error loading session {session_id}: {e}")
        
        return None
    
    def update_session_timestamp(self, session_id: str) -> bool:
        """
        Update session's last_accessed timestamp
        
        Args:
            session_id: Session ID to update
            
        Returns:
            True if successful
        """
        try:
            session_data = self.load_session(session_id)
            if session_data:
                session_data["last_accessed"] = datetime.now().timestamp()
                return self.persist_session(session_id, session_data)
        except Exception as e:
            logger.error(f"❌ Error updating session timestamp: {e}")
        
        return False
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Cleanup old sessions từ {days} ngày trước
        
        Args:
            days: Số ngày cần giữ lại (default: 30 days)
            
        Returns:
            Số sessions được xóa
        """
        try:
            cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()
            deleted_count = 0
            
            for session_file in self.sessions_dir.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        last_accessed = session_data.get("last_accessed", 0)
                        
                        if last_accessed < cutoff_time:
                            session_file.unlink()
                            deleted_count += 1
                            logger.debug(f"🗑️ Deleted old session: {session_file.name}")
                
                except Exception as e:
                    logger.error(f"❌ Error processing {session_file.name}: {e}")
            
            if deleted_count > 0:
                logger.info(f"🧹 Cleanup completed: {deleted_count} old sessions removed")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error in cleanup_old_sessions: {e}")
            return 0
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session storage statistics
        
        Returns:
            Stats về sessions được lưu trữ
        """
        try:
            session_files = list(self.sessions_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in session_files)
            
            return {
                "total_persisted_sessions": len(session_files),
                "storage_size_bytes": total_size,
                "storage_size_mb": round(total_size / 1024 / 1024, 2),
                "current_counter": self.daily_counter,
                "current_date": self.last_date,
                "storage_path": str(self.storage_path)
            }
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {}
    
    def _make_serializable(self, obj: Any) -> Any:
        """Convert non-serializable objects to serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        else:
            # For other types, convert to string
            return str(obj)
    
    def export_all_sessions(self, export_path: str) -> bool:
        """
        Export tất cả sessions thành 1 backup file
        
        Args:
            export_path: Đường dẫn file backup
            
        Returns:
            True if successful
        """
        try:
            all_sessions = {}
            for session_file in self.sessions_dir.glob("*.json"):
                session_id = session_file.stem
                with open(session_file, 'r', encoding='utf-8') as f:
                    all_sessions[session_id] = json.load(f)
            
            backup_data = {
                "exported_at": datetime.now().isoformat(),
                "total_sessions": len(all_sessions),
                "sessions": all_sessions
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Exported {len(all_sessions)} sessions to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error exporting sessions: {e}")
            return False
