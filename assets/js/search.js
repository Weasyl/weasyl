const animateSearchSettings = () => {
    const searchFind = $('#search-find');

    if (!searchFind.length) {
        return;
    }

    const searchCategory = $('#search-cat');
    const searchSubcategory = $('#search-subcat');
    const searchCategoryContainer = $('#search-cat-container');
    const searchSpecsContainer = $('#search-specs-container');
    const find = searchFind.val();

    searchFind.on('change', () => {
        const find = searchFind.val();
        const findUser = find === 'user';

        if (find === 'submit') {
            searchCategoryContainer.show(300);
        } else {
            searchCategoryContainer.hide(300);
        }

        if (findUser) {
            searchSpecsContainer.hide(300);
        } else {
            searchSpecsContainer.show(300);
        }
    });

    searchCategory.on('change', () => {
        searchSubcategory.val('');
    });

    searchSubcategory.on('change', () => {
        const subcategory = searchSubcategory.val();

        if (subcategory) {
            searchCategory.val(subcategory.charAt(0) + '000');
        }
    });

    searchCategoryContainer.toggle(find === 'submit');
    searchSpecsContainer.toggle(find !== 'user');

    searchCategoryContainer.add(searchSpecsContainer)
        .children('legend')
        .remove();
};

const displayNavigationCount = (element, count) => {
    if (count === 10000) {
        element.innerText += ' (10k+ more)';
    } else if (count >= 1000) {
        element.innerText += ` (~${count / 1000}k more)`;
    } else if (count >= 100) {
        element.innerText += ` (~${count} more)`;
    } else if (count > 0) {
        element.innerText += ` (${count} more)`
    } else {
        element.remove();
    }
};

const setOrDelete = (map, key, value) => {
    if (value == null) {
        map.delete(key);
    } else {
        map.set(key, value);
    }
};

const populateNavigationCounts = async () => {
    const searchBack = document.getElementById('search-back');
    const searchNext = document.getElementById('search-next');

    const params = new URLSearchParams(window.location.search);

    const backid = searchBack && new URL(searchBack.href).searchParams.get('backid');
    const nextid = searchNext && new URL(searchNext.href).searchParams.get('nextid');

    setOrDelete(params, 'backid', backid);
    setOrDelete(params, 'nextid', nextid);

    const response = await fetch(`/api-unstable/search/navigation-counts?${params}`);
    if (!response.ok) {
        return;
    }

    const {nextCount, backCount} = await response.json();

    if (searchBack) {
        displayNavigationCount(searchBack, backCount);
    }

    if (searchNext) {
        displayNavigationCount(searchNext, nextCount);
    }
};

animateSearchSettings();

const searchNav = document.getElementById('search-nav');

if (searchNav) {
    const observer = new IntersectionObserver(entries => {
        if (entries.some(entry => entry.isIntersecting)) {
            populateNavigationCounts();
            observer.unobserve(searchNav);
        }
    });

    observer.observe(searchNav);
}
