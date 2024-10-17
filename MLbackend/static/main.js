document.getElementById('inputForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission

    // Collect input values
    const repoUrl = document.getElementById('repo-url').value;
    const accessToken = document.getElementById('access-token').value;
    const email = document.getElementById('email').value;

    // Get the loader element
    const loader = document.querySelector('.loader');
    loader.style.display = 'block';

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
        loader.style.display = 'none'; // Hide loader 
        if (!response.ok) {
            alert('Something went wrong!');
            throw new Error('Network response was not ok');
        }
        return response.json(); // Parse the JSON response
    })
    .then(data => {
        // Store the data securely in session storage
        sessionStorage.setItem('resultData', JSON.stringify(data.result));
        // Redirect to the results page
        //window.location.href = '/MLbackend/templates/results.html';
        alert('Success!');
    })
    .catch(error => {
        console.error('Error:', error); 
        alert('Something went wrong!'); // Optional: Show an alert for the error
    });
});
