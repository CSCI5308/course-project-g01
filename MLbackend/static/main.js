document.getElementById('inputForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission

    // Collect input values
    const repoUrl = document.getElementById('repo-url').value;
    const accessToken = document.getElementById('access-token').value;
    const email = document.getElementById('email').value;

    // Send a POST request to the Flask backend
    fetch('/api/v1/smells', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'repo-url': repoUrl,
            'access-token': accessToken,
            'email': email
        }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json(); // Parse the JSON response
    })
    .then(data => {
        // Alert the message received from the server
        alert(data.status); 
    })
    .catch(error => {
        console.error('Error:', error); 
        alert('An error occurred: ' + error.message); // Optional: Show an alert for the error
    });
});
