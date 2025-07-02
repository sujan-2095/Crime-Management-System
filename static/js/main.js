// Main JavaScript for Crime Record Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Confirm deletion for delete buttons
    const confirmDelete = document.querySelectorAll('.confirm-delete');
    confirmDelete.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Enable form auto-save to localStorage (except for sensitive forms)
    const nonSensitiveForms = document.querySelectorAll('form:not(.sensitive-data)');
    nonSensitiveForms.forEach(function(form) {
        const formId = form.id || form.getAttribute('action');
        if (formId) {
            // Restore form data
            const savedData = localStorage.getItem('formData-' + formId);
            if (savedData) {
                const formData = JSON.parse(savedData);
                Object.keys(formData).forEach(function(key) {
                    const input = form.querySelector('[name="' + key + '"]');
                    if (input && input.type !== 'password') {
                        input.value = formData[key];
                    }
                });
            }
            
            // Save form data on input change
            form.querySelectorAll('input, textarea, select').forEach(function(input) {
                if (input.type !== 'password' && input.type !== 'hidden' && input.name) {
                    input.addEventListener('change', function() {
                        let data = localStorage.getItem('formData-' + formId) || '{}';
                        data = JSON.parse(data);
                        data[input.name] = input.value;
                        localStorage.setItem('formData-' + formId, JSON.stringify(data));
                    });
                }
            });
            
            // Clear saved data on submit
            form.addEventListener('submit', function() {
                localStorage.removeItem('formData-' + formId);
            });
        }
    });

    // Add confirm prompt to status changing select elements
    const statusSelects = document.querySelectorAll('select[name="status"]');
    statusSelects.forEach(function(select) {
        const originalValue = select.value;
        select.addEventListener('change', function() {
            if (
                (originalValue === 'Active' && select.value === 'Completed') ||
                (originalValue === 'Open' && select.value === 'Closed') ||
                (originalValue === 'Pending' && select.value === 'Closed')
            ) {
                if (!confirm('Changing the status to ' + select.value + ' may trigger automatic updates to related records. Continue?')) {
                    select.value = originalValue;
                }
            }
        });
    });

    // Format datetime-local inputs with current datetime
    const datetimeInputs = document.querySelectorAll('input[type="datetime-local"]');
    datetimeInputs.forEach(function(input) {
        if (!input.value) {
            const now = new Date();
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            
            input.value = `${year}-${month}-${day}T${hours}:${minutes}`;
        }
    });

    // Initialize custom file input displays
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name || 'No file chosen';
            const fileLabel = input.nextElementSibling;
            if (fileLabel && fileLabel.classList.contains('custom-file-label')) {
                fileLabel.textContent = fileName;
            }
        });
    });

    // Enable sticky header for large tables
    const largeTables = document.querySelectorAll('.table-responsive table');
    largeTables.forEach(function(table) {
        if (table.rows.length > 10) {
            const header = table.querySelector('thead');
            if (header) {
                header.classList.add('sticky-top', 'bg-dark');
            }
        }
    });
});
