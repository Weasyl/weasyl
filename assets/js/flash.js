import {byClass, make} from './dom.js';

// This is inserted into a `<script>` element in the sandbox without escaping.
const RUFFLE_CONFIG_JS = JSON.stringify({
    config: {
        publicPath: location.origin + '/js/ruffle/',
        polyfills: false,
        allowNetworking: 'none',
        autoplay: 'on',
    },
});

// This function is stringified and runs in the sandbox, so it can’t use any module-scoped names.
const SANDBOX_INIT_JS = String(async expectedOrigin => {
    const player = RufflePlayer.newest().createPlayer();
    player.className = 'player';

    document.body.appendChild(player);

    const playCommandP = new Promise(resolve => {
        const onmessage = e => {
            if (e.origin === expectedOrigin) {
                resolve(e.data);
                window.removeEventListener('message', onmessage);
            }
        };

        window.addEventListener('message', onmessage);
    });

    window.parent.postMessage('loaded', expectedOrigin);

    const playCommand = await playCommandP;

    if (playCommand.m_fullscreen) {
        player.ruffle().requestFullscreen();
    }

    player.ruffle().load({
        url: String(playCommand.m_url),
    });
});

const sandboxReady = new Promise(resolve => {
    const onmessage = e => {
        if (e.source === sandbox.contentWindow) {
            resolve();
            window.removeEventListener('message', onmessage);
        }
    };

    window.addEventListener('message', onmessage);
});

// This is inserted into the sandbox’s HTML without escaping. `location.origin` and `RUFFLE_SRC` never contain `"`.
const ruffleUrl = location.origin + RUFFLE_SRC;

const sandbox = make('iframe', {
    className: 'flash-player',
    srcdoc: `<!DOCTYPE html><style>html,body,.player{display:block;width:100%;height:100%;margin:0}</style><script type="module">window.RufflePlayer=${RUFFLE_CONFIG_JS};</script><script type="module" crossorigin="anonymous" src="${ruffleUrl}"></script><script type="module">(${SANDBOX_INIT_JS})('${location.origin}')</script>`,
});

const detailFlash = document.getElementById('detail-flash');

detailFlash.appendChild(sandbox);

sandboxReady.then(() => {
    const play = fullscreen => {
        controls.remove();

        const cover = byClass('flash-cover', detailFlash);
        if (cover) {
            cover.remove();
        }

        sandbox.style.visibility = 'visible';

        sandbox.contentWindow.postMessage({
            m_url: detailFlash.dataset.flashUrl,
            m_fullscreen: Boolean(fullscreen),
        }, '*');
    };

    const playButton = make('button', {
        type: 'button',
        textContent: 'Play Flash animation',
    });

    playButton.addEventListener('click', () => {
        play(false);
    });

    const playFullscreenButton = make('button', {
        type: 'button',
        textContent: 'Play fullscreen',
    });

    playFullscreenButton.addEventListener('click', () => {
        play(true);
    });

    const controls = byClass('flash-controls', detailFlash);
    controls.textContent = '';
    controls.appendChild(make('li')).appendChild(playButton);
    controls.appendChild(make('li')).appendChild(playFullscreenButton);
});
