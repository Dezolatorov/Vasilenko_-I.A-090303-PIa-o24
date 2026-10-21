// Витрина каталога (ЛР №10): данные из REST API Flask.

const API = document.body.dataset.api || "";
const state = { query: "", available: false, sort: "title" };

const catalogElement = document.getElementById("catalog");
const counterElement = document.getElementById("counter");
const statusElement = document.getElementById("status");
const panel = document.getElementById("panel");
const panelTitle = document.getElementById("panel-title");
const panelAuthor = document.getElementById("panel-author");
const panelFacts = document.getElementById("panel-facts");
const panelApi = document.getElementById("panel-api");

function card(book) {
    const article = document.createElement("article");
    article.className = "card";
    article.dataset.id = book.id;

    const badge = book.available > 0
        ? `<span class="badge ok">в наличии: ${book.available}</span>`
        : `<span class="badge none">нет в наличии</span>`;

    article.innerHTML = `
        <div class="card-head">
            <span class="card-id">#${book.id}</span>
            ${badge}
        </div>
        <div class="title">${book.title}</div>
        <div class="author">${book.author}</div>
        <div class="meta">${book.genre}, ${book.year} · ${book.price} ₽</div>
    `;
    article.addEventListener("click", () => openDetails(book.id));
    return article;
}

async function loadCatalog() {
    const params = new URLSearchParams();
    if (state.available) params.set("available", "true");
    params.set("sort", state.sort);
    params.set("order", state.sort === "price" ? "desc" : "asc");

    catalogElement.innerHTML = `<p class="empty">загрузка каталога…</p>`;
    try {
        const response = await fetch(`${API}/books?${params.toString()}`);
        const data = await response.json();

        const query = state.query.toLowerCase();
        let items = Array.isArray(data) ? data : [];
        if (state.query) {
            items = items.filter((book) =>
                book.title.toLowerCase().includes(query) ||
                book.author.toLowerCase().includes(query)
            );
        }

        catalogElement.innerHTML = "";
        if (!items.length) {
            catalogElement.innerHTML = `<p class="empty">книги не найдены</p>`;
        }
        items.forEach((book) => catalogElement.appendChild(card(book)));
        counterElement.textContent = `книг в выборке: ${items.length}`;
    } catch (error) {
        catalogElement.innerHTML = `<p class="empty">REST API недоступен: ${error.message}</p>`;
    }
}

async function loadStatus() {
    try {
        const response = await fetch(`${API}/books`);
        const data = await response.json();
        const total = Array.isArray(data) ? data.length : 0;
        statusElement.textContent = `API: 200 OK · книг в фонде: ${total}`;
    } catch (error) {
        statusElement.textContent = "API недоступен";
    }
}

async function openDetails(bookId) {
    const response = await fetch(`${API}/books/${bookId}`);
    const book = await response.json();

    panelTitle.textContent = book.title;
    panelAuthor.textContent = book.author;
    panelFacts.innerHTML = `
        <dt>Жанр</dt><dd>${book.genre}</dd>
        <dt>Год издания</dt><dd>${book.year}</dd>
        <dt>Цена</dt><dd>${book.price} ₽</dd>
        <dt>В наличии</dt><dd>${book.available}</dd>
    `;
    panelApi.textContent = `GET /books/${bookId} → HTTP 200 (JSON)`;
    panel.hidden = false;
}

let searchTimer = null;
document.getElementById("search").addEventListener("input", (event) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
        state.query = event.target.value.trim();
        loadCatalog();
    }, 250);
});

document.getElementById("only-available").addEventListener("change", (event) => {
    state.available = event.target.checked;
    loadCatalog();
});

document.getElementById("sort").addEventListener("change", (event) => {
    state.sort = event.target.value;
    loadCatalog();
});

document.getElementById("panel-close").addEventListener("click", () => {
    panel.hidden = true;
});

document.addEventListener("DOMContentLoaded", async () => {
    await loadStatus();
    await loadCatalog();
});