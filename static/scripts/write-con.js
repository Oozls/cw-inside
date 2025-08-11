let imgUrls = {
    "none":[]
}

fetch("/static/img/emoticon/touhou1.json")
    .then(response => response.json())
    .then(data => imgUrls = {...imgUrls, ...{'touhou1':data}})
    .catch(error => console.error('이모티콘 Url 로딩 중 에러 발생', error));

const gridContainer = document.getElementById('con_img_cell');
const select = document.getElementById('con_select');
const content = document.getElementsByClassName('toastui-editor-contents')[0];

function renderImages(category) {
    gridContainer.innerHTML = "";
    if (category == "none") {
        gridContainer.style = "position: absolute; height: 0; opacity: 0;"
    } else {
        gridContainer.style = "position: relative; height: auto; opacity: 1;"
    }
    imgUrls[category].forEach(url => {
        const img = document.createElement('img');

        img.src = url;
        img.className = "con_img";
        img.addEventListener('click', () => {
            const copyImg = img.cloneNode(true);
            editor.appendChild(copyImg)
        });

        gridContainer.appendChild(img);
    });
}

select.addEventListener('change', () => {
    renderImages(select.value);
});

gridContainer.style = "position: absolute; height: 0; opacity: 0;"
renderImages(select.value);