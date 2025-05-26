// Custom JavaScript functions will go here

document.addEventListener('DOMContentLoaded', function() {
    // Basic logout functionality (assuming JWT is stored in localStorage)
    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(event) {
            event.preventDefault();
            
            const refreshToken = localStorage.getItem('refreshToken');

            // Optionally, you can also make a request to the backend logout endpoint
            // to invalidate the refresh token on the server side.
            fetch('/api/users/logout/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // No Authorization header needed for DRF SimpleJWT's TokenBlacklistView if it's configured for public access
                    // or if the refresh token itself is the credential.
                },
                body: JSON.stringify({ refresh: refreshToken }) 
            })
            .then(response => {
                if (response.ok) {
                    console.log('Successfully logged out from backend. Refresh token invalidated.');
                } else {
                    // Even if backend logout fails (e.g. token already expired or invalid),
                    // still proceed with client-side cleanup.
                    console.error('Backend logout failed. Status:', response.status);
                    return response.json().then(err => console.error('Error details:', err));
                }
            })
            .catch(error => {
                console.error('Error during backend logout attempt:', error);
            })
            .finally(() => {
                // Clear tokens from localStorage (or wherever they are stored)
                localStorage.removeItem('accessToken');
                localStorage.removeItem('refreshToken');
                
                // Redirect to login page or home page
                // This assumes you have a 'login' URL name configured in your Django URLs.
                // If not, adjust the redirect URL accordingly.
                window.location.href = '/login/'; // Or your actual login page URL
            });
        });
    }
});
