import parseTags from './parse-tags.js';
import {byClass, make} from './dom.js';

const animateFlash = (element, color) => {
    element.animate([{color}, {}], {duration: 500});
};

const hasSuccessStatus = ({status}) =>
    200 <= status && status < 300;

// The time before showing an in-progress indicator for a background save action, in milliseconds.
// Makes it less distracting by reducing the number of status updates when the response comes back fast enough.
const SAVE_PROGRESS_DELAY = 500;

// see `weasyl.searchtag.UNDO_TOKEN_VALIDITY`
const UNDO_TOKEN_VALIDITY = 60;

const SUCCESS_COLOR = 'green';
const FAILURE_COLOR = '#e30';

const ACTION_BUTTONS = Symbol();
const UNDO_TOKEN = Symbol();
const UNDO_EXPIRE_TIMER = Symbol();

class StatusReporter {
    #display;
    #progressDelayTimer;

    constructor(display) {
        this.#display = display;
    }

    m_start() {
        this.#progressDelayTimer = setTimeout(this.#display.m_showProgress, SAVE_PROGRESS_DELAY);
    }

    m_reportSuccess(...args) {
        clearTimeout(this.#progressDelayTimer);
        this.#display.m_stopProgress();
        this.#display.m_showSuccess(...args);
    }

    m_reportFailure() {
        clearTimeout(this.#progressDelayTimer);
        this.#display.m_stopProgress();
        this.#display.m_showFailure();
    }
}

const undoTagAction = (target, tag, actionsFieldset) => {
    const reporter = new StatusReporter({
        m_showProgress: () => {
            actionsFieldset.classList.add('tag-form-status-saving');
            actionsFieldset.textContent = 'Undoing…';
        },
        m_stopProgress: () => {
            actionsFieldset.classList.remove('tag-form-status-saving');
        },
        m_showSuccess: () => {
            actionsFieldset.disabled = false;
            actionsFieldset.textContent = '';
            actionsFieldset.appendChild(actionsFieldset[ACTION_BUTTONS]);
            actionsFieldset[ACTION_BUTTONS] = null;
        },
        m_showFailure: () => {
            actionsFieldset[ACTION_BUTTONS] = null;
            actionsFieldset.textContent = 'Error.';
            animateFlash(actionsFieldset, FAILURE_COLOR);
        },
    });

    actionsFieldset.disabled = true;

    fetch(`/api-unstable/tag-suggestions/${target}/${tag}/status`, {
        method: 'DELETE',
        body: actionsFieldset[UNDO_TOKEN],
    })
        .then((response) => {
            if (!hasSuccessStatus(response)) {
                return Promise.reject({});
            }

            reporter.m_reportSuccess();
        })
        .catch((err) => {
            reporter.m_reportFailure();
            return Promise.reject(err);
        });

    clearTimeout(actionsFieldset[UNDO_EXPIRE_TIMER]);
    actionsFieldset[UNDO_TOKEN] = null;
    actionsFieldset[UNDO_EXPIRE_TIMER] = null;
};

const applyTagAction = (target, tag, actionsFieldset, isApproveAction) => {
    const storeActionButtons = () => {
        if (!actionsFieldset[ACTION_BUTTONS]) {
            const actionButtons = actionsFieldset[ACTION_BUTTONS] = document.createDocumentFragment();
            actionButtons.append(...actionsFieldset.children);
        }
    };

    const reporter = new StatusReporter({
        m_showProgress: () => {
            storeActionButtons();
            actionsFieldset.classList.add('tag-form-status-saving');
            actionsFieldset.textContent = `${isApproveAction ? 'Approv' : 'Reject'}ing…`;
        },
        m_stopProgress: () => {
            actionsFieldset.classList.remove('tag-form-status-saving');
        },
        m_showSuccess: (canUndo) => {
            storeActionButtons();

            const undoButton = make('button', {
                className: 'link-button',
                textContent: 'Undo',
            });
            undoButton.dataset.tagAction = 'undo';

            actionsFieldset.disabled = false;
            actionsFieldset.textContent = `Suggestion ${isApproveAction ? 'approv' : 'reject'}ed. `;

            if (canUndo) {
                actionsFieldset.appendChild(undoButton);

                actionsFieldset[UNDO_EXPIRE_TIMER] = setTimeout(() => {
                    undoButton.remove();
                }, UNDO_TOKEN_VALIDITY * 1000);
            }
        },
        m_showFailure: () => {
            actionsFieldset[ACTION_BUTTONS] = null;
            actionsFieldset.textContent = 'Error.';  // don’t imply that the action definitely didn’t go through; prompt refresh at user’s convenience
            animateFlash(actionsFieldset, FAILURE_COLOR);
        },
    });

    actionsFieldset.disabled = true;

    fetch(`/api-unstable/tag-suggestions/${target}/${tag}/status`, {
        method: 'PUT',
        body: isApproveAction ? 'approve' : 'reject',
    })
        .then(async (response) => {
            if (!hasSuccessStatus(response)) {
                return Promise.reject({});
            }

            const body = new Uint8Array(await response.arrayBuffer());
            const canUndo = body.length > 1;

            if (canUndo) {
                actionsFieldset[UNDO_TOKEN] = body.slice(1);
            }

            reporter.m_reportSuccess(canUndo);
        })
        .catch((err) => {
            reporter.m_reportFailure();
            return Promise.reject(err);
        });
};

const tagsWithActions = byClass('tags-with-actions');
const {tagEditType} = tagsWithActions.dataset;

if (tagEditType !== 'none') {
    const manage = byClass('tags-manage');
    const tagsField = byClass('tags-form', manage).elements.tags;

    // `.tag-actions` only exists when there is already an action, so create it if necessary
    let tagActions = tagsWithActions.lastElementChild;
    if (!tagActions.classList.contains('tag-actions')) {
        tagActions = tagsWithActions.appendChild(make('span', {
            className: 'tag-actions',
        }));
    }

    const editButton = make('button', {
        type: 'button',
        className: 'link-button',
        textContent: tagEditType === 'edit' ? 'Edit tags' : '+ Suggest tags',
    });

    editButton.addEventListener('click', () => {
        manage.hidden = !manage.hidden;

        if (!manage.hidden) {
            tagsField.focus();
        }
    });

    tagActions.insertAdjacentElement('afterbegin', editButton);

    if (tagEditType === 'edit') {
        const tagRejectFeedback = byClass('tag-reject-feedback');
        const statusOutput = byClass('tag-reject-feedback-status', tagRejectFeedback);
        let activeTag = null;
        let abortController = null;

        const feedbackReporter = new StatusReporter({
            m_showProgress: () => {
                statusOutput.classList.add('tag-form-status-saving');
                statusOutput.value = 'Saving…';
            },
            m_stopProgress: () => {
                statusOutput.classList.remove('tag-form-status-saving');
            },
            m_showSuccess: () => {
                statusOutput.value = 'Feedback saved.';
                animateFlash(statusOutput, SUCCESS_COLOR);
            },
            m_showFailure: () => {
                statusOutput.value = 'Error saving feedback.';
                animateFlash(statusOutput, FAILURE_COLOR);
            },
        });

        tagRejectFeedback.addEventListener('change', () => {
            if (abortController !== null) {
                abortController.abort();
            }
            abortController = new AbortController();

            fetch(`/api-unstable/tag-suggestions/${tagRejectFeedback.dataset.target}/${activeTag}/feedback`, {
                method: 'PUT',
                body: new URLSearchParams(new FormData(tagRejectFeedback)),
                signal: abortController.signal,
            })
                .then((response) => {
                    if (!hasSuccessStatus(response)) {
                        return Promise.reject({});
                    }

                    feedbackReporter.m_reportSuccess();
                })
                .catch((err) => {
                    if (err.name !== 'AbortError') {
                        feedbackReporter.m_reportFailure();
                        return Promise.reject(err);
                    }
                });
            feedbackReporter.m_start();
        });

        byClass('suggested-tags', manage).addEventListener('click', (e) => {
            const {tagAction} = e.target.dataset;

            if (!tagAction) {
                return;
            }

            const actionsFieldset = e.target.parentNode;
            const {tag} = actionsFieldset.parentNode.dataset;
            const {target} = tagRejectFeedback.dataset;

            switch (tagAction) {
                case 'approve':
                    if (!parseTags(tagsField.value).includes(tag)) {
                        tagsField.value += (/(?:^|\s)$/.test(tagsField.value) ? '' : ' ') + tag;
                    }

                    applyTagAction(target, tag, actionsFieldset, true);
                    tagRejectFeedback.hidden = true;
                    break;

                case 'reject':
                    activeTag = tag;
                    Object.assign(byClass('tag-suggested', tagRejectFeedback), {
                        textContent: tag,
                        href: `/search?q=${tag}`,
                    });

                    applyTagAction(target, tag, actionsFieldset, false);

                    // TODO: is resetting `<output>` value reliable across browsers?
                    tagRejectFeedback.reset();
                    tagRejectFeedback.hidden = false;

                    break;

                case 'undo': {
                    const initialValue = tagsField.value;
                    let valueRemoved;
                    if (initialValue.endsWith(tag) && /(?:^|\s)$/.test(valueRemoved = initialValue.slice(0, -tag.length))) {
                        tagsField.value = valueRemoved.trimEnd();
                    }

                    undoTagAction(target, tag, actionsFieldset);
                    tagRejectFeedback.hidden = true;
                    break;
                }
            }
        });
    }
}
