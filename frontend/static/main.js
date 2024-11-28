const form = document.getElementById("inputForm");
const error = {
    repoUrl: "",
    accessToken: "",
    email: ""
};

form.addEventListener('submit', function(event) {
    event.preventDefault(); 

    // Reset error messages
    Object.keys(error).forEach(key => error[key] = "");
    form.classList.remove('was-validated');


    // Collect input values
    const repoUrl = document.getElementById('repo-url').value;
    const accessToken = document.getElementById('access-token').value;
    const email = document.getElementById('email').value;

    // Validate inputs
    if (!validateGitHubUrl(repoUrl)) {
        error.repoUrl = "Valid URL (https://github.com/username/repository) is required.";
    }
    if (!accessToken || !validateAccessToken(accessToken)) {
        error.accessToken = "Valid Github PAT: github_pat_xxxxxx";
    }
    if (!email || !validateEmail(email)) {
        error.email = "Valid email is required.";
    }

    if (error.repoUrl || error.accessToken || error.email) {
        renderErrors(); 
        return;
    }

    const loaderOverlay = document.getElementById('loaderOverlay');

    loaderOverlay.style.display = 'flex'; 

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
        loaderOverlay.style.display = 'none'; // Hide the overlay

        if (response.ok) {
            return response.text();  // Get the response as text
        } else {
            console.error('Response status:', response.status);
            throw new Error(`Network response was not ok: ${response.statusText}`);
        }
    })
    .then(html => {
        // Here, you can use innerHTML to render the HTML response into a specific element
        document.open();
        document.write(html);
        document.close();
    })
    .catch(error => {
        console.error('Error:', error); 
        alert('Something went wrong!'); // Optional: Show an alert for the error
    });
});

// Function to render errors on the TextFields
function renderErrors() {
    // Clear previous error states
    
    form.classList.remove('was-validated');

    // Check for errors and update input styles
    const repoUrlInput = document.getElementById("repo-url");
    const accessTokenInput = document.getElementById("access-token");
    const emailInput = document.getElementById("email");

    if (error.repoUrl) {
        repoUrlInput.classList.add("is-invalid");
        repoUrlInput.nextElementSibling.innerText = error.repoUrl;
    } else {
        repoUrlInput.classList.remove("is-invalid");
    }

    if (error.accessToken) {
        accessTokenInput.classList.add("is-invalid");
        accessTokenInput.nextElementSibling.innerText = error.accessToken;
    } else {
        accessTokenInput.classList.remove("is-invalid");
    }

    if (error.email) {
        emailInput.classList.add("is-invalid");
        emailInput.nextElementSibling.innerText = error.email;
    } else {
        emailInput.classList.remove("is-invalid");
    }

    // Activate Bootstrap validation
    form.classList.add('was-validated');
}

// Function to validate email format
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(String(email).toLowerCase());
}

// Function to validate GitHub URL format
function validateGitHubUrl(url) {
    const re = /^https:\/\/github\.com\/[^/]+\/[^/]+$/; // Matches "https://github.com/username/repository"
    return re.test(url);
}

// Function to validate Access Token format
function validateAccessToken(token) {
    const re = /^github_pat_[A-Za-z0-9_-]{36,}$/; // Matches GitHub PAT format
    return re.test(token);
}
