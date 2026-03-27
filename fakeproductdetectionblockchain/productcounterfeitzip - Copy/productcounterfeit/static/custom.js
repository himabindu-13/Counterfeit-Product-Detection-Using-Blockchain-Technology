function verifyProduct() {
    const qrInput = document.getElementById('qrInput');
    const resultDiv = document.getElementById('result');
    
    if (!qrInput.value) {
        alert('Please enter a QR code');
        return;
    }
    
    fetch('/scan_qr', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ qr_data: qrInput.value })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const product = data.product;
            resultDiv.innerHTML = `
                <div class="product-info">
                    <h4 class="neon-text">✅ Product Verified</h4>
                    <div class="row">
                        <div class="col-md-6">
                            <strong>Product Name:</strong> ${product.name}<br>
                            <strong>Description:</strong> ${product.description}<br>
                            <strong>Manufacturer:</strong> ${product.manufacturer}<br>
                        </div>
                        <div class="col-md-6">
                            <strong>Batch Number:</strong> ${product.batch_number}<br>
                            <strong>Manufacturing Date:</strong> ${product.manufacturing_date}<br>
                            <strong>Expiry Date:</strong> ${product.expiry_date}<br>
                        </div>
                    </div>
                    <div class="mt-3">
                        <span class="${product.blockchain_verified ? 'verified-badge' : 'not-verified-badge'}">
                            ${product.blockchain_verified ? '✓ Blockchain Verified' : '✗ Not on Blockchain'}
                        </span>
                    </div>
                    ${product.signature_present !== undefined ? `
                    <div class="mt-2">
                        <span class="${product.signature_present && product.signature_valid ? 'verified-badge' : 'not-verified-badge'}">
                            ${product.signature_present ? (product.signature_valid ? '✓ Digitally Verified' : '✗ Digital Signature Invalid') : 'No Digital Signature'}
                        </span>
                        ${product.signer_address ? `<div><small>Signed by address: ${product.signer_address}</small></div>` : ''}
                        ${product.signature_present && product.signature_valid ? `
                        <div class="mt-2">
                            <small>
                                This QR encodes a cryptographic signature of the product identifier. We verify it on-device by recovering the signer address from the signature and checking it matches our official signing key. A valid signature means the QR data hasn't been tampered with and was issued by us.
                            </small>
                        </div>
                        ` : ''}
                        ${product.signature_present && !product.signature_valid ? `
                        <div class="mt-2">
                            <small>
                                The embedded cryptographic signature does not match our official signing key. This QR may be altered or counterfeit.
                            </small>
                        </div>
                        ` : ''}
                        ${!product.signature_present ? `
                        <div class="mt-2">
                            <small>
                                This is a legacy QR without a digital signature. Verification uses database/blockchain records only.
                            </small>
                        </div>
                        ` : ''}
                    </div>
                    ` : ''}
                    ${product.blockchain_tx_hash ? `
                    <div class="mt-2">
                        <small>TX Hash: ${product.blockchain_tx_hash}</small>
                    </div>
                    ` : ''}
                </div>
            `;
        } else {
            resultDiv.innerHTML = `
                <div class="product-info" style="border-left-color: #ff00ff;">
                    <h4 class="text-magenta">❌ Product Not Found</h4>
                    <p>This product may be counterfeit or not registered in our system.</p>
                    <p><strong>Warning:</strong> Do not use this product.</p>
                </div>
            `;
        }
        resultDiv.style.display = 'block';
    })
    .catch(error => {
        console.error('Error:', error);
        resultDiv.innerHTML = `
            <div class="product-info" style="border-left-color: #ff0000;">
                <h4>⚠️ Verification Error</h4>
                <p>There was an error verifying the product. Please try again.</p>
            </div>
        `;
        resultDiv.style.display = 'block';
    });
}

// Simulate QR scanner (for demo purposes)
function simulateQRScan() {
    const demoQRs = [
        'demo_qr_hash_1',
        'demo_qr_hash_2',
        'demo_qr_hash_3'
    ];
    const randomQR = demoQRs[Math.floor(Math.random() * demoQRs.length)];
    document.getElementById('qrInput').value = randomQR;
}