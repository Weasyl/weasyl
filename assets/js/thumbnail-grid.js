import ready from './util/ready.js';

// Implementation notes:
//
// - Having the actual content be in the shadow DOM would also improve selector performance and avoid the “targeting class” hack, but requires recreating the rest of the thumbnail grid styles there as well.
// - In the current implementation, container queries don’t overlap. Cards above a wrap point never change, though; rules could be shared at the row level between larger ranges of widths. It might be worth investigating whether the reduced number of rules improves performance or the increased number of matching rules or container queries harms performance.

const MIN_WIDTH = 125;   // minimum width per cell (should match min thumbnail width)
const ROW_BASIS = 250;   // row height basis (should match max thumbnail height)
const ITEM_GAP = 8;      // common item padding
const BREAKPOINT = 480;  // when the viewport is narrower than this, double the maximum number of rows

// The minimum thumbnail grid container width to generate a layout for, in `px`.
const CONTAINER_WIDTH_MIN = 420;

// The maximum thumbnail grid container width to generate a layout for, in `px`.
// (See `#page-container`’s `max-width` in site.scss.)
const CONTAINER_WIDTH_MAX = 1650;

// The minimum width difference between distinct layouts, in `px`.
const STEP_MIN = 125;

const getWidth = width =>
    width ? Math.max(width, MIN_WIDTH) : null;

let uniqueClassCounter = 0;
const nextUniqueClass = () => `_Tg${++uniqueClassCounter}`;

/* TODO: test cases, if this code or an equivalent still exists once we get to frontend testing
 *
 * - thumbnails with a natural height less than `ROW_BASIS`
 * - " making up an entire row
 * - thumbnails narrower than `MIN_WIDTH` and taller than `ROW_BASIS`
 * - thumbnails with and without WebP (or future alternative formats. note: `<picture>` is not `display: contents`)
 * - thumbnails of various sizes without dimension information
 * - default thumbnails for each category
 */

const getLayout = (footprint, thumbnailWidths, containerWidth) => {
    // TODO: target a specific number of thumbnails for each footprint instead of making a sharp jump
    let maxRows =
        containerWidth <= BREAKPOINT
            ? footprint.m_maxRowsNarrow
            : footprint.m_maxRowsWide;

    const row = [];
    let rowWidth = ITEM_GAP;

    const rules = [];
    let rowLimited = false;

    const commitRow = () => {
        const totalGap = (row.length + 1) * ITEM_GAP;
        const nonGapWidth = rowWidth - totalGap;

        const rowSelector =
            `&:nth-child(n+${1 + row[0].m_index})`
            + `:nth-child(-n+${1 + row.at(-1).m_index})`;

        rules.push(`${rowSelector}{--g:${totalGap};--h:${(ROW_BASIS / nonGapWidth).toFixed(4)}}`);

        row.length = 0;
        rowWidth = ITEM_GAP;
    };

    // Determines how much narrower the container could get without changing the computed layout.
    let maxNonWrappingRowWidth = 0;

    for (let [i, naturalWidth] of thumbnailWidths.entries()) {
        naturalWidth ??= ROW_BASIS;
        const oldRowWidth = rowWidth;
        rowWidth += naturalWidth + ITEM_GAP;
        row.push({
            m_index: i,
            m_width: naturalWidth,
        });

        if (rowWidth >= containerWidth) {
            maxNonWrappingRowWidth = Math.max(maxNonWrappingRowWidth, oldRowWidth);

            commitRow();

            // If a row limit was specified and we reached it, hide the remaining thumbnails.
            if (--maxRows === 0 && i + 1 < thumbnailWidths.length) {
                rules.push(`&:nth-child(n+${2 + i}){display:none}`);
                rowLimited = true;
                break;
            }
        }
    }

    if (row.length !== 0) {
        // The last element in this leftover row didn’t cause a wrap – that’s why it’s left over. Once the container becomes narrow enough for this element to cause a wrap, the layout still doesn’t change; it’s only once the *previous* element causes a wrap.
        maxNonWrappingRowWidth = Math.max(maxNonWrappingRowWidth, rowWidth - (row.at(-1).m_width + ITEM_GAP));

        // Style the leftovers to ensure that they never wrap, even when this layout is used at a narrower-than-intended size. `$thumbnail-grid-max-height` prevents them from stretching.
        commitRow();
    }

    let isHardMinWidth = false;

    // If passing the breakpoint would result in more rows becoming visible, don’t claim that this layout is valid past the breakpoint.
    if (
        rowLimited
        && maxNonWrappingRowWidth <= BREAKPOINT
        && containerWidth > BREAKPOINT
        && footprint.m_maxRowsNarrow > footprint.m_maxRowsWide
    ) {
        maxNonWrappingRowWidth = BREAKPOINT + 1;
        isHardMinWidth = true;
    }

    return {
        m_rules: rules,
        m_minWidth: maxNonWrappingRowWidth,
        m_isHardMinWidth: isHardMinWidth,
    };
};

