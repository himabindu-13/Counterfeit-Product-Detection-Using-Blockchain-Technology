// This file contains JavaScript code for client-side functionality, such as form validation and AJAX requests.

document.addEventListener('DOMContentLoaded', function() {
    // Example: Form validation for login and registration
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            if (!username || !password) {
                event.preventDefault();
                alert('Please fill in all fields.');
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const role = document.getElementById('role').value;

            if (!username || !password || !role) {
                event.preventDefault();
                alert('Please fill in all fields.');
            }
        });
    }

    // Example: AJAX request to purchase a product
    const purchaseButtons = document.querySelectorAll('.purchase-button');
    purchaseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.productId;

            fetch('/api/purchase_product', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ product_id: productId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Product purchased successfully!');
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
});