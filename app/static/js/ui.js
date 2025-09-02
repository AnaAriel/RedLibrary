// static/js/ui.js

const btnProfile = document.getElementById('btn-profile');
const menuProfile = document.getElementById('menu-profile');

if (btnProfile && menuProfile) {
  btnProfile.addEventListener('click', () => {
    menuProfile.classList.toggle('open');
  });

  document.addEventListener('click', (e) => {
    const clickedInside = btnProfile.contains(e.target) || menuProfile.contains(e.target);
    if (!clickedInside) menuProfile.classList.remove('open');
  });
}

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

// ===== MODAL DE DETALHES (LÓGICA ATUALIZADA) =====
const modal = document.getElementById("book-modal");
// Em static/js/ui.js
if (modal) {
  const modalClose = document.querySelector(".modal-close");
  const modalCover = document.getElementById("modal-cover");
  const modalTitle = document.getElementById("modal-title");
  const modalAuthor = document.getElementById("modal-author");
  const modalPublisher = document.getElementById("modal-publisher");
  const modalPages = document.getElementById("modal-pages");
  const modalDate = document.getElementById("modal-date");
  const modalDesc = document.getElementById("modal-description");
  
  // Elementos do formulário do modal da estante
  const updateForm = document.getElementById("update-form");
  const deleteForm = document.getElementById("delete-form");
  const statusSelect = document.getElementById("shelf-status");
  const ratingInput = document.getElementById("rating-value");
  
  // Pega os elementos das estrelas do modal
  const starRatingContainer = document.getElementById("star-rating");
  // Só executa o código das estrelas se o container existir (para não dar erro na home)
  if (starRatingContainer) {
    const stars = starRatingContainer.querySelectorAll(".star");

    // Função "ajudante" para pintar a quantidade correta de estrelas
    function updateStars(rating) {
      stars.forEach(star => {
        star.classList.toggle('selected', star.dataset.value <= rating);
      });
    }

    // Adiciona um evento de clique para cada estrela
    stars.forEach(star => {
      star.addEventListener('click', () => {
        const ratingValue = star.dataset.value;
        // Atualiza o valor no campo escondido
        ratingInput.value = ratingValue;
        // Atualiza o visual das estrelas
        updateStars(ratingValue);
      });
    });
  }

  function openBookModal(card) {
    // Sempre preenche as informações básicas do livro
    modalCover.src = card.dataset.cover;
    modalTitle.textContent = card.dataset.title;
    modalAuthor.textContent = card.dataset.authors;
    
    // As verificações abaixo garantem que o JS não quebre na página que não tem esses spans
    if(modalDesc) modalDesc.textContent = card.dataset.description || "Sem descrição disponível";
    if (modalPublisher) modalPublisher.textContent = card.dataset.publisher || "—";
    if (modalPages) modalPages.textContent = card.dataset.pages || "—";
    if (modalDate) modalDate.textContent = card.dataset.date || "—";
    
    const userBookId = card.dataset.userBookId;
    if (userBookId && updateForm && deleteForm) {
        updateForm.style.display = "block";
        deleteForm.style.display = "block";

        updateForm.action = `/shelf/update/${userBookId}`;
        deleteForm.action = `/shelf/delete/${userBookId}`;

        statusSelect.value = card.dataset.status;
        
        // --- LINHAS ATUALIZADAS AQUI ---
        // Pega a avaliação atual do card
        const currentRating = parseInt(card.dataset.rating, 10) || 0;
        // Atualiza o campo escondido com o valor atual
        ratingInput.value = currentRating;
        // Chama a função para pintar a quantidade correta de estrelas ao abrir o modal
        if (starRatingContainer) { // Garante que a função só seja chamada se as estrelas existirem
          updateStars(currentRating);
        }
        
    } else if (updateForm && deleteForm) {
        updateForm.style.display = "none";
        deleteForm.style.display = "none";
    }

    modal.style.display = "flex";
  }

  modalClose.addEventListener("click", () => modal.style.display = "none");
  window.addEventListener("click", (e) => {
    if (e.target === modal) modal.style.display = "none";
  });

  document.querySelectorAll(".card").forEach(card => {
    card.addEventListener("click", () => {
        openBookModal(card);
    });
  });
}

