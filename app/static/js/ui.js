const btnProfile = document.getElementById('btn-profile'); // Botão do perfil pelo ID
const menuProfile = document.getElementById('menu-profile'); // Menu suspenso do perfil

if (btnProfile && menuProfile) { // Verifica se os elementos existem na página
  btnProfile.addEventListener('click', () => { // Adiciona evento de clique ao botão
    menuProfile.classList.toggle('open'); // Alterna a classe 'open' para mostrar/ocultar o menu
  });

  document.addEventListener('click', (e) => { // Captura cliques no documento
    const clickedInside = btnProfile.contains(e.target) || menuProfile.contains(e.target); // Verifica se clicou dentro do perfil
    if (!clickedInside) menuProfile.classList.remove('open'); // Se clicou fora, fecha o menu
  });
}

// ====== CHECKBOXES EXCLUSIVAS (TÍTULO x AUTOR) ======
const formFilters = document.querySelector('.search--filters');
if (formFilters) {
  const chkTitle  = formFilters.querySelector('#chk-title');
  const chkAuthor = formFilters.querySelector('#chk-author');
  const hiddenSearchBy = formFilters.querySelector('input[name="search_by"]');

  function syncMode() {
    if (!hiddenSearchBy) return;
    hiddenSearchBy.value = (chkAuthor && chkAuthor.checked) ? 'author' : 'title';
  }

  function enforceExclusive(changed) {
    if (!chkTitle || !chkAuthor) return;
    if (changed === chkTitle  && chkTitle.checked)  chkAuthor.checked = false;
    if (changed === chkAuthor && chkAuthor.checked) chkTitle.checked  = false;
    if (!chkTitle.checked && !chkAuthor.checked) chkTitle.checked = true;
    syncMode();
  }

  chkTitle?.addEventListener('change',  () => enforceExclusive(chkTitle));
  chkAuthor?.addEventListener('change', () => enforceExclusive(chkAuthor));
  formFilters.addEventListener('submit', syncMode);

  enforceExclusive(chkAuthor?.checked ? chkAuthor : chkTitle);
}

// ===== MODAL DE DETALHES =====
const modal = document.getElementById("book-modal");
const modalClose = document.querySelector(".modal-close");

if (modal) {
  // elementos internos
  const modalCover = document.getElementById("modal-cover");
  const modalTitle = document.getElementById("modal-title");
  const modalAuthor = document.getElementById("modal-author");
  const modalPublisher = document.getElementById("modal-publisher");
  const modalPages = document.getElementById("modal-pages");
  const modalDate = document.getElementById("modal-date");
  const modalDesc = document.getElementById("modal-description");

  function openBookModal(book) {
    modalCover.src = book.cover;
    modalTitle.textContent = book.title;
    modalAuthor.textContent = book.authors;
    modalPublisher.textContent = book.publisher || "—";
    modalPages.textContent = book.pageCount || "—";
    modalDate.textContent = book.publishedDate || "—";
    modalDesc.textContent = book.description || "Sem descrição disponível";
    modal.style.display = "flex";
  }

  modalClose.addEventListener("click", () => modal.style.display = "none");
  window.addEventListener("click", (e) => {
    if (e.target === modal) modal.style.display = "none";
  });

  // adicionar eventos nos livros
  document.querySelectorAll(".card").forEach(card => {
    card.addEventListener("click", () => {
      const book = {
        cover: card.dataset.cover,
        title: card.dataset.title,
        authors: card.dataset.authors,
        publisher: card.dataset.publisher,
        pageCount: card.dataset.pages,
        publishedDate: card.dataset.date,
        description: card.dataset.description
      };
      openBookModal(book);
    });
  });
  
}

// Abre/fecha o dropdown
document.addEventListener("click", function(e) {
  const isDropdownButton = e.target.matches(".add-button");
  const dropdowns = document.querySelectorAll(".dropdown");

  dropdowns.forEach(drop => {
    if (drop.contains(e.target)) {
      drop.classList.toggle("open");
    } else {
      drop.classList.remove("open");
    }
  });
});

// Captura o clique nas opções
document.addEventListener("click", function(e) {
  if (e.target.matches(".dropdown-item")) {
    const status = e.target.dataset.status;
    const bookId = e.target.dataset.book;

    // 🚀 Aqui futuramente você manda pro backend via fetch()
    alert(`Livro ${bookId} marcado como: ${status}`);

    // Fecha o menu depois do clique
    e.target.closest(".dropdown").classList.remove("open");
  }
});