// Crafts Live Preview Javascript

document.addEventListener('DOMContentLoaded', function() {
    // Select form inputs
    const nameInput = document.getElementById('id_name');
    const priceInput = document.getElementById('id_price');
    const categorySelect = document.getElementById('id_category');
    const descInput = document.getElementById('id_description');
    const imageInput = document.getElementById('id_image');
    const statusSelect = document.getElementById('id_status');

    // Select preview placeholders
    const prevName = document.getElementById('preview-name');
    const prevPrice = document.getElementById('preview-price');
    const prevCategory = document.getElementById('preview-category');
    const prevDesc = document.getElementById('preview-description');
    const prevImage = document.getElementById('preview-image');
    const prevStatus = document.getElementById('preview-status-badge');
    const prevStatusDot = document.getElementById('preview-status-dot');

    if (!prevName) return; // Not on form page with preview

    // Update name
    if (nameInput) {
        nameInput.addEventListener('input', function() {
            prevName.textContent = this.value.trim() || 'Product Name Placeholder';
        });
    }

    // Update price
    if (priceInput) {
        priceInput.addEventListener('input', function() {
            const val = parseFloat(this.value);
            const isRTL = document.documentElement.getAttribute('dir') === 'rtl';
            const currency = isRTL ? ' ج.م' : ' EGP';
            if (!isNaN(val)) {
                prevPrice.textContent = isRTL ? val.toFixed(2) + currency : currency + ' ' + val.toFixed(2);
            } else {
                prevPrice.textContent = isRTL ? '0.00' + currency : currency + ' 0.00';
            }
        });
    }

    // Update category
    if (categorySelect) {
        categorySelect.addEventListener('change', function() {
            const selectedText = this.options[this.selectedIndex].text;
            if (prevCategory) {
                prevCategory.textContent = this.value ? selectedText : 'Category';
            }
        });
    }

    // Update description
    if (descInput) {
        descInput.addEventListener('input', function() {
            if (prevDesc) {
                prevDesc.textContent = this.value.trim() || 'No description provided yet.';
            }
        });
    }

    // Update status badge
    if (statusSelect) {
        statusSelect.addEventListener('change', function() {
            const status = this.value;
            if (prevStatus) {
                prevStatus.textContent = status;
                if (status === 'PUBLISHED') {
                    prevStatus.className = 'badge bg-success text-white';
                    if (prevStatusDot) prevStatusDot.className = 'status-dot bg-success';
                } else {
                    prevStatus.className = 'badge bg-secondary text-white';
                    if (prevStatusDot) prevStatusDot.className = 'status-dot bg-secondary';
                }
            }
        });
    }

    // Update image preview using FileReader
    if (imageInput) {
        imageInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    prevImage.src = e.target.result;
                };
                reader.readAsDataURL(file);
            } else {
                // If file is cleared, revert to fallback placeholder
                if (prevImage.dataset.originalSrc) {
                    prevImage.src = prevImage.dataset.originalSrc;
                } else {
                    prevImage.src = 'https://images.unsplash.com/photo-1513519245088-0e12902e5a38?q=80&w=600&auto=format&fit=crop';
                }
            }
        });
    }
});
