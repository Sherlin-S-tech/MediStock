(() => {
  const sidebar = document.getElementById('sidebar');
  const backdrop = document.getElementById('sidebarBackdrop');
  const toggle = document.getElementById('menuToggle');
  const close = () => { sidebar?.classList.remove('open'); backdrop?.classList.remove('visible'); };
  toggle?.addEventListener('click', () => { sidebar?.classList.toggle('open'); backdrop?.classList.toggle('visible'); });
  backdrop?.addEventListener('click', close);
  document.querySelectorAll('form[data-confirm]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });
  document.querySelectorAll('input[type="number"]').forEach((input) => {
    input.addEventListener('input', () => {
      if (input.value !== '' && Number(input.value) < 0) input.setCustomValidity('Enter zero or a positive value.');
      else input.setCustomValidity('');
    });
  });
})();
