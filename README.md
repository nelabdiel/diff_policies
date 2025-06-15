# Policy Analysis Platform

> **Prerequisites**: This application requires [Ollama](https://ollama.com/) to be installed and running for AI-powered analysis features.

An advanced document comparison tool that leverages semantic analysis and AI to help identify changes between policy documents, government memos, and other official documents.

## Features

- **Document Upload & Processing**: Support for PDF, TXT, and HTML documents
- **Semantic Document Comparison**: Advanced algorithms to match and compare document sections
- **AI-Powered Analysis**: LLM integration for intelligent change detection and summarization
- **Structured Data Extraction**: Automatically extract definitions, requirements, actions, and deadlines
- **Visual Diff Generation**: HTML-based diff views for easy change identification
- **Change Impact Classification**: Categorize changes by impact level and type
- **Fallback Mechanisms**: Robust error handling with simplified analysis when AI services are unavailable

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLAlchemy with SQLite
- **Document Processing**: PyPDF2, pdfplumber, BeautifulSoup4
- **AI/ML**: Ollama for local LLM analysis
- **Semantic Matching**: Sentence transformers and scikit-learn for document similarity
- **Frontend**: Bootstrap 5 with vanilla JavaScript

## Installation

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/) installed and running

### Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**
   ```bash
   python main.py
   ```

   Or using Gunicorn for production:
   ```bash
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```

## Usage

### Uploading Documents

1. Navigate to the home page
2. Click "Choose File" and select a PDF, TXT, or HTML document
3. Enter a descriptive title for the document
4. Click "Upload Document"

### Comparing Documents

1. Upload at least two documents
2. Navigate to the "Compare Documents" page
3. Select two documents from the dropdown menus
4. Click "Compare Documents"
5. Review the detailed comparison results, including:
   - Section-by-section changes
   - Added/removed content
   - Modified sections with detailed analysis
   - Overall summary of changes

### Understanding Results

The comparison results include:

- **Matched Sections**: Sections that exist in both documents with similarity analysis
- **Added Sections**: Content that appears only in the newer document
- **Removed Sections**: Content that was present in the original but removed
- **Change Statistics**: Quantitative analysis of document changes
- **Impact Classification**: AI-powered categorization of change significance

## Configuration

### Database Configuration

The application uses SQLite and automatically creates `instance/diffpolicy.db`

### File Upload Limits

- Maximum file size: 16MB
- Supported formats: PDF, TXT, HTML, HTM
- Files are stored in the `uploads/` directory

### AI Integration

The platform uses Ollama for AI-powered document analysis and includes fallback mechanisms when services are unavailable.

## API Endpoints

- `GET /` - Main upload page
- `POST /upload` - Document upload handler
- `GET /compare` - Document comparison form
- `POST /compare` - Process document comparison
- `GET /document/<id>` - View individual document
- `POST /analyze_section` - API endpoint for section analysis

## Project Structure

```
├── app.py                    # Flask application factory
├── main.py                   # Application entry point
├── models.py                 # Database models
├── routes.py                 # URL routes and handlers
├── document_processor.py     # Document parsing and extraction
├── semantic_matcher.py       # Section matching algorithms
├── diff_generator.py         # Comparison result generation
├── llm_analyzer.py          # LLM integration for analysis
├── simple_analyzer.py       # Fallback analysis without LLM
├── structured_parser.py     # Structured data extraction
├── templates/               # HTML templates
├── static/                  # CSS and JavaScript files
├── uploads/                 # Uploaded document storage
└── instance/                # Database and instance files
```

## Development

### Running in Development Mode

```bash
export FLASK_ENV=development
python main.py
```

### Adding New Document Types

To support additional document formats:

1. Update `ALLOWED_EXTENSIONS` in `routes.py`
2. Add processing logic in `document_processor.py`
3. Update the upload form validation in templates

### Extending AI Analysis

To add new analysis features:

1. Extend the `LLMAnalyzer` class in `llm_analyzer.py`
2. Update the fallback logic in `simple_analyzer.py`
3. Modify the comparison results structure in `diff_generator.py`

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed via `pip install -r requirements.txt`
2. **Database Errors**: Check database permissions and connection string
3. **File Upload Errors**: Verify the `uploads/` directory exists and is writable
4. **Memory Issues**: Large documents may require increased memory allocation

### Performance Optimization

- For large documents, consider implementing pagination
- Use database indexing for frequently queried fields
- Cache semantic embeddings for repeated comparisons
- Consider using a message queue for long-running analysis tasks

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with appropriate tests
4. Submit a pull request with a clear description