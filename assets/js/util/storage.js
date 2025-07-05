var logStorageError = error => {
    try {
        console.warn(error);
    } catch (_consoleError) {}
};

export var trySetLocal = (key, value) => {
    try {
        localStorage.setItem(key, value);
    } catch (error) {
        logStorageError(error);
    }
};

export var tryGetLocal = key => {
    try {
        return localStorage.getItem(key);
    } catch (error) {
        logStorageError(error);
        return null;
    }
};
