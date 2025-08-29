// ====== DROPDOWN DO PERFIL ======
const btnProfile = document.getElementById('btn-profile'); // Obtém o botão do perfil pelo ID
const menuProfile = document.getElementById('menu-profile'); // Obtém o menu suspenso do perfil

if (btnProfile && menuProfile) { // Verifica se os elementos existem na página
  btnProfile.addEventListener('click', () => { // Adiciona evento de clique ao botão
    menuProfile.classList.toggle('open'); // Alterna a classe 'open' para mostrar/ocultar o menu
  }); // Fim do clique

  document.addEventListener('click', (e) => { // Captura cliques no documento
    const clickedInside = btnProfile.contains(e.target) || menuProfile.contains(e.target); // Verifica se clicou dentro do perfil
    if (!clickedInside) menuProfile.classList.remove('open'); // Se clicou fora, fecha o menu
  }); // Fim do listener global
} // Fim da verificação

// ====== CHECKBOXES EXCLUSIVAS (TÍTULO x AUTOR) ======
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

  // estado inicial coerente
  enforceExclusive(chkAuthor?.checked ? chkAuthor : chkTitle);
}