// Abre/fecha o dropdown de "Adicionar"
document.addEventListener("click", function(e) {
  const isDropdownButton = e.target.matches(".add-button");
  
  if (!isDropdownButton && e.target.closest('.dropdown') != null) return;

  let currentDropdown;
  if(isDropdownButton) {
      currentDropdown = e.target.closest('.dropdown');
      currentDropdown.classList.toggle('open');
  }

  document.querySelectorAll(".dropdown.open").forEach(dropdown => {
      if(dropdown === currentDropdown) return;
      dropdown.classList.remove('open');
  });
});

// =======================================================
// ========= LÓGICA DE FILTRO E ORDENAÇÃO DA ESTANTE =========
// =======================================================
document.addEventListener('DOMContentLoaded', () => {
  // Só executa este código se estivermos na página da estante
  const shelfControls = document.querySelector('.shelf-controls');
  if (!shelfControls) {
    return;
  }

  const controlButtons = shelfControls.querySelectorAll('.control-btn');
  const searchInput = document.getElementById('shelf-search-input');
  const grid = document.querySelector('.grid');
  // Pega todos os cards e transforma em um array para poder ordenar
  const bookCards = Array.from(grid.querySelectorAll('.card'));

  // --- LÓGICA DE FILTRAGEM (Status: Lido, Lendo, etc.) ---
  function filterBooks(filterValue) {
    bookCards.forEach(card => {
      const cardStatus = card.dataset.status;
      
      if (filterValue === 'all' || cardStatus === filterValue) {
        card.style.display = 'block'; // Mostra o card
      } else {
        card.style.display = 'none'; // Esconde o card
      }
    });
  }

  // --- LÓGICA DE ORDENAÇÃO (A-Z, Autor, etc.) ---
  function sortBooks(sortValue) {
    const [sortBy, sortDir] = sortValue.split('-'); // Ex: 'title-asc' -> ['title', 'asc']

    bookCards.sort((a, b) => {
      // Pega o valor do data-attribute (ex: data-title, data-authors)
      const valA = a.dataset[sortBy] ? a.dataset[sortBy].toLowerCase() : '';
      const valB = b.dataset[sortBy] ? b.dataset[sortBy].toLowerCase() : '';

      if (sortDir === 'asc') {
        return valA.localeCompare(valB); // Compara strings de A-Z
      } else {
        return valB.localeCompare(valA); // Compara strings de Z-A
      }
    });

    // Limpa o grid e adiciona os cards na nova ordem
    grid.innerHTML = '';
    bookCards.forEach(card => grid.appendChild(card));
  }
  
  // --- LÓGICA DA BUSCA LOCAL ---
  function searchOnShelf(searchTerm) {
    const term = searchTerm.toLowerCase();
    bookCards.forEach(card => {
      const title = card.dataset.title.toLowerCase();
      const authors = card.dataset.authors.toLowerCase();
      
      if (title.includes(term) || authors.includes(term)) {
        card.style.display = 'block';
      } else {
        card.style.display = 'none';
      }
    });
  }

  // --- ADICIONA OS EVENTOS NOS BOTÕES ---
  controlButtons.forEach(button => {
    button.addEventListener('click', () => {
      // Estilo do botão ativo
      controlButtons.forEach(btn => btn.classList.remove('active'));
      button.classList.add('active');
      
      const filter = button.dataset.filter;
      const sort = button.dataset.sort;

      if (filter) {
        filterBooks(filter);
      } else if (sort) {
        sortBooks(sort);
      }
    });
  });
  
  // --- ADICIONA O EVENTO NA BARRA DE BUSCA ---
  searchInput.addEventListener('input', (e) => {
    searchOnShelf(e.target.value);
  });
});