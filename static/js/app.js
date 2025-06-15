// Main application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });
    
    // File upload preview
    const fileInput = document.getElementById('document');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const fileSize = file.size;
                const fileName = file.name;
                const fileType = file.type;
                
                // Show file info
                let fileInfo = document.querySelector('.file-info');
                if (!fileInfo) {
                    fileInfo = document.createElement('div');
                    fileInfo.className = 'file-info mt-2';
                    fileInput.parentNode.appendChild(fileInfo);
                }
                
                let sizeText;
                if (fileSize > 1024 * 1024) {
                    sizeText = (fileSize / (1024 * 1024)).toFixed(1) + ' MB';
                } else if (fileSize > 1024) {
                    sizeText = (fileSize / 1024).toFixed(1) + ' KB';
                } else {
                    sizeText = fileSize + ' bytes';
                }
                
                fileInfo.innerHTML = `
                    <div class="card border-success">
                        <div class="card-body py-2">
                            <small class="text-success">
                                <i class="fas fa-file me-1"></i>
                                <strong>${fileName}</strong> (${sizeText})
                            </small>
                        </div>
                    </div>
                `;
                
                // Check file size
                if (fileSize > 16 * 1024 * 1024) {
                    fileInfo.innerHTML = `
                        <div class="alert alert-danger py-2 mb-0">
                            <small>
                                <i class="fas fa-exclamation-triangle me-1"></i>
                                File too large. Maximum size is 16MB.
                            </small>
                        </div>
                    `;
                }
            }
        });
    }
    
    // Document comparison form validation
    const compareForm = document.querySelector('form[action*="compare"]');
    if (compareForm) {
        const doc1Select = document.getElementById('document1');
        const doc2Select = document.getElementById('document2');
        
        if (doc1Select && doc2Select) {
            // Update doc2 options when doc1 changes
            doc1Select.addEventListener('change', function() {
                const selectedValue = this.value;
                const doc2Options = doc2Select.querySelectorAll('option');
                
                doc2Options.forEach(function(option) {
                    if (option.value === selectedValue && option.value !== '') {
                        option.style.display = 'none';
                        option.disabled = true;
                    } else {
                        option.style.display = 'block';
                        option.disabled = false;
                    }
                });
                
                // Reset doc2 if it's the same as doc1
                if (doc2Select.value === selectedValue) {
                    doc2Select.value = '';
                }
            });
            
            // Update doc1 options when doc2 changes
            doc2Select.addEventListener('change', function() {
                const selectedValue = this.value;
                const doc1Options = doc1Select.querySelectorAll('option');
                
                doc1Options.forEach(function(option) {
                    if (option.value === selectedValue && option.value !== '') {
                        option.style.display = 'none';
                        option.disabled = true;
                    } else {
                        option.style.display = 'block';
                        option.disabled = false;
                    }
                });
                
                // Reset doc1 if it's the same as doc2
                if (doc1Select.value === selectedValue) {
                    doc1Select.value = '';
                }
            });
        }
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Section analysis API integration
    const analyzeButtons = document.querySelectorAll('.analyze-section-btn');
    analyzeButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const sectionId = this.dataset.sectionId;
            const oldText = this.dataset.oldText;
            const newText = this.dataset.newText;
            
            // Show loading state
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="loading-spinner"></span> Analyzing...';
            this.disabled = true;
            
            // Make API call
            fetch('/api/analyze_section', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    old_text: oldText,
                    new_text: newText
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.analysis) {
                    // Show analysis result
                    const resultDiv = document.getElementById(`analysis-${sectionId}`);
                    if (resultDiv) {
                        resultDiv.innerHTML = `
                            <div class="alert alert-info">
                                <strong>AI Analysis:</strong> ${data.analysis}
                            </div>
                        `;
                    }
                } else {
                    console.error('Analysis failed:', data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            })
            .finally(() => {
                // Restore button
                this.innerHTML = originalText;
                this.disabled = false;
            });
        });
    });
    
    // Export functionality
    const exportBtn = document.getElementById('export-comparison');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            const comparisonData = {
                document1: document.querySelector('[data-doc1-title]')?.dataset.doc1Title,
                document2: document.querySelector('[data-doc2-title]')?.dataset.doc2Title,
                sections: []
            };
            
            // Collect section data
            document.querySelectorAll('.section-card').forEach(function(card) {
                const changeType = card.dataset.changeType;
                const title = card.querySelector('.card-title').textContent.trim();
                const summary = card.querySelector('.summary-text')?.textContent.trim();
                
                comparisonData.sections.push({
                    title: title,
                    changeType: changeType,
                    summary: summary
                });
            });
            
            // Create and download JSON file
            const dataStr = JSON.stringify(comparisonData, null, 2);
            const dataBlob = new Blob([dataStr], {type: 'application/json'});
            
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `policy-comparison-${Date.now()}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        });
    }
    
    // Print functionality
    const printBtn = document.getElementById('print-comparison');
    if (printBtn) {
        printBtn.addEventListener('click', function() {
            window.print();
        });
    }
});

// Utility function to format file sizes
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Utility function to escape HTML
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Show loading overlay
function showLoading(message = 'Processing...') {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
    overlay.style.backgroundColor = 'rgba(0,0,0,0.7)';
    overlay.style.zIndex = '9999';
    
    overlay.innerHTML = `
        <div class="text-center text-white">
            <div class="loading-spinner mb-3" style="width: 3rem; height: 3rem;"></div>
            <h5>${message}</h5>
        </div>
    `;
    
    document.body.appendChild(overlay);
}

// Hide loading overlay
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}
