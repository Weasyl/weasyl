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

        searchFind.toggleClass('last-input', findUser);
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
    searchFind.toggleClass('last-input', find === 'user');
};

const populateNavigationCounts = async () => {
    const searchBack = document.getElementById('search-back');
    const searchNext = document.getElementById('search-next');

    const response = await fetch(`/api-unstable/search/navigation-counts${window.location.search}`);
    const {nextCount, backCount} = await response.json();

    if (backCount > 0) {
        searchBack.innerText += ` (~${backCount} more)`;
    } else {
        searchBack.remove();
    }

    if (nextCount > 0) {
        searchNext.innerText += ` (~${nextCount} more)`;
    } else {
        searchNext.remove();
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
