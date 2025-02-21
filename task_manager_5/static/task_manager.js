document.getElementById("addTaskBtn").addEventListener("click", function() {
    const taskInput = document.getElementById("taskInput").value;
    fetch('/tasks', {
        method: 'POST',
        body: JSON.stringify({ task_name: taskInput }),
        headers: { 'Content-Type': 'application/json' },
    });

    const msg = new SpeechSynthesisUtterance(taskInput + " added.");
    window.speechSynthesis.speak(msg);
});

const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.onresult = function(event) {
    const taskInput = event.results[0][0].transcript;
    document.getElementById("taskInput").value = taskInput;
    fetch('/tasks', {
        method: 'POST',
        body: JSON.stringify({ task_name: taskInput }),
        headers: { 'Content-Type': 'application/json' },
    });

    const msg = new SpeechSynthesisUtterance(taskInput + " added.");
    window.speechSynthesis.speak(msg);
};
recognition.start();
