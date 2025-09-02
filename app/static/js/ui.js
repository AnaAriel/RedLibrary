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

  function openBookModal(card) {
    // Sempre preenche as informações básicas do livro
    modalCover.src = card.dataset.cover;
    modalTitle.textContent = card.dataset.title;
    modalAuthor.textContent = card.dataset.authors;
    modalDesc.textContent = card.dataset.description || "Sem descrição disponível";
    
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
        ratingInput.value = card.dataset.rating || 0;
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