(function () {
    'use strict';

    var searchFind = $('#search-find');
    var searchCategory = $('#search-cat');
    var searchSubcategory = $('#search-subcat');
    var searchCategoryContainer = $('#search-cat-container');
    var searchSpecsContainer = $('#search-specs-container');
    var find = searchFind.val();

    if (!searchFind.length) {
        return;
    }

    searchFind.on('change', function updateSearchCategories() {
        var find = searchFind.val();
        var findUser = find === 'user';

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

    searchCategory.on('change', function clearSubcategory() {
        searchSubcategory.val('');
    });

    searchSubcategory.on('change', function updateCategory() {
        var subcategory = searchSubcategory.val();

        if (subcategory) {
            searchCategory.val(subcategory.charAt(0) + '000');
        }
    });

    searchCategoryContainer.toggle(find === 'submit');
    searchSpecsContainer.toggle(find !== 'user');
    searchFind.toggleClass('last-input', find === 'user');
})();
