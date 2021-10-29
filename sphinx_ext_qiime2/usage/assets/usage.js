window.addEventListener('load', () => {
  showInterface('cli-usage');
});

function showInterface(interfaceName) {
  knownInterfaces = ['artifact-usage', 'cli-usage'];
  if (!knownInterfaces.includes(interfaceName)) { return };
  knownInterfaces.forEach((el) => {
    const hidden = interfaceName !== el;
    document.querySelectorAll(`.${el}`).forEach((el) => el.hidden = hidden);
  });
}
