/**
 * Client-side video embedding support; currently only for Bluesky.
 */
import Hls from 'hls.js';

export const loadBlueskyVideo = () => {
    const video = document.getElementById('bsky-video');

    if (!video) {
        return;
    }

    const hls = new Hls();

    hls.on(Hls.Events.ERROR, (event, data) => {
        if (data.fatal) {
            console.error(data);
            const errorMessage = document.getElementById('video-error');
            errorMessage.hidden = false;

            // Opting not to hls.destroy() in case the fatal error happened
            // mid-stream, and the user still wants to be able to rewind to
            // an earlier part of the video that loaded okay.
        }
    });

    hls.loadSource(video.src);
    hls.attachMedia(video);
};
