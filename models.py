from app import db
from datetime import datetime

class PolicyDocument(db.Model):
    __tablename__ = 'policy_document'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # pdf, text, html
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    file_size = db.Column(db.Integer)
    
    # Structured document data
    structured_data = db.Column(db.JSON)  # Stores parsed definitions, requirements, actions, deadlines
    summary = db.Column(db.Text)  # Document summary
    
    def __init__(self, title, filename, content, document_type, file_size=None, structured_data=None, summary=None):
        self.title = title
        self.filename = filename
        self.content = content
        self.document_type = document_type
        self.file_size = file_size
        self.structured_data = structured_data
        self.summary = summary
    
    def __repr__(self):
        return f'<PolicyDocument {self.title}>'

class DocumentComparison(db.Model):
    __tablename__ = 'document_comparison'
    
    id = db.Column(db.Integer, primary_key=True)
    doc1_id = db.Column(db.Integer, db.ForeignKey('policy_document.id'), nullable=False)
    doc2_id = db.Column(db.Integer, db.ForeignKey('policy_document.id'), nullable=False)
    comparison_result = db.Column(db.JSON)  # Store the diff results
    structured_comparison = db.Column(db.JSON)  # Store structured element comparison
    summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    doc1 = db.relationship('PolicyDocument', foreign_keys=[doc1_id], backref='comparisons_as_doc1')
    doc2 = db.relationship('PolicyDocument', foreign_keys=[doc2_id], backref='comparisons_as_doc2')
    
    def __init__(self, doc1_id, doc2_id, comparison_result=None, structured_comparison=None, summary=None):
        self.doc1_id = doc1_id
        self.doc2_id = doc2_id
        self.comparison_result = comparison_result
        self.structured_comparison = structured_comparison
        self.summary = summary
    
    def __repr__(self):
        return f'<DocumentComparison {self.id}>'
