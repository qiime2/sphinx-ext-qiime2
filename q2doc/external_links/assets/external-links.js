window.addEventListener('load', () => {
  document.querySelectorAll('a.reference.external').forEach((link) => {
    link.target = '_blank';
  });
});
