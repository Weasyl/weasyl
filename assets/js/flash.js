import {byClass, make} from './dom.js';

const detailFlash = document.getElementById('detail-flash');

const player = RufflePlayer.newest().createPlayer();
player.className = 'flash-player';

detailFlash.appendChild(player);

const play = () => {
    controls.remove();

    const cover = byClass('flash-cover', detailFlash);
    if (cover) {
        cover.remove();
    }

    player.style.visibility = 'visible';

    player.ruffle().load({
        url: detailFlash.dataset.flashUrl,
    });
};

const playButton = make('button', {
    type: 'button',
    textContent: 'Play Flash animation',
});

playButton.addEventListener('click', play);

const playFullscreenButton = make('button', {
    type: 'button',
    textContent: 'Play fullscreen',
});

playFullscreenButton.addEventListener('click', () => {
    player.ruffle().requestFullscreen();
    play();
});

const controls = byClass('flash-controls', detailFlash);
controls.textContent = '';
controls.appendChild(make('li')).appendChild(playButton);
controls.appendChild(make('li')).appendChild(playFullscreenButton);
