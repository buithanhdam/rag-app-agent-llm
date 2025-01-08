import os
from typing import List, Dict, Optional, Union
from pathlib import Path
import tempfile
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableFormerMode,
    AcceleratorOptions
)
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.utils.export import generate_multimodal_pages

class DoclingReader:
    """A document reader class that uses Docling to process various document formats."""
    
    def __init__(
        self,
        num_threads: int = 4,
        image_resolution_scale: float = 2.0,
        enable_ocr: bool = True,
        enable_tables: bool = True
    ):
        """
        Initialize the DoclingReader with custom settings.
        
        Args:
            num_threads: Number of CPU threads to use
            image_resolution_scale: Scale factor for image resolution
            enable_ocr: Whether to enable OCR processing
            enable_tables: Whether to enable table detection
        """
        os.environ['OMP_NUM_THREADS'] = str(num_threads)
        self.image_resolution_scale = image_resolution_scale
        self.converter = self._initialize_converter(
            enable_ocr=enable_ocr,
            enable_tables=enable_tables,
            num_threads=num_threads
        )
    
    def _initialize_converter(
        self,
        enable_ocr: bool,
        enable_tables: bool,
        num_threads: int
    ) -> DocumentConverter:
        """Initialize the document converter with specified settings."""
        pipeline_options = PdfPipelineOptions()
        
        # Configure OCR and table detection
        pipeline_options.do_ocr = enable_ocr
        pipeline_options.do_table_structure = enable_tables
        if enable_tables:
            pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
            pipeline_options.table_structure_options.do_cell_matching = False
        
        # Configure processing options
        pipeline_options.accelerator_options = AcceleratorOptions(num_threads=num_threads)
        pipeline_options.images_scale = self.image_resolution_scale
        pipeline_options.generate_page_images = True
        
        return DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=PyPdfiumDocumentBackend
                )
            }
        )
    
    def process_file(
        self,
        file_path: Union[str, Path],
        max_pages: int = 100,
        max_file_size: int = 20971520  # 20MB
    ) -> Dict:
        """
        Process a document file and extract its content.
        
        Args:
            file_path: Path to the document file
            max_pages: Maximum number of pages to process
            max_file_size: Maximum file size in bytes
            
        Returns:
            Dict containing processed document information including:
            - markdown_content: Extracted text in markdown format
            - pages: List of dictionaries containing per-page information
            - metadata: Document metadata
        """
        file_path = Path(file_path)
        
        try:
            # Convert the document
            result = self.converter.convert(
                str(file_path),
                max_num_pages=max_pages,
                max_file_size=max_file_size
            )
            
            # Extract markdown content
            markdown_content = result.document.export_to_markdown()
            
            # Process pages and extract multimodal content
            pages = []
            for content in generate_multimodal_pages(result):
                text_content, markdown_content, content_dt, page_cells, page_segments, page = content
                
                page_info = {
                    "page_number": page.page_no,
                    "text_content": text_content,
                    "markdown_content": markdown_content,
                    "tables": page_cells,
                    "segments": page_segments,
                    "metadata": {
                        "width": getattr(page, 'width', 0),
                        "height": getattr(page, 'height', 0),
                        "dpi": getattr(page, '_default_image_scale', 1.0) * 72
                    }
                }
                pages.append(page_info)
            
            return {
                "markdown_content": markdown_content,
                "pages": pages,
                "metadata": {
                    "file_name": file_path.name,
                    "file_size": file_path.stat().st_size,
                    "num_pages": len(pages)
                }
            }
            
        except Exception as e:
            raise Exception(f"Error processing document: {str(e)}")
    
    def process_bytes(
        self,
        file_bytes: bytes,
        file_extension: str,
        max_pages: int = 100,
        max_file_size: int = 20971520
    ) -> Dict:
        """
        Process a document from bytes data.
        
        Args:
            file_bytes: Document content as bytes
            file_extension: File extension (e.g., '.pdf', '.docx')
            max_pages: Maximum number of pages to process
            max_file_size: Maximum file size in bytes
            
        Returns:
            Dict containing processed document information
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name
            
        try:
            return self.process_file(tmp_path, max_pages, max_file_size)
        finally:
            os.unlink(tmp_path)