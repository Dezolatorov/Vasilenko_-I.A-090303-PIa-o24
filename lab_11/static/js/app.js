// Витрина каталога: данные берутся из REST API, обложки — из CDN.

const API = document.body.dataset.api || "";
const CDN = (document.body.dataset.cdn || "").replace(/\/$/, "");

const state = { query: "", available: false, sort: "title", selectedId: null };

const catalogElement = document.getElementById("catalog");
const counterElement = document.getElementById("counter");
const statusElement = document.getElementById("status");
const panel = document.getElementById("panel");
const panelTitle = document.getElementById("panel-title");
const panelAuthor = document.getElementById("panel-author");
const panelFacts = document.getElementById("panel-facts");
const panelTags = document.getElementById("panel-tags");
const panelMessage = document.getElementById("panel-message");
const readerSelect = document.getElementById("reader");

function card(book) {
    const article = document.createElement("article");
    article.className = "card";
    article.dataset.id = book.id;

    const cover = book.cover_url
        ? `<img src="${book.cover_url}" alt="Обложка: ${book.title}" loading="lazy">`
        : `<div class="cover-empty">нет обложки</div>`;

    const badge = book.available_copies > 0
        ? `<span class="badge ok">в наличии: ${book.available_copies} из ${book.total_copies}</span>`
        : `<span class="badge none">все выданы</span>`;

    article.innerHTML = `
        ${cover}
        <div class="title">${book.title}</div>
        <div class="author">${book.author}</div>
        <div class="meta">${book.genre}, ${book.year} · ${book.price} ₽</div>
        ${badge}
    `;
    article.addEventListener("click", () => openDetails(book.id));
    return article;
}

async function loadCatalog() {
    const params = new URLSearchParams();
    if (state.query) params.set("q", state.query);
    if (state.available) params.set("available", "true");
    params.set("sort", state.sort);
    params.set("order", state.sort === "price" ? "desc" : "asc");

    catalogElement.innerHTML = `<p class="empty">загрузка каталога…</p>`;
    try {
        const response = await fetch(`${API}/catalog?${params.toString()}`);
        const data = await response.json();

        catalogElement.innerHTML = "";
        if (!data.items.length) {
            catalogElement.innerHTML = `<p class="empty">книги не найдены</p>`;
        }
        data.items.forEach((book) => catalogElement.appendChild(card(book)));
        counterElement.textContent = `книг в выборке: ${data.count}`;
    } catch (error) {
        catalogElement.innerHTML = `<p class="empty">REST API недоступен: ${error.message}</p>`;
    }
}

async function loadStatus() {
    try {
        const response = await fetch(`${API}/health`);
        const data = await response.json();
        statusElement.textContent = `API: ${data.status} · БД: ${data.database} · кэш: ${data.cache} · TTL ${data.cache_ttl} с`;
    } catch (error) {
        statusElement.textContent = "API недоступен";
    }
}

async function loadReaders() {
    const response = await fetch(`${API}/readers`);
    const data = await response.json();
    readerSelect.innerHTML = data.items
        .map((reader) => `<option value="${reader.id}">${reader.full_name}</option>`)
        .join("");
}

async function openDetails(bookId) {
    state.selectedId = bookId;
    panelMessage.textContent = "";
    const response = await fetch(`${API}/books/${bookId}/details`);
    const book = await response.json();

    panelTitle.textContent = book.title;
    panelAuthor.textContent = book.author;
    panelFacts.innerHTML = `
        <dt>Жанр</dt><dd>${book.genre}</dd>
        <dt>Год издания</dt><dd>${book.year}</dd>
        <dt>Цена</dt><dd>${book.price} ₽</dd>
        <dt>В наличии</dt><dd>${book.available_copies} из ${book.total_copies}</dd>
        <dt>Обложка</dt><dd><a href="${book.cover_url}" target="_blank" rel="noreferrer">CDN</a></dd>
    `;
    panelTags.innerHTML = book.tags.map((tag) => `<span class="tag">${tag}</span>`).join("");
    panel.hidden = false;
}

async function issueLoan() {
    if (!state.selectedId) return;
    const payload = { book_id: state.selectedId, reader_id: Number(readerSelect.value), days: 14 };

    const response = await fetch(`${API}/loans`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (response.ok) {
        panelMessage.className = "panel-message ok";
        panelMessage.textContent = `Выдано, срок возврата: ${data.due_at}`;
        await loadCatalog();
        await openDetails(state.selectedId);
    } else {
        panelMessage.className = "panel-message error";
        panelMessage.textContent = `Ошибка ${response.status}: ${data.error}`;
    }
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
    state.selectedId = null;
});

document.getElementById("issue").addEventListener("click", issueLoan);

document.addEventListener("DOMContentLoaded", async () => {
    await loadStatus();
    await loadReaders();
    await loadCatalog();
});
