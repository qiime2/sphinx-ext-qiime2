KNOWN_INTERFACES = {
  'cli-usage': 'q2cli',
  'artifact-usage': 'Artifact API',
};

window.addEventListener('load', () => {
  showInterface(Object.keys(KNOWN_INTERFACES)[0]);

  const firstUsageBlock = document.getElementById('usage-0');
  const interfaceSelect = document.createElement('select');
  interfaceSelect.addEventListener('change', (e) => showInterface(e.target.value));

  for (const [value, text] of Object.entries(KNOWN_INTERFACES)) {
    const opt = document.createElement('option');
    opt.value = value;
    opt.text = text;
    interfaceSelect.appendChild(opt);
  };

  firstUsageBlock.parentElement.querySelector('h1:first-of-type').after(interfaceSelect);
});

function showInterface(interfaceName) {
  const knownInterfaceKeys = Object.keys(KNOWN_INTERFACES);
  if (!knownInterfaceKeys.includes(interfaceName)) { return };
  knownInterfaceKeys.forEach((el) => {
    const hidden = interfaceName !== el;
    document.querySelectorAll(`.${el}`).forEach((el) => el.hidden = hidden);
  });
}
