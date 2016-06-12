import arrow
import pytest

from libweasyl.constants import Category
from libweasyl.models import content, helpers
from libweasyl.test.common import datadir, make_submission, make_user, user_with_age
from libweasyl import constants, exceptions, ratings


def test_warn_on_rating_assignment_with_no_owner(recwarn):
    """
    A warning is emitted if the rating is set on a submission before the owner
    is set.
    """
    sub = content.Submission()
    sub.rating = ratings.GENERAL
    warning = recwarn.pop(RuntimeWarning)
    assert warning.message.args[0] == 'tried to set the rating on a Submission without an owner'


@pytest.mark.parametrize(('age', 'rating'), [
    (1, ratings.GENERAL),
    (14, ratings.MODERATE),
    (19, ratings.MATURE),
    (19, ratings.EXPLICIT),
])
def test_user_of_age_can_use_rating(age, rating):
    """
    Various age/rating combinations are valid and don't raise an exception.
    """
    user = user_with_age(age)
    sub = content.Submission(owner=user)
    sub.rating = rating
    assert sub.rating == rating


@pytest.mark.parametrize(('age', 'rating'), [
    (1, ratings.MODERATE),
    (1, ratings.MATURE),
    (1, ratings.EXPLICIT),
    (14, ratings.MATURE),
    (14, ratings.EXPLICIT),
])
def test_user_of_age_can_not_use_rating(age, rating):
    """
    Various age/rating combinations are invalid and do raise an exception.
    """
    user = user_with_age(age)
    sub = content.Submission(owner=user)
    with pytest.raises(exceptions.RatingExceeded):
        sub.rating = rating


def convert_artist_tags(tags):
    return [(t.lstrip('*'), helpers.CharSettings({'artist-tag'} if t.startswith('*') else set(), {}, {}))
            for t in tags]


@pytest.mark.parametrize(('tags_before', 'tags_after', 'done_by_artist'), [
    (['spam', 'eggs'], ['spam', 'eggs'], False),
    (['spam', 'eggs'], ['spam', 'eggs', 'sausage'], False),
    (['spam', 'eggs'], ['spam', 'eggs', '*sausage'], True),
    (['spam', 'eggs'], [], False),
    ([], ['spam', 'eggs'], False),
    ([], ['*spam', '*eggs'], True),
    (['spam', 'eggs'], ['spam', 'sausage'], False),
    (['spam', 'eggs'], ['spam', '*sausage'], True),
    (['*spam', '*eggs'], ['*spam', '*eggs', 'sausage'], False),
    (['*spam', '*eggs'], ['*spam', '*eggs', '*sausage'], True),
])
def test_set_tags(db, tags_before, tags_after, done_by_artist):
    """
    ``set_tags`` will add and remove tags as appropriate on a submission.
    """
    sub = make_submission(db)
    tags_before = convert_artist_tags(tags_before)
    tags_after = convert_artist_tags(tags_after)
    db.add_all([content.SubmissionTag(tag=t, settings=s, targetid=sub.submitid) for t, s in tags_before])
    db.flush()
    sub.set_tags([t for t, _ in tags_after], done_by_artist=done_by_artist)
    db.flush()
    all_tags = content.SubmissionTag.query.all()
    assert sorted((t.tag, t.settings.settings) for t in all_tags) == sorted((t, s.settings) for t, s in tags_after)


def test_set_tags_with_extant_tags(db):
    """
    ``set_tags`` will use extant Tag rows.
    """
    sub = make_submission(db)
    db.add_all([content.SubmissionTag(tag=t, targetid=sub.submitid) for t in ['spam', 'eggs']])
    db.add(content.Tag(title='sausage'))
    db.flush()
    sub.set_tags(['spam', 'eggs', 'sausage'])
    db.flush()
    all_tags = content.SubmissionTag.query.all()
    assert sorted(t.tag for t in all_tags) == ['eggs', 'sausage', 'spam']


def test_created_submission_attributes(db, monkeypatch):
    """
    ``Submission.create`` adds a Submission to the database with attributes
    taken from its arguments and datestamped with the current time.
    """
    user = make_user(db)
    data = datadir.join('1x70.gif').read(mode='rb')
    monkeypatch.setattr(content.Submission, 'now', staticmethod(lambda: arrow.get(0)))
    content.Submission.create(
        owner=user, title='Title', rating=ratings.GENERAL, description='Description.',
        category=Category.visual, subtype=1010, folder=None, tags=['spam', 'eggs'],
        submission_data=data)
    db.flush()
    [sub] = content.Submission.query.all()
    assert sub.userid == user.userid
    assert sub.title == 'Title'
    assert sub.rating == ratings.GENERAL
    assert sub.content == 'Description.'
    assert sub.subtype == 1010
    assert sub.folderid is None
    assert sorted(sub.tags) == ['eggs', 'spam']
    assert sub.unixtime == arrow.get(0)
    assert sub.sorttime == arrow.get(0)


