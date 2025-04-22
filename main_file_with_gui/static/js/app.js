function updateBill() {
    fetch('/api/current_bill')
        .then(response => response.json())
        .then(data => {
            // Update bill items table
            const billItemsBody = document.getElementById('bill-items-body');
            billItemsBody.innerHTML = '';
            
            if (data.items.length === 0) {
                const emptyRow = document.createElement('tr');
                emptyRow.innerHTML = '<td colspan="4" style="text-align: center;">No items detected</td>';
                billItemsBody.appendChild(emptyRow);
            } else {
                data.items.forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${item.name}</td>
                        <td>${item.quantity}</td>
                        <td>$${item.unit_price.toFixed(2)}</td>
                        <td>$${item.total.toFixed(2)}</td>
                    `;
                    billItemsBody.appendChild(row);
                });
            }
            
            // Update summary values
            document.getElementById('subtotal').textContent = `$${data.subtotal.toFixed(2)}`;
            document.getElementById('tax').textContent = `$${data.tax.toFixed(2)}`;
            document.getElementById('total').textContent = `$${data.total.toFixed(2)}`;
        })
        .catch(error => {
            console.error('Error fetching bill data:', error);
        });
}

// Generate receipt and view it
// Replace the generate-receipt handler in app.js
document.getElementById('generate-receipt').addEventListener('click', function() {
    // Show loading message
    showMessage('Generating receipt...', 'info');
    
    fetch('/generate_receipt')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage('Bill Generated Successfully!', 'success');
            } else {
                showMessage('Failed to generate bill.', 'error');
            }
        })
        .catch(error => {
            console.error('Error generating receipt:', error);
            showMessage('Error generating receipt.', 'error');
        });
});

// Reset the bill
document.getElementById('reset-bill').addEventListener('click', function() {
    fetch('/reset_bill')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage('Bill reset successfully!', 'success');
                updateBill(); // Update the bill display immediately
            } else {
                showMessage('Failed to reset bill.', 'error');
            }
        })
        .catch(error => {
            console.error('Error resetting bill:', error);
            showMessage('Error resetting bill.', 'error');
        });
});
// Add this to app.js
document.getElementById('stop-program').addEventListener('click', function() {
    if (confirm('Are you sure you want to terminate the program?')) {
        fetch('/terminate_program')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage('Program is terminating...', 'info');
                    setTimeout(() => {
                        window.close();
                    }, 2000);
                }
            })
            .catch(error => {
                console.error('Error terminating program:', error);
                showMessage('Error terminating program.', 'error');
            });
    }
});


// Show message function
function showMessage(text, type) {
    const messageElement = document.getElementById('message');
    messageElement.textContent = text;
    messageElement.className = type; // 'success', 'error', or 'info'
    
    // Show the message
    messageElement.classList.remove('hidden');
    
    // Hide the message after 3 seconds unless it's an info message for loading
    if (type !== 'info') {
        setTimeout(() => {
            messageElement.classList.add('hidden');
        }, 3000);
    }
}

// Print receipt function (can be used on receipt page)
function printReceipt() {
    window.print();
}

// Update the bill every 2 seconds
setInterval(updateBill, 2000);

// Initialize the bill display on page load
document.addEventListener('DOMContentLoaded', updateBill);
