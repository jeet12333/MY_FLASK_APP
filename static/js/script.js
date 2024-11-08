document.addEventListener('DOMContentLoaded', () => {
    const socket = io(); // Only declared once here

    const username = document.getElementById("chat-username").textContent;

    // Fetch and display all users
    function fetchUsers() {
        fetch('/users')
            .then(response => response.json())
            .then(users => {
                const userList = document.getElementById("user-list");
                userList.innerHTML = ""; // Clear existing users
                users.forEach(user => {
                    const li = document.createElement("li");
                    li.textContent = user;
                    li.onclick = () => selectUser(user);
                    userList.appendChild(li);
                });
            });
    }

    // Select user and display chat
    function selectUser(user) {
        document.getElementById("chat-username").textContent = user;
        const messagesDiv = document.getElementById("messages");
        if (messagesDiv) messagesDiv.innerHTML = ""; // Clear chat history for the selected user
    }

    // Function to send a message
    function sendMessage() {
        const messageInput = document.getElementById("message");
        const message = messageInput.value;
        const chatUser = document.getElementById("chat-username").textContent;

        if (message) {
            socket.emit('message', { username: chatUser, message });
            displayMessage(username, message, 'right'); // Display on right side
            messageInput.value = '';
        }
    }

    // Function to display message in chat area
    function displayMessage(sender, message, position) {
        const messagesDiv = document.getElementById("messages");
        if (messagesDiv) {
            const messageElement = document.createElement("div");
            messageElement.classList.add("message", position);
            messageElement.textContent = `${sender}: ${message}`;
            messagesDiv.appendChild(messageElement);
            messagesDiv.scrollTop = messagesDiv.scrollHeight; // Scroll to the bottom
        }
    }

    // Receive message and display in chat history
    socket.on('message', function(data) {
        const position = data.username === username ? 'right' : 'left'; // Adjust position
        displayMessage(data.username, data.message, position);
    });

    // Function to search for a user
    document.getElementById("search-user").addEventListener("input", function() {
        const searchTerm = this.value.toLowerCase();
        const userListItems = document.querySelectorAll(".user-list li");
        userListItems.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(searchTerm) ? "" : "none"; // Show or hide based on search term
        });
    });

    // Function to logout
    document.getElementById('logout-button').addEventListener('click', function() {
        fetch('/logout', {
            method: 'POST' // Use the method expected by your server
        })
        .then(response => {
            if (response.ok) {
                window.location.href = '/'; // Redirect after successful logout
            } else {
                console.error('Logout failed');
            }
        })
        .catch(error => console.error('Error:', error));
    });

    // Function to send a file
    function sendFile() {
        const fileInput = document.getElementById("file-input");
        const file = fileInput.files[0];
        const chatUser = document.getElementById("chat-username").textContent;

        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                const fileData = event.target.result;
                socket.emit('file', { filename: file.name, data: fileData, username: chatUser });
            };
            reader.readAsArrayBuffer(file);
        }
    }

    // Receive and display file notification
    socket.on('file', function(data) {
        const messagesDiv = document.getElementById("messages");
        if (messagesDiv) {
            const fileElement = document.createElement("div");
            fileElement.classList.add("file-message");
            fileElement.textContent = `${data.username} sent a file: ${data.filename}`;
            messagesDiv.appendChild(fileElement);
            messagesDiv.scrollTop = messagesDiv.scrollHeight; // Scroll to the bottom
        }
    });

    // Initialize chat and user list on page load
    fetchUsers(); // Fetch users when the document is loaded
});