def test_created_submission_friends_only_setting(db):
    """
    Creating a friends-only submission sets the friends-only setting.
    """
    user = make_user(db)
    data = datadir.join('1x70.gif').read(mode='rb')
    content.Submission.create(
        owner=user, title='Title', rating=ratings.GENERAL, description='Description.',
        category=Category.visual, subtype=1010, folder=None, tags=['spam', 'eggs'],
        submission_data=data, friends_only=True)
    db.flush()
    [sub] = content.Submission.query.all()
    assert 'friends-only' in sub.settings


def test_created_submission_critique_setting(db):
    """
    Creating a critique-requested submission sets the critique setting.
    """
    user = make_user(db)
    data = datadir.join('1x70.gif').read(mode='rb')
    content.Submission.create(
        owner=user, title='Title', rating=ratings.GENERAL, description='Description.',
        category=Category.visual, subtype=1010, folder=None, tags=['spam', 'eggs'],
        submission_data=data, critique_requested=True)
    db.flush()
    [sub] = content.Submission.query.all()
    assert 'critique' in sub.settings


def test_submission_data_required(db):
    """
    Submission data or an embed link is required.
    """
    user = make_user(db)
    with pytest.raises(exceptions.InvalidData):
        content.Submission.create(
            owner=user, title='Title', rating=ratings.GENERAL, description='Description.',
            category=Category.visual, subtype=1010, folder=None, tags=['spam', 'eggs'])


def test_submission_data_and_embed_link_fails(db):
    """
    Conversely, a submission with both submission data and an embed link is
    invalid.
    """
    user = make_user(db)
    data = datadir.join('fake.swf').read(mode='rb')
    with pytest.raises(exceptions.InvalidData):
        content.Submission.create(
            owner=user, title='Title', rating=ratings.GENERAL, description='Description.',
            category=Category.multimedia, subtype=1010, folder=None, tags=['spam', 'eggs'],
            submission_data=data, embed_link='https://example.com/')


def test_submission_data_gets_limited(db):
    """
    Submission data must be smaller than the size limit.
    """
    user = make_user(db)
    data = datadir.join('1x70.gif').read(mode='rb')
    with pytest.raises(exceptions.SubmissionFileTooLarge):
        content.Submission.create(
            owner=user, title='Title', rating=ratings.GENERAL, description='Description.',
            category=Category.visual, subtype=1010, folder=None, tags=['spam', 'eggs'],
            submission_data=data, submission_size_limit=1)


def test_submission_data_gets_limited_to_default(db, monkeypatch):
    """
    If no submission size limit is provided, the default is used per-file type.
    """
    user = make_user(db)
    data = datadir.join('1x70.gif').read(mode='rb')
    monkeypatch.setitem(constants.DEFAULT_LIMITS, 'gif', 1)
    with pytest.raises(exceptions.SubmissionFileTooLarge):
        content.Submission.create(
            owner=user, title='Title', rating=ratings.GENERAL, description='Description.',
            category=Category.visual, subtype=1010, folder=None, tags=['spam', 'eggs'], submission_data=data)


def test_no_visual_embedded_submissions(db):
    """
    Visual submission can't have an embed link.
    """
    user = make_user(db)
    with pytest.raises(ValueError):
        content.Submission.create(
            owner=user, title='Title', rating=ratings.GENERAL, description='Description.',
            category=Category.visual, subtype=1010, folder=None, tags=['spam', 'eggs'],
            embed_link='https://example.com/')


def test_literary_submission_embed(db):
    """
    Embedded literary submissions create GoogleDocEmbeds as well.
    """
    user = make_user(db)
    content.Submission.create(
        owner=user, title='Title', rating=ratings.GENERAL, description='Description.',
        category=Category.literary, subtype=1010, folder=None, tags=['spam', 'eggs'],
        embed_link='https://example.com/')
    db.flush()
    [sub] = content.Submission.query.all()
    assert sub.settings['embed-type'] == 'google-drive'
    [embed] = content.GoogleDocEmbed.query.all()
    assert embed.embed_url == 'https://example.com/'


def test_multimedia_submission_embed(db):
    """
    Embedded multimedia submissions store the embed url as part of the description.
    """
    user = make_user(db)
    content.Submission.create(
        owner=user, title='Title', rating=ratings.GENERAL, description='Description.',
        category=Category.multimedia, subtype=1010, folder=None, tags=['spam', 'eggs'],
        embed_link='https://example.com/')
    db.flush()
    [sub] = content.Submission.query.all()
    assert sub.settings['embed-type'] == 'other'
    assert sub.content == 'https://example.com/\nDescription.'


def test_invalid_category_embed_link(db):
    """
    Unrecognized categories are treated as errors when a submission is created
    with an embed link.
    """
    user = make_user(db)
    with pytest.raises(ValueError):
        content.Submission.create(
            owner=user, title='Title', rating=ratings.GENERAL, description='Description.', category='spam',
            subtype=1010, folder=None, tags=['spam', 'eggs'], embed_link='https://example.com/')


def test_invalid_category_submission_data(db):
    """
    Unrecognized categories are treated as errors when a submission is created
    with submission data.
    """
    user = make_user(db)
    data = datadir.join('1x70.gif').read(mode='rb')
    with pytest.raises(ValueError):
        content.Submission.create(
            owner=user, title='Title', rating=ratings.GENERAL, description='Description.', category='spam',
            subtype=1010, folder=None, tags=['spam', 'eggs'], submission_data=data)
