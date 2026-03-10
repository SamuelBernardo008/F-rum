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

function toggleNotifs() {
            const dropdown = document.getElementById('notifDropdown');
            dropdown.classList.toggle('show');
        }

        // Fecha o dropdown se clicar fora dele
        window.onclick = function(event) {
            if (!event.target.closest('.notif-container')) {
                const dropdown = document.getElementById('notifDropdown');
                if (dropdown.classList.contains('show')) {
                    dropdown.classList.remove('show');
                }
            }
        }

document.querySelectorAll('.link-ajax').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault(); // Impede o recarregamento da página
        const url = this.getAttribute('href');

        fetch(url)
            .then(response => response.text())
            .then(html => {
                document.getElementById('conteudo-dinamico').innerHTML = html;
                // Atualiza a URL no navegador sem recarregar
                window.history.pushState({}, '', url); 
            });
    });
});