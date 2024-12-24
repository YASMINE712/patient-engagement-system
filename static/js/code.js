document.getElementById('signupForm').addEventListener('submit', function(event) {
    event.preventDefault();

    // Get the user inputs
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // Create a data object
    const data = {
        username: username,
        password: password
    };

    // Send the data to Flask via POST request
    fetch('/signup', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        // Display success message
        document.getElementById('responseMessage').innerText = data.message;
    })
    .catch((error) => {
        console.error('Error:', error);
        document.getElementById('responseMessage').innerText = "Oops, something went wrong. Please try again!";
    });
});
