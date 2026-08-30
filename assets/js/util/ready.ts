
const ready =
    document.readyState === 'loading'
        ? new Promise<void>(resolve => {
            document.addEventListener('DOMContentLoaded', () => {
                resolve();
            });
        })
        : Promise.resolve();

export default ready;


