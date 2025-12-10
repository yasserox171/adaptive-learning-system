// Main JavaScript file for adaptive learning system

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Handle exercise submissions
    const exerciseForms = document.querySelectorAll('.exercise-form');
    exerciseForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const exerciseId = this.dataset.exerciseId;
            
            fetch(`/api/exercise/${exerciseId}`, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.correct) {
                    showAlert('success', 'إجابة صحيحة!');
                } else {
                    showAlert('danger', 'إجابة خاطئة، حاول مرة أخرى');
                }
            });
        });
    });

    // Update progress bar
    function updateProgress() {
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            const width = progressBar.style.width;
            // Here you would typically fetch actual progress from the server
            console.log('Current progress:', width);
        }
    }

    // Alert helper function
    function showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Initialize any page-specific functionality
    initPageSpecific();
});

function initPageSpecific() {
    const body = document.body;
    
    // Dashboard page
    if (body.classList.contains('dashboard-page')) {
        console.log('Dashboard page initialized');
        // Add dashboard-specific functionality here
    }
    
    // Lesson page
    if (body.classList.contains('lesson-page')) {
        console.log('Lesson page initialized');
        // Add lesson-specific functionality here
    }
    
    // Section page
    if (body.classList.contains('section-page')) {
        console.log('Section page initialized');
        // Section page functionality is handled in the template
    }
}

// Utility function to format dates
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    const date = new Date(dateString);
    return date.toLocaleDateString('ar-EG', options);
}

// Utility function to handle API errors
function handleApiError(error) {
    console.error('API Error:', error);
    showAlert('danger', 'حدث خطأ في الاتصال بالخادم. يرجى المحاولة مرة أخرى.');
}

// Export for use in browser console if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatDate,
        handleApiError
    };
}

// دالة لحذف العناصر
function deleteItem(url, itemId, itemName) {
    if (confirm(`هل أنت متأكد من حذف ${itemName}؟`)) {
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('success', data.message);
                setTimeout(() => location.reload(), 1500);
            } else {
                showAlert('danger', data.message);
            }
        })
        .catch(error => {
            showAlert('danger', 'حدث خطأ أثناء الحذف');
        });
    }
}

// دالة لعرض التنبيهات
function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// إضافة أزرار Bootstrap Icons
if (!document.querySelector('link[href*="bootstrap-icons"]')) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css';
    document.head.appendChild(link);
}