// Crafts Live Preview Javascript

document.addEventListener('DOMContentLoaded', function() {
    // Select form inputs
    const nameInput = document.getElementById('id_name');
    const priceInput = document.getElementById('id_price');
    const categorySelect = document.getElementById('id_category');
    const descInput = document.getElementById('id_description');
    const imageInput = document.getElementById('id_image');
    const statusToggle = document.getElementById('status-toggle');

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
    if (statusToggle) {
        statusToggle.addEventListener('change', function() {
            const isPublished = this.checked;
            if (prevStatus) {
                prevStatus.textContent = isPublished ? 'PUBLISHED' : 'DRAFT';
                if (isPublished) {
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

    // Select rating & review_count inputs & preview spans
    const ratingInput = document.getElementById('id_rating');
    const reviewCountInput = document.getElementById('id_review_count');
    const prevStars = document.getElementById('preview-stars');
    const prevReviewsCount = document.getElementById('preview-reviews-count');

    // Update rating stars
    if (ratingInput && prevStars) {
        ratingInput.addEventListener('input', function() {
            const val = parseFloat(this.value);
            if (isNaN(val) || val < 0) return;
            const fullStars = Math.min(5, Math.max(0, Math.floor(val)));
            const halfStar = (val - fullStars) >= 0.25 && fullStars < 5 ? 1 : 0;
            const emptyStars = Math.max(0, 5 - fullStars - halfStar);
            
            let html = '';
            for (let i = 0; i < fullStars; i++) {
                html += '<i class="bi bi-star-fill"></i>';
            }
            if (halfStar) {
                html += '<i class="bi bi-star-half"></i>';
            }
            for (let i = 0; i < emptyStars; i++) {
                html += '<i class="bi bi-star"></i>';
            }
            prevStars.innerHTML = html;
        });
    }

    // Update reviews count
    if (reviewCountInput && prevReviewsCount) {
        reviewCountInput.addEventListener('input', function() {
            const val = parseInt(this.value);
            if (!isNaN(val) && val >= 0) {
                prevReviewsCount.textContent = `(${val})`;
            } else {
                prevReviewsCount.textContent = '(0)';
            }
        });
    }
});
