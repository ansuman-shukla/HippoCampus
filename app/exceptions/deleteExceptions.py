import logging
from typing import Optional
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentSaveError(Exception):
    def __init__(self, message: str, user_id: Optional[str] = None, doc_id: Optional[str] = None):
        super().__init__(message)
        self.user_id = user_id
        self.doc_id = doc_id    

        