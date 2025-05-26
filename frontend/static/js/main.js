// Custom JavaScript functions will go here

document.addEventListener('DOMContentLoaded', function() {
    // Basic logout functionality (assuming JWT is stored in localStorage)
    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(event) {
            event.preventDefault();
            
            // Clear tokens from localStorage (or wherever they are stored)
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            
            // Redirect to login page or home page
            // This assumes you have a 'login' URL name configured in your Django URLs.
            // If not, adjust the redirect URL accordingly.
            window.location.href = '/login/'; // Or your actual login page URL
            
            // Optionally, you can also make a request to the backend logout endpoint
            // to invalidate the refresh token on the server side.
            // fetch('/api/users/logout/', {
            //     method: 'POST',
            //     headers: {
            //         'Content-Type': 'application/json',
            //         // Include Authorization header if your logout endpoint requires it
            //     },
            //     body: JSON.stringify({ refresh: localStorage.getItem('refreshToken') }) 
            // })
            // .then(response => {
            //     if (response.ok) {
            //         console.log('Successfully logged out from backend.');
            //     } else {
            //         console.error('Backend logout failed.');
            //     }
            // })
            // .catch(error => console.error('Error during backend logout:', error));
        });
    }
});