/**
 * Click Payment Integration for VoiceConnect
 * 
 * This module handles Click payment system integration for Uzbekistan market,
 * replacing Stripe with local payment infrastructure.
 */

class ClickPaymentManager {
    constructor() {
        this.apiBaseUrl = '/api/v1/payments/click';
        this.currentPayment = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadPaymentHistory();
    }

    setupEventListeners() {
        // Subscription payment buttons
        document.querySelectorAll('.subscribe-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const plan = e.target.dataset.plan;
                const amount = e.target.dataset.amount;
                this.createSubscriptionPayment(plan, amount);
            });
        });

        // One-time payment buttons
        document.querySelectorAll('.pay-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const amount = e.target.dataset.amount;
                const description = e.target.dataset.description;
                this.createOneTimePayment(amount, description);
            });
        });

        // Payment status check
        document.getElementById('check-payment-btn')?.addEventListener('click', () => {
            const transactionId = document.getElementById('transaction-id').value;
            if (transactionId) {
                this.checkPaymentStatus(transactionId);
            }
        });
    }

    async createSubscriptionPayment(plan, amount) {
        try {
            this.showLoading('Creating subscription payment...');

            const tenantId = this.getCurrentTenantId();
            if (!tenantId) {
                throw new Error('Tenant ID not found. Please log in again.');
            }

            const response = await fetch(`${this.apiBaseUrl}/create-subscription`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    tenant_id: tenantId,
                    plan: plan,
                    amount: parseFloat(amount)
                })
            });

            const result = await response.json();

            if (result.success) {
                this.currentPayment = {
                    type: 'subscription',
                    plan: plan,
                    amount: amount,
                    merchant_trans_id: result.merchant_trans_id
                };

                this.showPaymentModal(result);
            } else {
                throw new Error(result.error || 'Failed to create subscription payment');
            }

        } catch (error) {
            console.error('Error creating subscription payment:', error);
            this.showError('Failed to create subscription payment: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async createOneTimePayment(amount, description) {
        try {
            this.showLoading('Creating payment...');

            const response = await fetch(`${this.apiBaseUrl}/create-payment`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    amount: parseFloat(amount),
                    description: description,
                    return_url: window.location.origin + '/payment/success'
                })
            });

            const result = await response.json();

            if (result.success) {
                this.currentPayment = {
                    type: 'one_time',
                    amount: amount,
                    description: description,
                    merchant_trans_id: result.merchant_trans_id
                };

                this.showPaymentModal(result);
            } else {
                throw new Error(result.error || 'Failed to create payment');
            }

        } catch (error) {
            console.error('Error creating payment:', error);
            this.showError('Failed to create payment: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    showPaymentModal(paymentData) {
        const modal = document.getElementById('click-payment-modal') || this.createPaymentModal();
        
        // Update modal content
        modal.querySelector('.payment-amount').textContent = `${paymentData.amount.toLocaleString()} UZS`;
        modal.querySelector('.payment-description').textContent = paymentData.description;
        modal.querySelector('.transaction-id').textContent = paymentData.merchant_trans_id;
        
        // Set payment URL
        const payButton = modal.querySelector('.click-pay-button');
        payButton.href = paymentData.payment_url;
        payButton.onclick = () => {
            // Track payment initiation
            this.trackPaymentEvent('payment_initiated', paymentData.merchant_trans_id);
            
            // Open Click payment in new window
            window.open(paymentData.payment_url, 'click_payment', 'width=800,height=600');
            
            // Start polling for payment status
            this.startPaymentStatusPolling(paymentData.merchant_trans_id);
            
            return false;
        };

        // Show modal
        modal.style.display = 'block';
        document.body.classList.add('modal-open');
    }

    createPaymentModal() {
        const modal = document.createElement('div');
        modal.id = 'click-payment-modal';
        modal.className = 'payment-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Click Payment</h3>
                    <span class="close-modal">&times;</span>
                </div>
                <div class="modal-body">
                    <div class="payment-details">
                        <div class="payment-info">
                            <p><strong>Amount:</strong> <span class="payment-amount"></span></p>
                            <p><strong>Description:</strong> <span class="payment-description"></span></p>
                            <p><strong>Transaction ID:</strong> <span class="transaction-id"></span></p>
                        </div>
                        <div class="payment-instructions">
                            <p>Click the button below to proceed with payment through Click system:</p>
                        </div>
                        <div class="payment-actions">
                            <a href="#" class="click-pay-button btn btn-primary">
                                Pay with Click
                            </a>
                            <button class="cancel-payment-btn btn btn-secondary">
                                Cancel
                            </button>
                        </div>
                    </div>
                    <div class="payment-status" style="display: none;">
                        <div class="status-indicator">
                            <div class="spinner"></div>
                            <p>Waiting for payment confirmation...</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add event listeners
        modal.querySelector('.close-modal').onclick = () => this.closePaymentModal();
        modal.querySelector('.cancel-payment-btn').onclick = () => this.cancelPayment();

        document.body.appendChild(modal);
        return modal;
    }

    async startPaymentStatusPolling(merchantTransId) {
        const modal = document.getElementById('click-payment-modal');
        const paymentDetails = modal.querySelector('.payment-details');
        const paymentStatus = modal.querySelector('.payment-status');
        
        // Show status indicator
        paymentDetails.style.display = 'none';
        paymentStatus.style.display = 'block';

        let attempts = 0;
        const maxAttempts = 60; // 5 minutes with 5-second intervals
        
        const pollInterval = setInterval(async () => {
            attempts++;
            
            try {
                const status = await this.checkPaymentStatus(merchantTransId);
                
                if (status.status === 'completed') {
                    clearInterval(pollInterval);
                    this.handlePaymentSuccess(merchantTransId);
                } else if (status.status === 'failed' || status.status === 'cancelled') {
                    clearInterval(pollInterval);
                    this.handlePaymentFailure(merchantTransId, status.status);
                } else if (attempts >= maxAttempts) {
                    clearInterval(pollInterval);
                    this.handlePaymentTimeout(merchantTransId);
                }
                
            } catch (error) {
                console.error('Error checking payment status:', error);
                if (attempts >= maxAttempts) {
                    clearInterval(pollInterval);
                    this.handlePaymentError(merchantTransId, error.message);
                }
            }
        }, 5000); // Check every 5 seconds
    }

    async checkPaymentStatus(merchantTransId) {
        const response = await fetch(`${this.apiBaseUrl}/payment-status/${merchantTransId}`, {
            headers: {
                'Authorization': `Bearer ${this.getAuthToken()}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to check payment status');
        }

        return await response.json();
    }

    handlePaymentSuccess(merchantTransId) {
        this.trackPaymentEvent('payment_completed', merchantTransId);
        this.showSuccess('Payment completed successfully!');
        this.closePaymentModal();
        this.refreshPage();
    }

    handlePaymentFailure(merchantTransId, status) {
        this.trackPaymentEvent('payment_failed', merchantTransId);
        this.showError(`Payment ${status}. Please try again.`);
        this.closePaymentModal();
    }

    handlePaymentTimeout(merchantTransId) {
        this.trackPaymentEvent('payment_timeout', merchantTransId);
        this.showWarning('Payment status check timed out. Please check your payment manually.');
        this.closePaymentModal();
    }

    handlePaymentError(merchantTransId, error) {
        this.trackPaymentEvent('payment_error', merchantTransId);
        this.showError('Error checking payment status: ' + error);
        this.closePaymentModal();
    }

    async cancelPayment() {
        if (this.currentPayment && this.currentPayment.merchant_trans_id) {
            try {
                await fetch(`${this.apiBaseUrl}/cancel-payment`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.getAuthToken()}`
                    },
                    body: JSON.stringify({
                        merchant_trans_id: this.currentPayment.merchant_trans_id,
                        reason: 'User cancelled payment'
                    })
                });

                this.trackPaymentEvent('payment_cancelled', this.currentPayment.merchant_trans_id);
            } catch (error) {
                console.error('Error cancelling payment:', error);
            }
        }

        this.closePaymentModal();
    }

    closePaymentModal() {
        const modal = document.getElementById('click-payment-modal');
        if (modal) {
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
        }
        this.currentPayment = null;
    }

    async loadPaymentHistory() {
        try {
            // TODO: Implement payment history loading
            // This should fetch payment history from the backend
            console.log('Loading payment history...');
        } catch (error) {
            console.error('Error loading payment history:', error);
        }
    }

    // Utility methods
    getCurrentTenantId() {
        // Get tenant ID from localStorage, session, or API
        return localStorage.getItem('tenant_id') || 
               document.querySelector('meta[name="tenant-id"]')?.content;
    }

    getAuthToken() {
        return localStorage.getItem('auth_token') || 
               document.querySelector('meta[name="csrf-token"]')?.content;
    }

    trackPaymentEvent(event, merchantTransId) {
        // Track payment events for analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', event, {
                'transaction_id': merchantTransId,
                'payment_method': 'click'
            });
        }
        
        console.log(`Payment event: ${event}`, merchantTransId);
    }

    showLoading(message) {
        const loader = document.getElementById('payment-loader') || this.createLoader();
        loader.querySelector('.loader-message').textContent = message;
        loader.style.display = 'block';
    }

    hideLoading() {
        const loader = document.getElementById('payment-loader');
        if (loader) {
            loader.style.display = 'none';
        }
    }

    createLoader() {
        const loader = document.createElement('div');
        loader.id = 'payment-loader';
        loader.className = 'payment-loader';
        loader.innerHTML = `
            <div class="loader-content">
                <div class="spinner"></div>
                <p class="loader-message">Processing...</p>
            </div>
        `;
        document.body.appendChild(loader);
        return loader;
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showWarning(message) {
        this.showNotification(message, 'warning');
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;

        notification.querySelector('.notification-close').onclick = () => {
            notification.remove();
        };

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    refreshPage() {
        // Refresh the page or specific sections after successful payment
        setTimeout(() => {
            window.location.reload();
        }, 2000);
    }
}

// Initialize Click Payment Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.clickPaymentManager = new ClickPaymentManager();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ClickPaymentManager;
}