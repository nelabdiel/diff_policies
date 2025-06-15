import os
import logging
from flask import render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from app import app, db
from models import PolicyDocument, DocumentComparison
from document_processor import DocumentProcessor
from semantic_matcher import SemanticMatcher
try:
    from llm_analyzer import LLMAnalyzer
except ImportError:
    from simple_analyzer import SimpleLLMAnalyzer as LLMAnalyzer
from diff_generator import DiffGenerator
from structured_parser import StructuredDocumentParser

# Configure allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'html', 'htm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page for uploading documents"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_document():
    """Handle document uploads"""
    try:
        if 'document' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('index'))
        
        file = request.files['document']
        title = request.form.get('title', '')
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('index'))
        
        if not allowed_file(file.filename):
            flash('File type not supported. Please upload PDF, TXT, or HTML files.', 'error')
            return redirect(url_for('index'))
        
        # Secure the filename and save the file
        filename = secure_filename(file.filename or 'document.txt')
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Process the document
        processor = DocumentProcessor()
        content, doc_type = processor.process_file(file_path)
        
        if not content:
            flash('Could not extract content from the file', 'error')
            os.remove(file_path)  # Clean up
            return redirect(url_for('index'))
        
        # Parse structured elements using LLM
        structured_parser = StructuredDocumentParser()
        structured_data = structured_parser.parse_document(content, title or filename)
        
        # Save to database
        document = PolicyDocument(
            title=title or filename,
            filename=filename,
            content=content,
            document_type=doc_type,
            file_size=os.path.getsize(file_path),
            structured_data=structured_data,
            summary=structured_data.get('summary', '')
        )
        
        db.session.add(document)
        db.session.commit()
        
        # Clean up uploaded file after processing
        os.remove(file_path)
        
        flash(f'Document "{document.title}" uploaded successfully!', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        logging.error(f"Error uploading document: {str(e)}")
        flash('An error occurred while uploading the document', 'error')
        return redirect(url_for('index'))

@app.route('/compare')
def compare_form():
    """Show comparison form"""
    documents = PolicyDocument.query.order_by(PolicyDocument.upload_time.desc()).all()
    return render_template('compare.html', documents=documents)

@app.route('/compare', methods=['POST'])
def compare_documents():
    """Compare two documents"""
    try:
        doc1_id = request.form.get('document1')
        doc2_id = request.form.get('document2')
        
        if not doc1_id or not doc2_id:
            flash('Please select two documents to compare', 'error')
            return redirect(url_for('compare_form'))
        
        if doc1_id == doc2_id:
            flash('Please select two different documents', 'error')
            return redirect(url_for('compare_form'))
        
        # Get documents from database
        doc1 = PolicyDocument.query.get_or_404(doc1_id)
        doc2 = PolicyDocument.query.get_or_404(doc2_id)
        
        # Check if comparison already exists
        existing_comparison = DocumentComparison.query.filter(
            ((DocumentComparison.doc1_id == doc1_id) & (DocumentComparison.doc2_id == doc2_id)) |
            ((DocumentComparison.doc1_id == doc2_id) & (DocumentComparison.doc2_id == doc1_id))
        ).first()
        
        if existing_comparison:
            comparison_result = existing_comparison.comparison_result
            structured_comparison = existing_comparison.structured_comparison
            summary = existing_comparison.summary
        else:
            # Check if documents have structured data, if not parse them
            if not doc1.structured_data:
                parser = StructuredDocumentParser()
                doc1.structured_data = parser.parse_document(doc1.content, doc1.title)
                doc1.summary = doc1.structured_data.get('summary', '')
                db.session.commit()
            
            if not doc2.structured_data:
                parser = StructuredDocumentParser()
                doc2.structured_data = parser.parse_document(doc2.content, doc2.title)
                doc2.summary = doc2.structured_data.get('summary', '')
                db.session.commit()
            
            # Perform traditional section-based comparison
            semantic_matcher = SemanticMatcher()
            diff_generator = DiffGenerator()
            
            sections1 = semantic_matcher.extract_sections(doc1.content)
            sections2 = semantic_matcher.extract_sections(doc2.content)
            matches = semantic_matcher.match_sections(sections1, sections2)
            
            comparison_result = diff_generator.generate_comparison(
                doc1.content, doc2.content, matches, sections1, sections2
            )
            
            # Perform structured comparison
            structured_parser = StructuredDocumentParser()
            structured_comparison = structured_parser.compare_structured_documents(
                doc1.structured_data, doc2.structured_data
            )
            
            # Generate enhanced summary
            llm_analyzer = LLMAnalyzer()
            summary = llm_analyzer.generate_overall_summary(comparison_result, doc1.title, doc2.title)
            
            # Save comparison to database
            new_comparison = DocumentComparison(
                doc1_id=doc1_id,
                doc2_id=doc2_id,
                comparison_result=comparison_result,
                structured_comparison=structured_comparison,
                summary=summary
            )
            db.session.add(new_comparison)
            db.session.commit()
        
        return render_template('compare.html', 
                             documents=PolicyDocument.query.all(),
                             comparison_result=comparison_result,
                             structured_comparison=structured_comparison,
                             summary=summary,
                             doc1=doc1,
                             doc2=doc2)
        
    except Exception as e:
        logging.error(f"Error comparing documents: {str(e)}")
        flash('An error occurred while comparing the documents', 'error')
        return redirect(url_for('compare_form'))

@app.route('/document/<int:doc_id>')
def view_document(doc_id):
    """View a single document"""
    document = PolicyDocument.query.get_or_404(doc_id)
    return render_template('document.html', document=document)

@app.route('/api/analyze_section', methods=['POST'])
def analyze_section():
    """API endpoint for analyzing a specific section change"""
    try:
        data = request.get_json()
        old_text = data.get('old_text', '')
        new_text = data.get('new_text', '')
        
        llm_analyzer = LLMAnalyzer()
        analysis = llm_analyzer.analyze_section_change(old_text, new_text)
        
        return jsonify({'analysis': analysis})
        
    except Exception as e:
        logging.error(f"Error analyzing section: {str(e)}")
        return jsonify({'error': 'Failed to analyze section'}), 500

@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum size is 16MB.', 'error')
    return redirect(url_for('index'))
