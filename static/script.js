document.getElementById("loginForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    const formData = new FormData(this);

    const response = await fetch("/login", {
        method: "POST",
        body: formData
    });

    if (response.redirected) {
        window.location.href = response.url;
    } else {
        document.getElementById("erro").innerText = "Login inválido";
    }
});

