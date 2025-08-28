document.addEventListener("DOMContentLoaded", () => {
    const video = document.getElementById("video");
    const channelList = document.getElementById("channel-list");

    // Загрузка списка каналов
    fetch("channels.json")
        .then(res => res.json())
        .then(channels => {
            channels.forEach((channel, index) => {
                const li = document.createElement("li");
                li.dataset.url = channel.url;
                li.dataset.name = channel.name;

                const img = document.createElement("img");
                img.src = channel.logo || "https://via.placeholder.com/32";
                img.alt = channel.name;

                const span = document.createElement("span");
                span.textContent = channel.name;

                li.appendChild(img);
                li.appendChild(span);
                channelList.appendChild(li);

                li.onclick = () => playChannel(channel.url, channel.name);
            });

            // Автозапуск первого канала
            if (channels.length > 0) {
                playChannel(channels[0].url, channels[0].name);
            }

            // Выделение первого
            if (channelList.children[0]) {
                channelList.children[0].classList.add("active");
            }
        })
        .catch(err => {
            console.error("Ошибка загрузки channels.json", err);
            alert("Не удалось загрузить список каналов");
        });

    function playChannel(url, name) {
        if (video.src) video.src = "";
        video.src = url;
        video.load();
        video.play();
        document.title = name;

        // Снимаем и добавляем active
        document.querySelectorAll("#channel-list li").forEach(li => {
            li.classList.remove("active");
        });
        const items = channelList.children;
        for (let i = 0; i < items.length; i++) {
            if (items[i].dataset.url === url) {
                items[i].classList.add("active");
                break;
            }
        }
    }

    // Управление с пульта
    let selectedIndex = 0;
    document.addEventListener("keydown", (e) => {
        const items = channelList.children;
        if (!items.length) return;

        switch (e.keyCode) {
            case 38: // Вверх
                if (selectedIndex > 0) selectedIndex--;
                break;
            case 40: // Вниз
                if (selectedIndex < items.length - 1) selectedIndex++;
                break;
            case 13: // OK
                const url = items[selectedIndex].dataset.url;
                const name = items[selectedIndex].dataset.name;
                playChannel(url, name);
                return;
            default:
                return;
        }
        // Прокрутка и подсветка
        items.forEach((item, i) => item.classList.toggle("active", i === selectedIndex));
        items[selectedIndex].scrollIntoView({ block: "center" });
    });
});