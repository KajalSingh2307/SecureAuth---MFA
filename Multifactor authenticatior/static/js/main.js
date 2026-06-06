// SecureAuth MFA Client-Side Helper

document.addEventListener('DOMContentLoaded', () => {
    // 1. Setup multi-digit OTP fields if they exist
    initOtpInputs();
    
    // 2. Setup inactivity countdown timer if session is active
    initSessionTimer();
    
    // 3. Setup Clipboard copying for secret key
    initSecretCopy();
});

/**
 * Handle 6-digit split OTP input boxes
 */
function initOtpInputs() {
    const otpContainer = document.querySelector('.otp-input-container');
    if (!otpContainer) return;
    
    const digits = otpContainer.querySelectorAll('.otp-digit');
    const hiddenInput = document.querySelector('#otp-hidden');
    const form = otpContainer.closest('form');
    
    if (digits.length === 0 || !hiddenInput) return;
    
    // Autofocus first input
    digits[0].focus();
    
    // Process each input box
    digits.forEach((input, index) => {
        // Handle input events (typing digits)
        input.addEventListener('input', (e) => {
            const val = e.target.value;
            // Allow only numbers
            e.target.value = val.replace(/[^0-9]/g, '');
            
            if (e.target.value.length > 0) {
                // Focus next input if available
                if (index < digits.length - 1) {
                    digits[index + 1].focus();
                }
            }
            updateHiddenValue();
        });
        
        // Handle keyboard navigation (backspace, arrow keys)
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace') {
                if (input.value.length === 0 && index > 0) {
                    digits[index - 1].value = '';
                    digits[index - 1].focus();
                    updateHiddenValue();
                }
            } else if (e.key === 'ArrowLeft' && index > 0) {
                digits[index - 1].focus();
            } else if (e.key === 'ArrowRight' && index < digits.length - 1) {
                digits[index + 1].focus();
            }
        });
        
        // Handle pasting of full code (e.g. 123456)
        input.addEventListener('paste', (e) => {
            e.preventDefault();
            const pasteData = (e.clipboardData || window.clipboardData).getData('text').trim();
            
            // Look for a 6-digit number sequence
            if (/^\d{6}$/.test(pasteData)) {
                for (let i = 0; i < digits.length; i++) {
                    digits[i].value = pasteData[i];
                }
                digits[digits.length - 1].focus();
                updateHiddenValue();
            }
        });
    });
    
    function updateHiddenValue() {
        let code = '';
        digits.forEach(input => {
            code += input.value;
        });
        hiddenInput.value = code;
    }
    
    // Form submission validation
    if (form) {
        form.addEventListener('submit', (e) => {
            updateHiddenValue();
            if (hiddenInput.value.length !== 6) {
                e.preventDefault();
                otpContainer.classList.add('shake-animation');
                setTimeout(() => {
                    otpContainer.classList.remove('shake-animation');
                }, 500);
            }
        });
    }
}

/**
 * Visual countdown widget for session timeout
 */
function initSessionTimer() {
    const timerElement = document.getElementById('session-countdown');
    if (!timerElement) return;
    
    // Session length in seconds (15 minutes = 900 seconds)
    // Server-side session also enforces this.
    let remainingTime = parseInt(timerElement.dataset.timeoutSeconds || "900", 10);
    const dot = document.querySelector('.timer-dot');
    
    const interval = setInterval(() => {
        remainingTime--;
        
        if (remainingTime <= 0) {
            clearInterval(interval);
            timerElement.textContent = "Session Expired";
            window.location.href = "/login?timeout=1";
            return;
        }
        
        // Update countdown text
        const minutes = Math.floor(remainingTime / 60);
        const seconds = remainingTime % 60;
        timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        // Change warning levels on UI widget
        if (remainingTime < 60) {
            // Less than 1 minute
            if (dot) {
                dot.className = 'timer-dot danger';
            }
            timerElement.style.color = '#ef4444';
        } else if (remainingTime < 180) {
            // Less than 3 minutes
            if (dot) {
                dot.className = 'timer-dot warning';
            }
            timerElement.style.color = '#f59e0b';
        }
    }, 1000);
    
    // Reset timer on client activity pings (can be done if we wanted to ping server, 
    // but we will keep it simple. Clicking "extend session" or reloading does it natively.)
}

/**
 * Setup Copy to Clipboard for the secret base32 key
 */
function initSecretCopy() {
    const copyBtn = document.querySelector('.secret-copy-btn');
    if (!copyBtn) return;
    
    copyBtn.addEventListener('click', () => {
        const textToCopy = copyBtn.dataset.key;
        if (!textToCopy) return;
        
        navigator.clipboard.writeText(textToCopy).then(() => {
            const originalText = copyBtn.textContent;
            copyBtn.textContent = 'Copied!';
            copyBtn.style.color = '#10b981';
            
            setTimeout(() => {
                copyBtn.textContent = originalText;
                copyBtn.style.color = '';
            }, 2000);
        }).catch(err => {
            console.error('Could not copy secret key: ', err);
        });
    });
}
