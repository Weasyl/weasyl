const ready =
    document.readyState === 'loading'
        ? new Promise(resolve => {
            document.addEventListener('DOMContentLoaded', () => {
                resolve();
            });
        })
        : Promise.resolve();

export default ready;
