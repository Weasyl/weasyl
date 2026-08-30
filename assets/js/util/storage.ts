
const logStorageError = error => {
    try {
        console.warn(error);
    } catch (_consoleError) { /* ignore */ }
};

export const trySetLocal = (key, value) => {
    try {
        localStorage.setItem(key, value);
    } catch (error) {
        logStorageError(error);
    }
};

export const tryGetLocal = key => {
    try {
        return localStorage.getItem(key);
    } catch (error) {
        logStorageError(error);
        return null;
    }
};


