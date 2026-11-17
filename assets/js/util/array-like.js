export const forEach = (list, callback) => {
    for (let i = 0, l = list.length; i < l; i++) {
        callback(list[i]);
    }
};

export const some = (list, predicate) => {
    for (let i = 0, l = list.length; i < l; i++) {
        if (predicate(list[i])) {
            return true;
        }
    }

    return false;
};