const layout = (container, stylesheet, targetingClass) => {
    let footprint = {m_maxRowsNarrow: 0, m_maxRowsWide: 0};
    if (container.classList.contains('tiny-footprint')) {
        footprint = {m_maxRowsNarrow: 1, m_maxRowsWide: 1};
    } else if (container.classList.contains('small-footprint')) {
        footprint = {m_maxRowsNarrow: 2, m_maxRowsWide: 1};
    } else if (container.classList.contains('medium-footprint')) {
        footprint = {m_maxRowsNarrow: 4, m_maxRowsWide: 2};
    }

    const thumbnailWidths = container.dataset.widths.split(',').map(getWidth);

    // Generate layouts at various widths from `CONTAINER_WIDTH_MAX` down to `CONTAINER_WIDTH_MIN`. Wider layouts can apply to narrower viewports than intended, but not the other way around (typical thumbnails should never be stretched or be centered in wider containers).
    const layouts = [];

    for (let containerWidth = CONTAINER_WIDTH_MAX; containerWidth >= CONTAINER_WIDTH_MIN;) {
        const layout = getLayout(footprint, thumbnailWidths, containerWidth);
        layouts.push({
            m_maxWidth: containerWidth,
            m_rules: layout.m_rules,
        });

        containerWidth -= STEP_MIN;

        if (layout.m_minWidth - 1 <= containerWidth) {
            containerWidth = layout.m_minWidth - 1;
        } else if (layout.m_isHardMinWidth) {
            // Breakpoint happened within `STEP_MIN` of the previous layout, so just discard the previous layout. (As long as `BREAKPOINT + STEP_MIN < CONTAINER_WIDTH_MAX`, this won’t break anything.)
            layouts.length--;
            containerWidth = layout.m_minWidth - 1;
        }
    }

    let css = `.${targetingClass} > .item {`;

    for (const [i, naturalWidth] of thumbnailWidths.entries()) {
        css += `&:nth-child(${1 + i}){--r:${((naturalWidth ?? ROW_BASIS) / ROW_BASIS).toFixed(4)}}`;
    }

    for (const [i, layout] of layouts.entries()) {
        const queries = [];

        if (i > 0) {
            queries.push(`(width <= ${layout.m_maxWidth}px)`);
        }

        if (i + 1 < layouts.length) {
            const narrowerLayout = layouts[i + 1];
            queries.push(`(width > ${narrowerLayout.m_maxWidth}px)`);
        }

        const rules = layout.m_rules.join('');

        if (queries.length) {
            css += `@container ${queries.join(' and ')} {${rules}}`;
        } else {
            css += rules;
        }
    }

    stylesheet.replaceSync(css);
};

const initialize = container => {
    const targetingClass = nextUniqueClass();
    const stylesheet = new CSSStyleSheet();

    document.adoptedStyleSheets.push(stylesheet);
    container.classList.add(targetingClass);

    layout(container, stylesheet, targetingClass);
    container.classList.add('thumbnail-grid-enhanced');
};

class ThumbnailGrid extends HTMLUListElement {
    connectedCallback() {
        initialize(this);
    }
}

const defineThumbnailGrid = () => {
    // This implementation of enhanced thumbnails requires support for CSS nesting and container size queries. There don’t seem to have been any browser versions that supported CSS nesting but not container size queries, so just check for the former.
    if (!CSS.supports('selector(&)')) {
        return;
    }

    customElements.define('thumbnail-grid', ThumbnailGrid, {extends: 'ul'});

    ready.then(() => {
        const grids = document.getElementsByClassName('thumbnail-grid');

        if (grids[0] && !(grids[0] instanceof ThumbnailGrid)) {
            // Give enhanced thumbnail layout to supported browsers that don’t support customized built-in elements (i.e. just Safari).
            for (const grid of grids) {
                initialize(grid);
            }
        }
    });
};

export default defineThumbnailGrid;
