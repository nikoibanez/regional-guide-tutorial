const query = document.querySelector('#query');
const state = document.querySelector('#state');
const results = document.querySelector('#results');
const count = document.querySelector('#count');
let records = [];

function render() {
  const search = query.value.trim().toLocaleLowerCase();
  const matches = records.filter((item) => {
    const searchable = `${item.name} ${item.city} ${item.category}`.toLocaleLowerCase();
    return (!state.value || item.state === state.value) && searchable.includes(search);
  });
  results.replaceChildren();
  for (const item of matches) {
    const li = document.createElement('li');
    const heading = document.createElement('strong');
    heading.textContent = item.name;
    li.append(heading, document.createTextNode(` — ${item.city}, ${item.state} (${item.category || 'Uncategorized'})`));
    if (item.website) {
      const link = document.createElement('a');
      link.href = item.website;
      link.textContent = ' Website';
      link.rel = 'noopener noreferrer';
      li.append(link);
    }
    results.append(li);
  }
  count.textContent = `${matches.length} of ${records.length} records shown`;
}

async function start() {
  try {
    const response = await fetch('./directory.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    records = await response.json();
    render();
  } catch (error) {
    count.textContent = 'Could not load directory.json. Run build.py and serve over HTTP.';
    console.error(error);
  }
}
query.addEventListener('input', render);
state.addEventListener('change', render);
start();
