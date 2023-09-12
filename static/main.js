let highest_id = 0;
let scrollToBottom = true;

function getColor(value) {
  let hue = ((1 - value) * 120).toString(10);
  return ["hsl(", hue, ",100%,50%)"].join("");
}

async function update_data() {
  let response = await fetch("/interactions");
  let interactions = await response.json();
  for (const i of interactions) {
    if (i.id > highest_id) {
      document.body.append(new Date(i.timestamp * 1000).toLocaleString());
      let d = document.createElement("div")
      d.textContent = i.query;
      document.body.append(d);
      document.body.innerHTML += "...";
      d = document.createElement("div")
      d.textContent = i.response;
      d.style.color = getColor(i.temperature);
      document.body.append(d);
      document.body.append(document.createElement("br"))
    }
  }
  if (interactions.length) {
    highest_id = interactions.at(-1).id;
    if (scrollToBottom) {
      window.scrollTo(0, document.body.scrollHeight);
    }
  }
  setTimeout(update_data, 3000)
}

window.onscroll = function(ev) {
    scrollToBottom = (window.innerHeight + Math.round(window.scrollY)) >= document.body.offsetHeight;
};